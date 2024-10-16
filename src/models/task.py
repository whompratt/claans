from datetime import date
from typing import TYPE_CHECKING, List

from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.models.base import Base
from src.models.task_reward import TaskReward

if TYPE_CHECKING:
    from src.models.record import Record


class Task(Base):
    __tablename__ = "tasks"

    id: Mapped[int] = mapped_column(primary_key=True)
    description: Mapped[str] = mapped_column(nullable=False)
    reward: Mapped[TaskReward] = mapped_column(nullable=False, index=True)
    ephemeral: Mapped[bool] = mapped_column(default=False)
    active: Mapped[bool] = mapped_column(default=False)
    last: Mapped[date] = mapped_column(nullable=True)

    records: Mapped[List["Record"]] = relationship(
        back_populates="task", cascade="all, delete", passive_deletes=True
    )

    def __init__(self, description: str, reward: TaskReward, ephemeral: bool):
        self.description = description
        self.reward = reward
        self.ephemeral = ephemeral

    def __repr__(self):
        return f"Task({vars(self)})"

    def __str__(self):
        return f"Task:\ndescription: {self.description}\ndice: {self.reward}\nactive: {self.active}\nephemeral: {self.ephemeral}\nlast: {self.last}"
