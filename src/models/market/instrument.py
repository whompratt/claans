from typing import TYPE_CHECKING, List, Optional, Type

from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, Session, mapped_column, relationship

from src.models.base import Base
from src.models.claan import Claan
from src.models.market.company import Company

if TYPE_CHECKING:
    from src.models.market.share import Share
    from src.models.market.transaction import Transaction


class Instrument(Base):
    __tablename__ = "instruments"

    id: Mapped[int] = mapped_column(primary_key=True)
    price: Mapped[float] = mapped_column(nullable=False, default=10.0)
    enabled: Mapped[bool] = mapped_column(nullable=False, default=False)

    company_id: Mapped[int] = mapped_column(
        ForeignKey("companies.id", ondelete="CASCADE"), nullable=False
    )
    company: Mapped["Company"] = relationship(
        back_populates="instrument",
        cascade="all",
        passive_deletes=True,
        passive_updates=True,
        single_parent=True,
    )

    transactions: Mapped[List["Transaction"]] = relationship(
        back_populates="instrument",
        cascade="all, delete-orphan",
        passive_deletes=True,
        passive_updates=True,
    )
    shares: Mapped[List["Share"]] = relationship(
        back_populates="instrument",
        cascade="all, delete-orphan",
        passive_deletes=True,
        passive_updates=True,
    )

    def __init__(self, company: Company | int, price: Optional[float] = None):
        if isinstance(company, Company):
            self.company_id = company.id
        elif isinstance(company, int):
            self.company_id = company
        else:
            raise TypeError(
                "Instrument.copmany_id can only be initialized with a company object or an integer id"
            )
        self.price = price or 10.0

    @classmethod
    def create(
        cls, _session: Session, claan: Claan, price: Optional[float] = None
    ) -> Type["Instrument"]:
        new_instrument = Instrument(claan=claan, price=price or 10.0)
        _session.add(new_instrument)
        _session.commit()
