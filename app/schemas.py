from datetime import datetime

from pydantic import (
    BaseModel,
    ConfigDict,
    EmailStr,
    Field,
    field_validator,
    model_validator,
)


def normalize_name(value: str) -> str:
    value = value.strip()

    if len(value) < 2:
        raise ValueError("El nombre debe tener al menos 2 caracteres")

    return value


class UserCreate(BaseModel):
    name: str = Field(
        min_length=2,
        max_length=50,
    )
    email: EmailStr

    @field_validator("name")
    @classmethod
    def validate_name(cls, value: str) -> str:
        return normalize_name(value)


class UserUpdate(BaseModel):
    name: str | None = Field(
        default=None,
        min_length=2,
        max_length=50,
    )
    email: EmailStr | None = None
    is_active: bool | None = None

    @field_validator("name")
    @classmethod
    def validate_name(
        cls,
        value: str | None,
    ) -> str | None:
        if value is None:
            return None

        return normalize_name(value)

    @model_validator(mode="after")
    def validate_update(self):
        if not self.model_fields_set:
            raise ValueError("Debes enviar al menos un campo para actualizar")

        for field_name in self.model_fields_set:
            if getattr(self, field_name) is None:
                raise ValueError(f"{field_name} no puede ser null")

        return self


class UserResponse(BaseModel):
    id: int
    name: str
    email: EmailStr
    created_at: datetime
    is_active: bool

    model_config = ConfigDict(
        from_attributes=True,
    )


class TaskCreate(BaseModel):
    title: str = Field(
        min_length=1,
        max_length=120,
    )
    description: str | None = Field(
        default=None,
        max_length=1000,
    )

    @field_validator("title")
    @classmethod
    def validate_title(cls, value: str) -> str:
        value = value.strip()

        if not value:
            raise ValueError("El título no puede estar vacío")

        return value


class TaskUpdate(BaseModel):
    title: str | None = Field(
        default=None,
        min_length=1,
        max_length=120,
    )

    description: str | None = Field(
        default=None,
        max_length=1000,
    )

    is_completed: bool | None = None

    @field_validator("title")
    @classmethod
    def validate_title(
        cls,
        value: str | None,
    ) -> str | None:
        if value is None:
            return None

        value = value.strip()

        if not value:
            raise ValueError("El título no puede estar vacío")

        return value

    @model_validator(mode="after")
    def validate_update(self):
        if not self.model_fields_set:
            raise ValueError("Debes enviar al menos un campo para actualizar")

        if "title" in self.model_fields_set and self.title is None:
            raise ValueError("title no puede ser null")

        if "is_completed" in self.model_fields_set and self.is_completed is None:
            raise ValueError("is_completed no puede ser null")

        return self


class TaskResponse(BaseModel):
    id: int
    title: str
    description: str | None
    is_completed: bool
    created_at: datetime
    user_id: int

    model_config = ConfigDict(
        from_attributes=True,
    )
