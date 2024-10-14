from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING, Optional

from sqlalchemy import CheckConstraint, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.models.base import Base
from src.models.market.company import Company
from src.models.market.instrument import Instrument
from src.models.market.portfolio import Portfolio

if TYPE_CHECKING:
    pass


class TransactionType(Enum):
    QUEST = 1


class Operation(Enum):
    BUY = 1
    SELL = 2
    CREDIT = 3
    DEBIT = 4


class Transaction(Base):
    """Transaction ORM model.

    A transaction records the movement of funds from one entity to another
    """

    __tablename__ = "transactions"
    __table_args__ = (
        CheckConstraint(
            "(company_id IS NOT NULL AND portfolio_id IS NULL) or (company_id IS NULL AND portfolio_id IS NOT NULL)"
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    value: Mapped[float] = mapped_column(nullable=False)
    operation: Mapped[Operation] = mapped_column(nullable=False)
    timestamp: Mapped[datetime] = mapped_column(nullable=False, default=datetime.now())

    instrument_id: Mapped[int] = mapped_column(
        ForeignKey("instruments.id", ondelete="CASCADE"), nullable=True
    )
    instrument: Mapped["Instrument"] = relationship(
        cascade="all", passive_deletes=True, passive_updates=True
    )

    portfolio_id: Mapped[int] = mapped_column(
        ForeignKey("portfolios.id", ondelete="CASCADE"), nullable=True
    )
    portfolio: Mapped["Portfolio"] = relationship(
        back_populates="transactions",
        cascade="all",
        passive_deletes=True,
        passive_updates=True,
    )

    company_id: Mapped[int] = mapped_column(
        ForeignKey("companies.id", ondelete="CASCADE"), nullable=True
    )
    company: Mapped["Company"] = relationship(
        back_populates="transactions",
        cascade="all",
        passive_deletes=True,
        passive_updates=True,
    )

    def __init__(
        self,
        value: float,
        operation: Operation,
        instrument: Instrument | int,
        portfolio: Optional[Portfolio | int],
        company: Optional[Company | int],
        timestamp: Optional[datetime],
    ):
        self.value = value
        self.operation = operation
        self.timestamp = timestamp or datetime.now()

        if company and portfolio:
            raise KeyError("Transaction must have company or portfolio BUT NOT BOTH")
        if not company and not portfolio:
            raise KeyError("Transaction must have company OR portfolio")

        if isinstance(instrument, Instrument):
            self.instrument_id = instrument.id
        elif isinstance(instrument, int):
            self.instrument_id = instrument
        else:
            raise TypeError(
                "Transaction.instrument_id can only be initialized with a instrument object or an integer id"
            )

        if portfolio:
            if isinstance(portfolio, Portfolio):
                self.portfolio_id = portfolio.id
            elif isinstance(portfolio, int):
                self.portfolio_id = portfolio
            else:
                raise TypeError(
                    "Transaction.portfolio_id can only be initialized with a portfolio object or an integer id"
                )

        if company:
            if isinstance(company, Portfolio):
                self.company_id = company.id
            elif isinstance(company, int):
                self.company_id = company
            else:
                raise TypeError(
                    "Transaction.company_id can only be initialized with a company object or an integer id"
                )
