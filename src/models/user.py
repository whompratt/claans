from functools import total_ordering
from typing import TYPE_CHECKING, List, Optional, Type

from email_validator import validate_email
from sqlalchemy.orm import Mapped, mapped_column, relationship, validates

from src.models.base import Base
from src.models.claan import Claan

if TYPE_CHECKING:
    from src.models.record import Record


@total_ordering
class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    long_name: Mapped[str] = mapped_column(nullable=False)
    name: Mapped[str] = mapped_column(nullable=False)
    email: Mapped[str] = mapped_column(nullable=False, unique=True)
    claan: Mapped[Claan] = mapped_column(nullable=True, index=True)
    active: Mapped[bool] = mapped_column(nullable=False, default=True)

    records: Mapped[List["Record"]] = relationship(
        back_populates="user", cascade="all, delete", passive_deletes=True
    )

    def __init__(
        self,
        long_name: str,
        name: str,
        email: str,
        claan: Claan,
        active: Optional[bool] = True,
    ):
        self.long_name = long_name
        self.name = name
        self.email = email
        self.claan = claan
        self.active = active

    def __dir__(self):
        return ["long_name", "name", "email"]

    def _is_valid_operand(self, other):
        return all([hasattr(other, attr) for attr in dir(self)])

    def __repr__(self):
        return f"User({vars(self)})"

    def __str__(self):
        return f"{self.name}"

    def __eq__(self, other: Type["User"]):
        if not self._is_valid_operand(other):
            return NotImplemented
        return all(
            [
                (hasattr(other, attr)) and (getattr(self, attr) == getattr(other, attr))
                for attr in dir(self)
            ]
        )

    def __lt__(self, other: Type["User"]):
        if not self._is_valid_operand(other):
            return NotImplemented
        return self.name < other.name

    @validates("email")
    def validate_email(self, key, value):
        email = validate_email(value)
        if "advancinganalytics" in email.domain:
            return email.normalized
        else:
            raise ValueError("Email failed validation")
