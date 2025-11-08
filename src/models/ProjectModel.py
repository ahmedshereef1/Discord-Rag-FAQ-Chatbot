from .BaseDataModel import BaseDataModel
from .db_schemas import Project
from .enums.DataBaseEnum import DataBaseEnum

class ProjectModel(BaseDataModel):
    
    def __init__(self, db_client: object):
        super().__init__(db_client=db_client)

        self.collection = self.db_clinet[DataBaseEnum.COLLECTION_PROJECTS.value]

    # CRUD Operations
    # Create
    async def create_project(self, project: Project):
        result = await self.collection.insert_one(project.dict(by_alias=True, exclude_unset=True))

        project._id = result.inserted_id
        return project
    
    # Read
    async def get_project_or_create_one(self, project_id: str):
        record = await self.collection.find_one({"project_id": project_id})
        if record is None:
            # Create a new project
            project = Project(project_id=project_id)
            project = await self.create_project(project)
            return project

        return Project(**record)
    
    # Read - Get All with Pagination
    async def get_all_projects(self, page: int = 1, page_size: int = 10):
        # Count total number od documents
        total_documents= await self.collection.count_documents({})
        total_pages = total_documents // page_size
        if total_documents % page_size > 0:
            total_pages += 1
        
        curser = self.collection.find().skip((page - 1) * page_size).limit(page_size)
        projects= []
        async for document in curser:
            projects.append(Project(**document))
        
        return projects, total_pages
    
