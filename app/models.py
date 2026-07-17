from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Table
from sqlalchemy.orm import relationship
import datetime
from .database import Base

class Document(Base):
    __tablename__ = "documents"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    
    versions = relationship("DocumentVersion", back_populates="document")

class DocumentVersion(Base):
    __tablename__ = "document_versions"
    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, ForeignKey("documents.id"))
    version_number = Column(Integer)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    
    document = relationship("Document", back_populates="versions")
    nodes = relationship("Node", back_populates="version")

class Node(Base):
    __tablename__ = "nodes"
    id = Column(Integer, primary_key=True, index=True)
    version_id = Column(Integer, ForeignKey("document_versions.id"))
    parent_id = Column(Integer, ForeignKey("nodes.id"), nullable=True)
    logical_id = Column(String, index=True)  # Used to match nodes across versions (e.g. root/heading1/heading2)
    heading = Column(String)
    level = Column(Integer)
    body_text = Column(String)
    content_hash = Column(String)
    
    version = relationship("DocumentVersion", back_populates="nodes")
    children = relationship("Node", back_populates="parent", remote_side=[parent_id])
    parent = relationship("Node", back_populates="children", remote_side=[id])

selection_node = Table(
    "selection_node",
    Base.metadata,
    Column("selection_id", Integer, ForeignKey("selections.id")),
    Column("node_id", Integer, ForeignKey("nodes.id"))
)

class Selection(Base):
    __tablename__ = "selections"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    
    nodes = relationship("Node", secondary=selection_node)
