from datetime import date

from sqlalchemy.orm import Mapped, mapped_column

from src.models.base import Base


class Season(Base):
    __tablename__ = "season"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(nullable=False)
    start_date: Mapped[date] = mapped_column(nullable=False)

    def __init__(self, name: str, start_date: date):
        self.name = name
        self.start_date = start_date
