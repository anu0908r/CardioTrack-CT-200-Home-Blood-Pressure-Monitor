import fitz
import hashlib
from typing import List, Dict, Any, Optional

def compute_hash(text: str) -> str:
    return hashlib.sha256(text.encode('utf-8', errors='ignore')).hexdigest()

class ParsedNode:
    def __init__(self, heading: str, level: int, logical_id: str):
        self.heading = heading
        self.level = level
        self.logical_id = logical_id
        self.body_text = ""
        self.children: List['ParsedNode'] = []
    
    def add_text(self, text: str):
        if self.body_text:
            self.body_text += "\n" + text
        else:
            self.body_text = text

    @property
    def content_hash(self) -> str:
        return compute_hash(f"{self.heading}:{self.level}:{self.body_text}")

def parse_pdf(file_path: str) -> List[ParsedNode]:
    doc = fitz.open(file_path)
    
    root_nodes = []
    current_path = []  # Stack of ParsedNodes
    
    # Virtual root for text before any heading
    current_node = ParsedNode(heading="root", level=0, logical_id="root")
    root_nodes.append(current_node)
    
    def get_level_from_size(size: float) -> int:
        if size >= 16.0:
            return 1
        elif size > 12.0:
            return 2
        else:
            return 0 # Body text
            
    for page in doc:
        blocks = page.get_text("dict")["blocks"]
        for b in blocks:
            if "lines" not in b:
                continue
            for l in b["lines"]:
                text = "".join([s["text"] for s in l["spans"]]).strip()
                if not text:
                    continue
                size = round(l["spans"][0]["size"], 1)
                
                # Check if it's a heading
                level = get_level_from_size(size)
                
                if level > 0:
                    # It's a heading!
                    # If Title (size >= 22.0), treat it as level 1
                    while current_path and current_path[-1].level >= level:
                        # Special case: if it's the exact same level and we just added it, 
                        # and there's NO body text yet, merge them!
                        if current_path[-1].level == level and not current_path[-1].body_text and current_path[-1].heading != text:
                            current_path[-1].heading += " " + text
                            # Recompute logical ID? It's fine to leave it as the first line.
                            break
                        current_path.pop()
                    else:
                        # Only create new node if we didn't merge
                        parent_logical_id = current_path[-1].logical_id if current_path else "root"
                        safe_heading = text.lower().replace(" ", "-")
                        
                        logical_id = f"{parent_logical_id}/{safe_heading}"
                        
                        siblings = current_path[-1].children if current_path else root_nodes
                        duplicate_count = sum(1 for sib in siblings if sib.logical_id.startswith(logical_id))
                        if duplicate_count > 0:
                            logical_id = f"{logical_id}-{duplicate_count}"
                        
                        new_node = ParsedNode(heading=text, level=level, logical_id=logical_id)
                        
                        if current_path:
                            current_path[-1].children.append(new_node)
                        else:
                            root_nodes.append(new_node)
                            
                        current_path.append(new_node)
                        current_node = new_node
                else:
                    # Body text
                    current_node.add_text(text)
                    
    # Clean up empty root if needed
    if len(root_nodes) > 1 and not root_nodes[0].body_text and not root_nodes[0].children:
        root_nodes.pop(0)
        
    return root_nodes

def print_tree(nodes, indent=0):
    for node in nodes:
        print("  " * indent + f"- {node.heading} (L{node.level}) [Hash: {node.content_hash[:8]}]")
        print("  " * (indent + 1) + f"Logical ID: {node.logical_id}")
        if node.body_text:
            text_preview = node.body_text.replace('\n', ' ')[:50]
            print("  " * (indent + 1) + f"Text: {text_preview}...")
        print_tree(node.children, indent + 1)

if __name__ == "__main__":
    nodes = parse_pdf('ct200_manual.pdf')
    print_tree(nodes)
