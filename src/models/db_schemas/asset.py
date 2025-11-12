from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from bson import ObjectId  # pyright: ignore[reportMissingImports]
from datetime import datetime

class Asset(BaseModel):
    id: Optional[ObjectId] = Field(None, alias="_id")
    asset_project_id: ObjectId
    asset_type: str = Field(..., min_length=1)
    asset_name: str = Field(..., min_length=1)
    asset_size: Optional[int] = Field(default=None, ge=0)
    asset_config: Optional[Dict[str, Any]] = Field(default=None)
    asset_pushed_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        arbitrary_types_allowed = True

    @classmethod
    def get_indexes(cls):
        return [
            {
                "key" : [
                    ("asset_project_id" , 1)
                ],
                "name" : "asset_project_id_index_1",
                "unique" : False
            },
            {
                "key" : [
                    ("asset_project_id" , 1),
                    ("asset_name",1)
                ],
                "name" : "asset_project_id_name_index_1",
                "unique" : True
            }
        ]


