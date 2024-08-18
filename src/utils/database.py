from datetime import date
from pathlib import Path
from typing import Optional

import streamlit as st
import toml
from faker import Faker
from sqlalchemy import create_engine, func, select
from sqlalchemy.engine import URL
from sqlalchemy.engine.base import Engine
from sqlalchemy.orm import Session, sessionmaker

from src.models.base import Base
from src.models.dice import Dice
from src.models.task import TaskType


class Database:
    @classmethod
    @st.cache_resource
    def get_engine(
        cls, secrets_path: Optional[Path] = Path("./.streamlit/secrets.toml")
    ) -> Engine:
        if not secrets_path.exists():
            raise FileNotFoundError(
                "Secrets file not found. If no file path was provided, default path not found."
            )

        secrets = toml.load(secrets_path)
        connection_info: dict = secrets.get("connections").get("postgresql")
        connection_info["drivername"] = connection_info.pop("dialect")
        url = URL.create(**connection_info)

        engine = create_engine(url, echo=False)

        return engine

    @classmethod
    @st.cache_resource
    def get_session(cls, engine: Optional[Engine] = None) -> Session:
        """Return a :class:`sqlalchemy.orm.session.Session` object.

        :param engine: An optional instance of :class:`sqlalchemy.engine.base.Engine`.
            .. note:: If no engine is provided, :meth:get_database_engine will be called with default parameters.
        :return: new :class:`sqlalchemy.orm.session.sessionmaker` object.
            .. note:: This is a :class:sessionmaker, not a :class:session. Use `with sessionmaker() as session:` to implement, to guarantee sessions close properly.
        """
        if engine is None:
            engine = cls.get_engine()

        # TODO: Where the hell should this go?!
        Base.metadata.create_all(bind=engine)
        maker = sessionmaker(bind=engine, expire_on_commit=False)

        return maker()


def initialise() -> None:
    from src.models import Claan, Record, Season, Task, User

    _tables = [Claan, Record, Season, Task, User]
    Base.metadata.create_all(bind=Database.get_engine())

    with Database.get_session() as session, session.begin():
        ## Default season
        with session.begin_nested():
            query_season_count = select(func.count()).select_from(Season)
            season_count = session.scalar(query_season_count)
            if season_count == 0:
                season = Season(name="Default", start_date=date(2024, 7, 29))
                session.add(season)

        # If no users, populate each Claan with 3 test users
        with session.begin_nested():
            fake = Faker()
            for claan in Claan:
                query = (
                    select(func.count()).select_from(User).where(User.claan == claan)
                )
                count = session.scalar(query)

                if count < 1:
                    this_user = User(name=fake.name(), claan=claan)
                    session.add(this_user)

        # If no quests, populate with test quests for each die
        with session.begin_nested():
            query = (
                select(Task.dice, func.count())
                .select_from(Task)
                .where(Task.task_type == TaskType.QUEST)
                .group_by(Task.dice)
            )
            result = session.execute(query).all()
            quest_counts = {row.dice: row.count for row in result}
            for die in Dice:
                if quest_counts.get(die) is None:
                    quest = Task(
                        description=f"Sample Quest {die.name}",
                        task_type=TaskType.QUEST,
                        dice=die,
                        ephemeral=False,
                    )
                    session.add(quest)

        # If no activities, popeulate with test activities for each die bar D12
        with session.begin_nested():
            query = (
                select(Task.dice, func.count())
                .select_from(Task)
                .where(Task.task_type == TaskType.ACTIVITY)
                .group_by(Task.dice)
            )
            result = session.execute(query).all()
            activity_counts = {row.dice: row.count for row in result}
            for die in [Dice.D4, Dice.D6, Dice.D8, Dice.D10]:
                if activity_counts.get(die) is None:
                    activity = Task(
                        description=f"Sample Activity {die.name}",
                        task_type=TaskType.ACTIVITY,
                        dice=die,
                        ephemeral=False,
                    )
                    session.add(activity)

    pass


if __name__ == "__main__":
    initialise()
