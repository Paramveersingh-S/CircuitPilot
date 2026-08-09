from pydantic import BaseModel

class ChatEvent(BaseModel):
    type: str = "chat"
    role: str
    text: str

class FileChangedEvent(BaseModel):
    type: str = "file_changed"
    path: str
    ts: str
