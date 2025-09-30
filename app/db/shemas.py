from pydantic import BaseModel, Field, GetCoreSchemaHandler
from pydantic_core import core_schema
from datetime import datetime, timezone
from bson import ObjectId


class PyObjectId(ObjectId):
    @classmethod
    def __get_pydantic_core_schema__(cls, _source_type, _handler: GetCoreSchemaHandler):
        # Tell Pydantic how to validate
        return core_schema.no_info_after_validator_function(
            cls.validate,
            core_schema.str_schema()
        )

    @classmethod
    def validate(cls, v):
        if not ObjectId.is_valid(v):
            raise ValueError("Invalid ObjectId")
        return ObjectId(v)

    @classmethod
    def __get_pydantic_json_schema__(cls, _core_schema, handler):
        return handler(core_schema.str_schema())

class User(BaseModel):
    id: str = Field(default_factory=lambda: str(PyObjectId()), alias="_id")
    username: str
    email: str
    hashed_password: str
    role: str
    created_at: datetime = datetime.now(timezone.utc)
    updated_at: datetime = datetime.now(timezone.utc)

class UserProfile(BaseModel):
    first_name: str
    last_name: str
    thread_ids: list[str] = []
    courses: list[str] = []
    created_at: datetime = datetime.now(timezone.utc)
    updated_at: datetime = datetime.now(timezone.utc)
    user_id: PyObjectId

class RefreshToken(BaseModel):
    user_id: str = Field(default_factory=lambda: str(ObjectId()), alias="_id")
    token: str
    created_at: datetime = datetime.now(timezone.utc)
    expires_at: datetime