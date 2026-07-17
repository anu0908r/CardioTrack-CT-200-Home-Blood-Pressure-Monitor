from pydantic import BaseModel, ConfigDict
from typing import List, Optional, Any
from datetime import datetime

class NodeBase(BaseModel):
    heading: str
    level: int
    body_text: str

class NodeOut(NodeBase):
    id: int
    logical_id: str
    content_hash: str
    parent_id: Optional[int] = None
    
    model_config = ConfigDict(from_attributes=True)

class NodeDetailOut(NodeOut):
    children: List['NodeDetailOut'] = []

class DocumentVersionOut(BaseModel):
    id: int
    version_number: int
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)

class DocumentOut(BaseModel):
    id: int
    name: str
    versions: List[DocumentVersionOut] = []
    
    model_config = ConfigDict(from_attributes=True)

class SelectionCreate(BaseModel):
    name: str
    node_ids: List[int]

class SelectionOut(BaseModel):
    id: int
    name: str
    created_at: datetime
    nodes: List[NodeOut] = []
    
    model_config = ConfigDict(from_attributes=True)

class DiffSummary(BaseModel):
    logical_id: str
    is_changed: bool
    old_hash: str
    new_hash: str
    diff_text: Optional[str] = None
