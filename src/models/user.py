from typing import TYPE_CHECKING, List, Optional

from email_validator import validate_email
from sqlalchemy.orm import Mapped, mapped_column, relationship, validates

from src.models.base import Base
from src.models.claan import Claan

if TYPE_CHECKING:
    from src.models.record import Record


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

    def __repr__(self):
        return f"User({vars(self)})"

    def __str__(self):
        return f"User '{self.name}' in Claan '{self.claan.value}'"

    @validates("email")
    def validate_email(self, key, value):
        email = validate_email(value)
        if "advancinganalytics" in email.domain:
            return email.normalized
