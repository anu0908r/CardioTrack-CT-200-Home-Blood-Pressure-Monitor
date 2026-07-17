from fastapi import FastAPI, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
import os
from typing import List
import uvicorn

from . import models, schemas, services
from .database import engine, get_db

models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="CT-200 Backend API")

@app.post("/documents/ingest")
async def ingest_document(doc_name: str = Form(...), file: UploadFile = File(...), db: Session = Depends(get_db)):
    # Save uploaded file to temp path
    file_path = f"temp_{file.filename}"
    with open(file_path, "wb") as buffer:
        buffer.write(await file.read())
        
    try:
        doc_version = services.ingest_document(db, file_path, doc_name)
        return {"message": "Document ingested successfully", "version_id": doc_version.id, "version_number": doc_version.version_number}
    finally:
        if os.path.exists(file_path):
            os.remove(file_path)

@app.get("/documents/{doc_id}/versions", response_model=List[schemas.DocumentVersionOut])
def list_versions(doc_id: int, db: Session = Depends(get_db)):
    doc = db.query(models.Document).filter(models.Document.id == doc_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    return doc.versions

@app.get("/nodes", response_model=List[schemas.NodeDetailOut])
def list_nodes(doc_id: int, version_number: int = None, db: Session = Depends(get_db)):
    doc = db.query(models.Document).filter(models.Document.id == doc_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
        
    if version_number:
        version = db.query(models.DocumentVersion).filter(
            models.DocumentVersion.document_id == doc_id,
            models.DocumentVersion.version_number == version_number
        ).first()
    else:
        version = services.get_latest_version(db, doc_id)
        
    if not version:
        raise HTTPException(status_code=404, detail="Version not found")
        
    # Get top level nodes
    nodes = db.query(models.Node).filter(
        models.Node.version_id == version.id,
        models.Node.parent_id == None
    ).all()
    
    return nodes

@app.get("/nodes/{node_id}", response_model=schemas.NodeDetailOut)
def get_node(node_id: int, db: Session = Depends(get_db)):
    node = db.query(models.Node).filter(models.Node.id == node_id).first()
    if not node:
        raise HTTPException(status_code=404, detail="Node not found")
    return node

@app.get("/nodes/{node_id}/diff", response_model=schemas.DiffSummary)
def get_node_diff(node_id: int, db: Session = Depends(get_db)):
    diff = services.get_node_diff(db, node_id)
    if not diff:
        raise HTTPException(status_code=404, detail="Node not found")
    return diff

@app.post("/selections", response_model=schemas.SelectionOut)
def create_selection(selection: schemas.SelectionCreate, db: Session = Depends(get_db)):
    return services.create_selection(db, selection)

@app.post("/selections/{selection_id}/generate")
def generate_test_cases(selection_id: int, db: Session = Depends(get_db)):
    return services.generate_test_cases(db, selection_id)

@app.get("/selections/{selection_id}/generations")
def get_generations(selection_id: int, db: Session = Depends(get_db)):
    return services.get_generations_with_staleness(db, selection_id)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
