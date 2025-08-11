from pydantic import BaseModel


# Response Model for Getting File Content
class FileMetadata(BaseModel):
    path: str
    filename: str
    size: int
    mime_type: str
    language: str
