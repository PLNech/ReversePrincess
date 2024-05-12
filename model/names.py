import enum


class ModelName(str, enum.Enum):
    tiny = "tinyllama:1.1b-chat-v1-q2_K"
    llama3 = "llama3:latest"
    llama3_8 = "llama3:8b"
    dolphin = "dolphin-mistral:latest"
