from enum import Enum
from typing import TYPE_CHECKING, List

from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.models.base import Base
from src.models.market.company import Company
from src.models.user import User

if TYPE_CHECKING:
    from src.models.market.share import Share
    from src.models.market.transaction import Transaction


class BoardVote(Enum):
    ABSTAIN = 1
    WITHOLD = 2
    PAYOUT = 3

    def __str__(self):
        if self == BoardVote.WITHOLD:
            return "WITHHOLD"
        else:
            return self.name


class Portfolio(Base):
    __tablename__ = "portfolios"

    id: Mapped[int] = mapped_column(primary_key=True)
    cash: Mapped[float] = mapped_column(nullable=False, default=0.0)
    board_vote: Mapped[BoardVote] = mapped_column(
        nullable=False, default=BoardVote.ABSTAIN
    )

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    user: Mapped["User"] = relationship(back_populates=None)

    company_id: Mapped[int] = mapped_column(
        ForeignKey("companies.id", ondelete="CASCADE"), nullable=False
    )
    company: Mapped["Company"] = relationship(
        back_populates="board",
        cascade="all",
        passive_deletes=True,
        passive_updates=True,
    )

    transactions: Mapped[List["Transaction"]] = relationship(
        back_populates="portfolio",
        cascade="all, delete-orphan",
        passive_deletes=True,
        passive_updates=True,
    )
    shares: Mapped[List["Share"]] = relationship(
        back_populates="owner",
        cascade="all, delete-orphan",
        passive_deletes=True,
        passive_updates=True,
    )

    def __init__(self, user: User | int, company: Company | int):
        if isinstance(user, User):
            self.user_id = user.id
        elif isinstance(user, int):
            self.user_id = user
        else:
            raise TypeError(
                "Portfolio can only be instanced with a User object or an int"
            )

        if isinstance(company, Company):
            self.company_id = company.id
        elif isinstance(company, int):
            self.company_id = company
        else:
            raise TypeError(
                "Portfolio can only be instanced with a Company object or an int"
            )
