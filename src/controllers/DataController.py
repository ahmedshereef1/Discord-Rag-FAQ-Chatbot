from controllers.BaseController import BaseController
from fastapi import UploadFile
from models import ResponseSingnals
from .ProjectController import ProjectController
import re 
import os 

class DataController(BaseController):
    def __init__(self):
        super().__init__()
        self.size_scale = 1024 * 1024  # Scale for MB
    
    def validate_uploaded_file(self, file: UploadFile):
       
       if file.content_type not in self.app_settings.FILE_ALLOWED_TYPES:
           return False, ResponseSingnals.FILE_TYPE_NOT_SUPPORTED.value
    
       if file.size > self.app_settings.FILE_MAX_SIZE_MB * self.size_scale:
           return False, ResponseSingnals.FILE_SIZE_EXCEEDED.value

       return True, ResponseSingnals.FILE_VALIDATION_SUCCESS.value
    
    def generate_unique_filepath(self, original_filename: str, project_id: str):
        
        random_key = self.generate_random_string()
        project_path = ProjectController().get_project_path(project_id=project_id)

        clean_file_name = self.get_clean_file_name(original_filename=original_filename)

        new_file_path = os.path.join(
            project_path,
            f"{random_key}_{clean_file_name}"
        )

        while os.path.exists(new_file_path):
            random_key = self.generate_random_string()
            new_file_path = os.path.join(
                project_path,
                f"{random_key}_{clean_file_name}"
            )

        return new_file_path, random_key + "_" + clean_file_name
    
    def get_clean_file_name(self, original_filename: str):

        clean_file_name =  re.sub(r'[^a-zA-Z0-9._]', '', original_filename.strip())

        clean_file_name = clean_file_name.replace(' ', '_')

        return clean_file_name
