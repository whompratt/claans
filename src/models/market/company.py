from typing import TYPE_CHECKING, List

from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.models.base import Base
from src.models.claan import Claan

if TYPE_CHECKING:
    from src.models.market.instrument import Instrument
    from src.models.market.portfolio import Portfolio
    from src.models.market.transaction import Transaction


class Company(Base):
    __tablename__ = "companies"

    id: Mapped[int] = mapped_column(primary_key=True)
    claan: Mapped["Claan"] = mapped_column(nullable=False)
    cash: Mapped[float] = mapped_column(nullable=False, default=0.0)

    instrument: Mapped["Instrument"] = relationship(
        back_populates="company",
        cascade="all, delete-orphan",
        passive_deletes=True,
        passive_updates=True,
    )

    board: Mapped[List["Portfolio"]] = relationship(
        back_populates="company",
        cascade="all, delete-orphan",
        passive_deletes=True,
        passive_updates=True,
    )
    transactions: Mapped[List["Transaction"]] = relationship(
        back_populates="company",
        cascade="all, delete-orphan",
        passive_deletes=True,
        passive_updates=True,
    )

    def __init__(self, claan: Claan):
        self.claan = claan
