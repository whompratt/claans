from typing import TYPE_CHECKING, List

from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.models.base import Base
from src.models.claan import Claan

if TYPE_CHECKING:
    from src.models.record import Record


class User(Base):
    __tablename__ = "user"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(nullable=False)
    claan: Mapped[Claan] = mapped_column(nullable=False, index=True)

    records: Mapped[List["Record"]] = relationship(
        back_populates="user", cascade="all, delete", passive_deletes=True
    )

    def __init__(self, name: str, claan: Claan):
        self.name = name
        self.claan = claan
