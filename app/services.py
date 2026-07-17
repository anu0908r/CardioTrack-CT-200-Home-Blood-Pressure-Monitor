import os
from sqlalchemy.orm import Session
from fastapi import UploadFile
from typing import List, Optional
import json
from . import models, schemas, parser
from tinydb import TinyDB, Query
import uuid

# Initialize TinyDB for LLM generations
DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'generations.json')
tinydb = TinyDB(DB_PATH)

def get_latest_version(db: Session, document_id: int) -> Optional[models.DocumentVersion]:
    return db.query(models.DocumentVersion).filter(
        models.DocumentVersion.document_id == document_id
    ).order_by(models.DocumentVersion.version_number.desc()).first()

def ingest_document(db: Session, file_path: str, doc_name: str) -> models.DocumentVersion:
    # Check if doc exists
    doc = db.query(models.Document).filter(models.Document.name == doc_name).first()
    if not doc:
        doc = models.Document(name=doc_name)
        db.add(doc)
        db.commit()
        db.refresh(doc)
        version_number = 1
    else:
        latest_version = get_latest_version(db, doc.id)
        version_number = (latest_version.version_number + 1) if latest_version else 1
        
    doc_version = models.DocumentVersion(document_id=doc.id, version_number=version_number)
    db.add(doc_version)
    db.commit()
    db.refresh(doc_version)
    
    # Parse PDF
    parsed_nodes = parser.parse_pdf(file_path)
    
    def save_node(parsed_node, parent_id=None):
        db_node = models.Node(
            version_id=doc_version.id,
            parent_id=parent_id,
            logical_id=parsed_node.logical_id,
            heading=parsed_node.heading,
            level=parsed_node.level,
            body_text=parsed_node.body_text,
            content_hash=parsed_node.content_hash
        )
        db.add(db_node)
        db.commit()
        db.refresh(db_node)
        
        for child in parsed_node.children:
            save_node(child, db_node.id)
            
    for node in parsed_nodes:
        save_node(node)
        
    return doc_version

def get_node_diff(db: Session, node_id: int) -> schemas.DiffSummary:
    node = db.query(models.Node).filter(models.Node.id == node_id).first()
    if not node:
        return None
        
    # Find latest node with same logical_id in the same document
    doc_id = node.version.document_id
    latest_version = get_latest_version(db, doc_id)
    
    latest_node = db.query(models.Node).filter(
        models.Node.version_id == latest_version.id,
        models.Node.logical_id == node.logical_id
    ).first()
    
    if not latest_node:
        # Node was deleted
        return schemas.DiffSummary(
            logical_id=node.logical_id,
            is_changed=True,
            old_hash=node.content_hash,
            new_hash="",
            diff_text="Node was deleted in the latest version."
        )
        
    is_changed = (node.content_hash != latest_node.content_hash)
    diff_text = None
    if is_changed:
        import difflib
        diff = difflib.unified_diff(
            node.body_text.splitlines(),
            latest_node.body_text.splitlines(),
            fromfile=f'v{node.version.version_number}',
            tofile=f'v{latest_version.version_number}'
        )
        diff_text = '\n'.join(diff)
        
    return schemas.DiffSummary(
        logical_id=node.logical_id,
        is_changed=is_changed,
        old_hash=node.content_hash,
        new_hash=latest_node.content_hash,
        diff_text=diff_text
    )

def create_selection(db: Session, selection_data: schemas.SelectionCreate) -> models.Selection:
    selection = models.Selection(name=selection_data.name)
    db.add(selection)
    
    nodes = db.query(models.Node).filter(models.Node.id.in_(selection_data.node_ids)).all()
    selection.nodes.extend(nodes)
    
    db.commit()
    db.refresh(selection)
    return selection

def generate_test_cases(db: Session, selection_id: int) -> dict:
    selection = db.query(models.Selection).filter(models.Selection.id == selection_id).first()
    if not selection:
        return {"error": "Selection not found"}
        
    # Reconstruct text
    context_text = "\n\n".join([f"{n.heading}\n{n.body_text}" for n in selection.nodes])
    
    # MOCK LLM CALL
    # In a real app, this would use google-genai or similar.
    # The prompt would be: "Given the following medical device manual text, generate 3-5 QA test cases."
    # We will simulate a structured response here.
    
    mocked_response = [
        {"test_case": f"Verify {selection.nodes[0].heading} displays correctly", "steps": ["Turn on device", "Check display"], "expected": "Information is visible"},
        {"test_case": "Simulate error condition based on text", "steps": ["Trigger failure"], "expected": "Device shows error code"}
    ]
    
    generation_id = str(uuid.uuid4())
    generation_record = {
        "id": generation_id,
        "selection_id": selection_id,
        "pinned_nodes": [{"id": n.id, "logical_id": n.logical_id, "content_hash": n.content_hash} for n in selection.nodes],
        "test_cases": mocked_response
    }
    
    tinydb.insert(generation_record)
    return generation_record

def get_generations_with_staleness(db: Session, selection_id: int):
    GenQuery = Query()
    generations = tinydb.search(GenQuery.selection_id == selection_id)
    
    results = []
    for gen in generations:
        stale = False
        stale_details = []
        
        # Check staleness against latest document versions
        for pinned in gen["pinned_nodes"]:
            diff = get_node_diff(db, pinned["id"])
            if diff and diff.is_changed:
                stale = True
                stale_details.append(diff.dict())
                
        gen_out = dict(gen)
        gen_out["is_stale"] = stale
        gen_out["stale_details"] = stale_details
        results.append(gen_out)
        
    return results
