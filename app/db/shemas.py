from pydantic import BaseModel, ConfigDict, Field, GetCoreSchemaHandler, GetJsonSchemaHandler
from pydantic_core import core_schema
from datetime import datetime, timezone
from bson import ObjectId
from typing import Any, Optional


class PyObjectId(ObjectId):
    @classmethod
    def __get_pydantic_core_schema__(cls, source_type, handler: GetCoreSchemaHandler):
        return core_schema.no_info_after_validator_function(
            cls.validate,
            core_schema.str_schema(),
            serialization=core_schema.to_string_ser_schema(),
        )

    @classmethod
    def validate(cls, v: Any, _info=None):
        if isinstance(v, ObjectId):
            return v
        if not ObjectId.is_valid(v):
            raise ValueError(f"Invalid ObjectId: {v}")
        return ObjectId(v)

    @classmethod
    def __get_pydantic_json_schema__(cls, schema, handler):
        json_schema = handler(schema)
        json_schema.update(type="string")
        return json_schema


class User(BaseModel):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    username: str
    email: str
    hashed_password: str
    role: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class UserProfile(BaseModel):
    id: PyObjectId = Field(default_factory=None, alias="_id")
    first_name: str
    last_name: str
    thread_ids: list[str] = []
    courses: list[str] = []  # delete later
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    user_id: PyObjectId


class RefreshToken(BaseModel):
    id: PyObjectId = Field(default_factory=None, alias="_id")
    user_id: PyObjectId
    token: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    expires_at: datetime


class Course(BaseModel):
    model_config = ConfigDict(
        populate_by_name=True,  # Allow populating model fields by their alias
        arbitrary_types_allowed=True  # Allow custom types like PyObjectId
    )
    id: Optional[PyObjectId] = Field(default=None, alias="_id")
    thread_id: str
    title: str
    target: str
    outline: list | None = []
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    user_id: PyObjectId


class Question(BaseModel):
    question: str
    answer: int
    choices: list[str]


class Chapter(BaseModel):
    id: PyObjectId = Field(default_factory=None, alias="_id")
    title: str
    target: str
    order: int
    number_of_subtopics: int
    course_id: PyObjectId
    quiz: list[Question] = []
    quiz_result: list[int] = []
    quiz_answers: list[int] = []
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class Subtopic(BaseModel):
    id: PyObjectId = Field(default_factory=None, alias="_id")
    title: str
    content: str
    target: str
    order: int
    summary: str
    questions: list[Question] = []
    chapter_id: PyObjectId
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
