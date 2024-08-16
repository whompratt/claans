from datetime import date, datetime
from enum import Enum
from typing import TYPE_CHECKING, List

from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.models.base import Base
from src.models.dice import Dice

if TYPE_CHECKING:
    from src.models.record import Record


class TaskType(Enum):
    """Enum denoting the type of record"""

    QUEST = "quest"
    ACTIVITY = "activity"


class Task(Base):
    __tablename__ = "task"

    id: Mapped[int] = mapped_column(primary_key=True)
    description: Mapped[str] = mapped_column(nullable=False)
    task_type: Mapped[TaskType] = mapped_column(nullable=False)
    dice: Mapped[Dice] = mapped_column(nullable=False)
    ephemeral: Mapped[bool] = mapped_column(default=False)
    active: Mapped[bool] = mapped_column(default=False)
    last: Mapped[date] = mapped_column(default=datetime.min)

    records: Mapped[List["Record"]] = relationship(
        back_populates="task", cascade="all, delete", passive_deletes=True
    )

    def __init__(
        self, description: str, task_type: TaskType, dice: Dice, ephemeral: bool
    ):
        self.description = description
        self.task_type = task_type
        self.dice = dice
        self.ephemeral = ephemeral