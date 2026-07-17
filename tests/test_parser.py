import pytest
from app.parser import ParsedNode

def test_parsed_node_hash():
    node1 = ParsedNode("Test Heading", 1, "root/test")
    node1.add_text("Body text here.")
    
    node2 = ParsedNode("Test Heading", 1, "root/test")
    node2.add_text("Body text here.")
    
    node3 = ParsedNode("Test Heading", 1, "root/test")
    node3.add_text("Different body text.")
    
    assert node1.content_hash == node2.content_hash
    assert node1.content_hash != node3.content_hash

def test_logical_id_hierarchy():
    root = ParsedNode("root", 0, "root")
    child = ParsedNode("Child", 1, f"{root.logical_id}/child")
    root.children.append(child)
    
    assert child.logical_id == "root/child"

def test_duplicate_headings_get_unique_ids():
    # Simulate the logic that duplicate headings get indexed logically
    root = ParsedNode("root", 0, "root")
    child1 = ParsedNode("Warning", 1, "root/warning")
    root.children.append(child1)
    
    # 2nd warning should get a distinct logical ID
    siblings = root.children
    logical_id = "root/warning"
    duplicate_count = sum(1 for sib in siblings if sib.logical_id.startswith(logical_id))
    if duplicate_count > 0:
        logical_id = f"{logical_id}-{duplicate_count}"
        
    child2 = ParsedNode("Warning", 1, logical_id)
    root.children.append(child2)
    
    assert child1.logical_id == "root/warning"
    assert child2.logical_id == "root/warning-1"
    assert child1.logical_id != child2.logical_id

