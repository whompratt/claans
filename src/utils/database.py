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
from src.models.task_reward import TaskReward
from src.utils.logger import LOGGER


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
        with session.begin_nested():
            LOGGER.info("Checking for default season...")
            query_season_count = select(func.count()).select_from(Season)
            season_count = session.scalar(query_season_count)
            if season_count == 0:
                LOGGER.info("No default season, adding")
                season = Season(name="Default", start_date=date(2024, 7, 29))
                session.add(season)

        # If no users, populate each Claan with 3 test users
        with session.begin_nested():
            LOGGER.info("Populating empty Claans with fake users...")
            fake = Faker()
            for claan in Claan:
                query_cnt = (
                    select(func.count()).select_from(User).where(User.claan == claan)
                )
                count = session.scalar(query_cnt)

                if count < 1:
                    LOGGER.info(f"Adding fake user for Claan {claan.name}")
                    this_user = User(name=fake.name(), claan=claan)
                    session.add(this_user)

        ## Assign a claan to users with no claan
        with session.begin_nested():
            LOGGER.info("Checking for users with no Claan...")
            query = select(User).where(User.claan.is_(None))
            users_with_no_claan = session.execute(query).scalars().all()
            for user in users_with_no_claan:
                LOGGER.warning(
                    f"No Claan assigned to user {user.name} with id {user.id}"
                )

        # If no quests, populate with test quests for each die
        with session.begin_nested():
            LOGGER.info("Populating tasks...")
            query_cnt = (
                select(Task.reward, func.count())
                .select_from(Task)
                .group_by(Task.reward)
            )
            result = session.execute(query_cnt).all()
            quest_counts = {row.reward: row.count for row in result}
            for reward in TaskReward:
                if quest_counts.get(reward) is None:
                    LOGGER.info(f"Adding sample quest for reward ${reward.value}")
                    quest = Task(
                        description=f"Sample Quest {reward.name}",
                        reward=reward,
                        ephemeral=False,
                    )
                    session.add(quest)

        pass


if __name__ == "__main__":
    initialise()
