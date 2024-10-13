from datetime import date

from sqlalchemy import ForeignKey, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.models.base import Base
from src.models.claan import Claan
from src.models.dice import Dice
from src.models.task import Task
from src.models.user import User


class Record(Base):
    """
    Defines a record for a quest or activity, for submission of the record into the mongo database.

    Note that this class is used for both `submit_task` and `update_score`.
    `score` and `timestamp` are generated in `__post_init__`.
    `score` requires `dice` be already defined, which itself is an instance of `Dice`, using its `roll` function.
    `timestamp` is generated using the `datetime` library, which works natively with pymongo.

    Attributes:
        user: name of the user submitting the quest or activity.
        claan: instance of enum `Claans`, defining which claan this user is in.
        dice: instance of enum `Dice`, which defines the number of sides of the score die to roll.
    """

    __tablename__ = "records"

    id: Mapped[int] = mapped_column(primary_key=True)
    score: Mapped[int] = mapped_column(nullable=False)
    timestamp: Mapped[date] = mapped_column(nullable=False)
    claan: Mapped[Claan] = mapped_column(nullable=False)

    task_id: Mapped[int] = mapped_column(
        ForeignKey("tasks.id", ondelete="CASCADE"), nullable=False
    )
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )

    task: Mapped["Task"] = relationship("Task", back_populates="records")
    user: Mapped["User"] = relationship("User", back_populates="records")

    # Column for stock game only - nullable True so that this can be ignored for any existing records
    escrow: Mapped[bool] = mapped_column(
        nullable=True,
        default=True,
    )

    __table_args__ = (
        Index(
            "record_user_task_idx",
            user_id,
            task_id,
        ),
        Index(
            "record_timestamp_idx",
            timestamp.desc(),
        ),
    )

    # TODO: Don't take dice in, read from task instead
    # Basically if task is Task, then dice can be Dice or None
    # If task is int, dice must be Dice
    def __init__(self, task: Task | int, user: User | int, claan: Claan, dice: Dice):
        self.score = dice.roll()
        self.timestamp = date.today()
        self.claan = claan

        self.task_id = task if isinstance(task, int) else task.id
        self.user_id = user if isinstance(user, int) else user.id

    def __str__(self):
        return f"Record for user {self.user_id} against task {self.task_id}, in claan {self.claan} with score {self.score}"
