from __future__ import annotations

from datetime import datetime

from sqlalchemy import (
    BigInteger,
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Identity,
    String,
    UniqueConstraint,
    false,
    func,
    true,
)
from sqlalchemy.orm import (
    Mapped,
    mapped_column,
    relationship,
)

from app.database import Base


class User(Base):
    __tablename__ = "users"

    __table_args__ = (
        CheckConstraint(
            "char_length(trim(name)) >= 2",
            name="users_name_length_check",
        ),
    )

    id: Mapped[int] = mapped_column(
        BigInteger,
        Identity(always=True),
        primary_key=True,
    )

    name: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )

    email: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        unique=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        server_default=true(),
    )

    tasks: Mapped[list[Task]] = relationship(
        back_populates="user",
        passive_deletes=True,
    )

    api_keys: Mapped[list[ApiKey]] = relationship(
        back_populates="user",
        cascade="all, delete",
        passive_deletes=True,
    )


class Task(Base):
    __tablename__ = "tasks"

    id: Mapped[int] = mapped_column(
        BigInteger,
        Identity(always=True),
        primary_key=True,
    )

    title: Mapped[str] = mapped_column(
        String(120),
        nullable=False,
    )

    description: Mapped[str | None] = mapped_column(
        String(1000),
        nullable=True,
    )

    is_completed: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        server_default=false(),
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    user_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey(
            "users.id",
            ondelete="RESTRICT",
        ),
        nullable=False,
        index=True,
    )

    user: Mapped[User] = relationship(
        back_populates="tasks",
    )


class ApiKey(Base):
    __tablename__ = "api_keys"
    __table_args__ = (
        CheckConstraint(
            "char_length(trim(name)) >= 1",
            name="api_keys_name_not_blank_check",
        ),
        CheckConstraint(
            "char_length(key_id) = 24",
            name="api_keys_key_id_length_check",
        ),
        CheckConstraint(
            "char_length(key_digest) = 64",
            name="api_keys_key_digest_length_check",
        ),
        UniqueConstraint(
            "key_id",
            name="api_keys_key_id_key",
        ),
    )

    id: Mapped[int] = mapped_column(
        BigInteger,
        Identity(always=True),
        primary_key=True,
    )

    name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    key_id: Mapped[str] = mapped_column(
        String(24),
        nullable=False,
    )

    key_digest: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    expires_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    revoked_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    last_used_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    user_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey(
            "users.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    user: Mapped[User] = relationship(
        back_populates="api_keys",
    )
