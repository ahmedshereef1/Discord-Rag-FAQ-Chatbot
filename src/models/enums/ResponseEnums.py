from enum import Enum

class ResponseSingnals(Enum):

    FILE_TYPE_NOT_SUPPORTED = "File type not Supported."
    FILE_SIZE_EXCEEDED = "File size exceeds the maximum limit."
    FILE_VALIDATION_SUCCESS = "Successfully validated the uploaded file."
    FILE_VALIDATION_FAILED = "File validation failed."
    FILE_UPLOAD_SUCCESS = "File uploaded successfully."
    FILE_UPLOAD_FAILED = "File upload failed."
    PROCESSING_SUCCESS = "File processed successfully."
    PROCESSING_FAIELD = "File processing failed."
    NO_FILES_ERROR = "Not Found Files"
    FILE_ID_ERROR = "No file found with this ID"
    PROJECT_NOT_FOUND_ERROR = "Project not found"
    INSERT_INTO_VECTORDB_ERROR = "Insert into vector DB Error"
    INSERT_INTO_VECTORDB_SUCCESS = "Insert into vector DB Success"
    VECTORDB_COLLECTION_RETRIEVED = "vectordb_collection_retrieved"
    VECTORDB_SEARCH_ERROR = "Vector DB Search Error"
    VECTOTDB_SEARCH_SUCCESS = "Vector DB Search Success"
    RAG_ANSWER_ERROR = "Rag answer error"
    RAG_ANSWER_SUCCESS = "Rag answer success"
    DATA_PUSH_TASK_READY = "Data push task is ready"
    PROCESS_AND_PUSH_WORKFLOW_STARTED = "Process and push workflow started"