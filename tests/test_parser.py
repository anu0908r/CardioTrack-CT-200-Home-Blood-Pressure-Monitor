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
