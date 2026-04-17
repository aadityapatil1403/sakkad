from pydantic import BaseModel, Field


class Layer1TagsResponse(BaseModel):
    tags: list[str] = Field(min_length=10, max_length=10)


class Layer2TagsResponse(BaseModel):
    tags: list[str] = Field(min_length=10, max_length=10)
