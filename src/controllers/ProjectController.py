from .BaseController import BaseController
from fastapi import UploadFile
from models import ResponseSingnals
import os 

class ProjectController(BaseController):
    def __init__(self):
        super().__init__()

    def get_project_path(self, project_id: str):
        project_id = os.path.join(
            self.file_dir,
            project_id
        )

        if not os.path.exists(project_id):
            os.makedirs(project_id)
            
        return project_id