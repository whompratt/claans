from typing import Optional, Type

from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, Session, mapped_column, relationship

from src.models.base import Base
from src.models.market.instrument import Instrument
from src.models.market.portfolio import Portfolio


class Share(Base):
    __tablename__ = "shares"

    id: Mapped[int] = mapped_column(primary_key=True)

    instrument_id: Mapped[int] = mapped_column(
        ForeignKey("instruments.id", ondelete="CASCADE"), nullable=False
    )
    instrument: Mapped["Instrument"] = relationship(
        back_populates="shares",
        cascade="all",
        passive_deletes=True,
        passive_updates=True,
    )

    owner_id: Mapped[int] = mapped_column(
        ForeignKey("portfolios.id", ondelete="CASCADE"),
        nullable=True,
    )
    owner: Mapped["Portfolio"] = relationship(
        back_populates="shares",
        cascade="all",
        passive_deletes=True,
        passive_updates=True,
    )

    def __init__(self, instrument: Instrument | int, owner: Optional[Portfolio | int]):
        if isinstance(instrument, Instrument):
            self.instrument_id = instrument.id
        elif isinstance(instrument, int):
            self.instrument_id = instrument
        else:
            raise TypeError(
                "Share.instrument_id can only be initialized with a instrument object or an integer id"
            )

        if owner:
            if isinstance(owner, Instrument):
                self.owner_id = owner.id
            elif isinstance(owner, int):
                self.owner_id = owner
            else:
                raise TypeError(
                    "Share.instrument_id can only be initialized with a instrument object or an integer id"
                )

    @classmethod
    def create(
        cls,
        _session: Session,
        instrument: Instrument | int,
        owner: Optional[Portfolio | int],
    ) -> Type["Share"]:
        new_share = Share(instrument=instrument, owner=owner)
        _session.add(new_share)
        _session.commit()
