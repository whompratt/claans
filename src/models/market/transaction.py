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
        instrument: Optional[Instrument | int],
        portfolio: Optional[Portfolio | int],
        company: Optional[Company | int],
        timestamp: Optional[datetime],
    ):
        """Initialize a new Transaction object.

        :param value: The float value of the transaction ($)
        :param operation: The type of transaction performed, of type :class:`OperationType`, an enum

        :param instrument: `optional` If relevant, which instrument this transaction was against
        :param timestamp: `optional` An optional timestamp to set, defaulting to :meth:`datetime.now()` if None

        :param company: Required if :param:`portfolio` is None, the company which is receiving or losing funds
        :param portfolio: Required if :param:`company` is None, the portfoio which is receiving or losing funds
        """
        self.value = value
        self.operation = operation
        self.timestamp = timestamp or datetime.now()

        if company and portfolio:
            raise ValueError("Transaction must have company or portfolio BUT NOT BOTH")
        if not company and not portfolio:
            raise ValueError("Transaction must have company OR portfolio")

        if operation in [Operation.BUY, Operation.SELL] and not instrument:
            raise ValueError(
                "If operation is BUY or SELL instrument must be present in init"
            )
        if instrument:
            if isinstance(instrument, Instrument):
                self.instrument_id = instrument.id
            elif isinstance(instrument, int):
                self.instrument_id = instrument
            else:
                raise ValueError(
                    "Transaction.instrument_id can only be initialized with a instrument object or an integer id"
                )

        if portfolio:
            if isinstance(portfolio, Portfolio):
                self.portfolio_id = portfolio.id
            elif isinstance(portfolio, int):
                self.portfolio_id = portfolio
            else:
                raise ValueError(
                    "Transaction.portfolio_id can only be initialized with a portfolio object or an integer id"
                )

        if company:
            if isinstance(company, Company):
                self.company_id = company.id
            elif isinstance(company, int):
                self.company_id = company
            else:
                raise ValueError(
                    "Transaction.company_id can only be initialized with a company object or an integer id"
                )
