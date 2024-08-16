from datetime import date
from typing import Dict

from sqlalchemy import ForeignKey, func, select
from sqlalchemy.orm import Mapped, Session, mapped_column, relationship

from src.models.base import Base
from src.models.claan import Claan
from src.models.dice import Dice
from src.models.season import Season
from src.models.task import Task
from src.models.user import User
from src.utils.timer import timer


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
        type: instance of enum `RecordType`, defining whether this is a quest or activity.
        dice: instance of enum `Dice`, which defines the number of sides of the score die to roll.
    """

    __tablename__ = "record"

    id: Mapped[int] = mapped_column(primary_key=True)
    score: Mapped[int] = mapped_column(nullable=False)
    timestamp: Mapped[date] = mapped_column(nullable=False)
    claan: Mapped[Claan] = mapped_column(nullable=False)

    task_id: Mapped[int] = mapped_column(
        ForeignKey("task.id", ondelete="CASCADE"), nullable=False
    )
    user_id: Mapped[int] = mapped_column(
        ForeignKey("user.id", ondelete="CASCADE"), nullable=False
    )

    task: Mapped["Task"] = relationship("Task", back_populates="records")
    user: Mapped["User"] = relationship("User", back_populates="records")

    # TODO: Don't take dice in, read from task instead
    # Basically if task is Task, then dice can be Dice or None
    # If task is int, dice must be Dice
    def __init__(self, task: Task | int, user: User | int, claan: Claan, dice: Dice):
        self.score = dice.roll()
        self.timestamp = date.today()
        self.claan = claan

        self.task_id = task if isinstance(task, int) else task.id
        self.user_id = user if isinstance(user, int) else user.id

    @classmethod
    @timer
    def get_claan_scores(cls, _session: Session) -> Dict[Claan, int]:
        """Returns a formatted dict of Claans and their scores for the current Season."""
        query = select(func.max(Season.start_date))
        season = _session.scalar(query)

        query = (
            select(cls.claan, func.sum(cls.score).label("score"))
            .where(cls.timestamp >= season)
            .group_by("claan")
        )
        result = _session.execute(query).all()

        scores: dict = {claan: 0 for claan in Claan}
        for row in result:
            scores[row.claan] = row.score

        return scores
