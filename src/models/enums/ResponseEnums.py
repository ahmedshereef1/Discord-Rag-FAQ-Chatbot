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