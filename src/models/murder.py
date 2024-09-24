from typing import Optional

from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.models.base import Base
from src.models.user import User


class Murder(Base):
    __tablename__ = "murder"

    id: Mapped[int] = mapped_column(primary_key=True)
    task: Mapped[str] = mapped_column(nullable=True)

    agent_id: Mapped[int] = mapped_column(ForeignKey("user.id"), nullable=False)
    target_id: Mapped[int] = mapped_column(ForeignKey("user.id"), nullable=False)

    agent: Mapped["User"] = relationship("User", primaryjoin="Murder.agent_id==User.id")
    target: Mapped["User"] = relationship(
        "User", primaryjoin="Murder.target_id==User.id"
    )

    def __init__(
        self, agent: int | User, target: int | User, task: Optional[str] = None
    ) -> None:
        self.agent_id = agent if isinstance(agent, int) else agent.id
        self.target_id = target if isinstance(target, int) else target.id
        self.task = task
