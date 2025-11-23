from .minirag_base import SQLAIchemyBase
from sqlalchemy import Column, DateTime, ForeignKey, Index
from sqlalchemy import Integer, String, func
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
import uuid


class Asset(SQLAIchemyBase):

    __tablename__ = "assets"

    asset_id = Column(Integer, primary_key=True, autoincrement=True)
    asset_uuid = Column(UUID(as_uuid=True), default=uuid.uuid4, unique=True, nullable=False)
    
    asset_type = Column(String, nullable=False)
    asset_name = Column(String, nullable=False)
    asset_size = Column(Integer, nullable=False)
    asset_config = Column(JSONB, nullable=True)

    asset_project_id = Column(Integer, ForeignKey("projects.project_id"), nullable=False)

    project = relationship("Project", back_populates="assets")
    chunks = relationship("DataChunk", back_populates="asset", cascade="all, delete-orphan")  

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), nullable=True)

    __table_args__  = (
        Index("idx_asset_project_id",asset_project_id),
        Index("idx_asset_type", asset_type)
    )
