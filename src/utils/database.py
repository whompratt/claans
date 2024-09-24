import random
from datetime import date
from itertools import cycle
from pathlib import Path
from typing import Optional

import streamlit as st
import toml
from faker import Faker
from sqlalchemy import create_engine, delete, func, select
from sqlalchemy.engine import URL
from sqlalchemy.engine.base import Engine
from sqlalchemy.exc import MultipleResultsFound, NoResultFound
from sqlalchemy.orm import Session, sessionmaker

from src.models.base import Base
from src.models.dice import Dice
from src.models.murder import Murder
from src.models.task import TaskType
from src.utils.murder import generate_targets


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

    _tables = [Claan, Record, Season, Task, User, Murder]
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
                query_cnt = (
                    select(func.count()).select_from(User).where(User.claan == claan)
                )
                count = session.scalar(query_cnt)

                if count < 1:
                    this_user = User(name=fake.name(), claan=claan)
                    session.add(this_user)

        # If no quests, populate with test quests for each die
        with session.begin_nested():
            query_cnt = (
                select(Task.dice, func.count())
                .select_from(Task)
                .where(Task.task_type == TaskType.QUEST)
                .group_by(Task.dice)
            )
            result = session.execute(query_cnt).all()
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
            query_cnt = (
                select(Task.dice, func.count())
                .select_from(Task)
                .where(Task.task_type == TaskType.ACTIVITY)
                .group_by(Task.dice)
            )
            result = session.execute(query_cnt).all()
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

        # For game of Murder, if 'murder' table is empty, populate
        tasks = [
            "Get a picture of you giving your target bunny ears",
            "Get your target to tell you what Claan they're in",
            "Get your target to say 'AAFest'",
            "Get your target to shake your hand",
            "Get your target to hold something for you",
            "Get your target to high-five you",
            "Get a picture of you and your target wearing matching accessories (like hats or sunglasses)",
            "Get your target to lend you a pen or another small item",
            "Get a selfie with your target making a silly face",
            "Get your target to tell you the time",
            "Get your target to compliment you on something (like your shirt or hair)",
            "Get your target to draw something for you on paper",
            "Get your target to agree with an opinion you state (even if it's something trivial)",
            "Get your target to hold the door open for you",
            "Get your target to teach you how to do something (e.g., tie a knot, do a dance move)",
            "Get your target to answer a random trivia question you ask",
            "Get your target to tell you about their day or weekend plans",
            "Get your target to laugh at a joke you tell",
            "Get your target to write something down for you",
        ]
        random.shuffle(tasks)
        tasks = cycle(tasks)
        with session.begin_nested():
            # Add a task for the Murder game, for submitting records
            query_task = select(Task).where(Task.description == "MURDER")
            result = session.execute(query_task).one_or_none()
            if result is None:
                murder_task = Task(
                    "MURDER",
                    TaskType.QUEST,
                    Dice.D4,
                    False,
                )
                session.add(murder_task)

        with session.begin_nested():
            # Delete all rows in Murder table and rebuild
            query_del = delete(Murder)
            session.execute(query_del)

            murder_targets = generate_targets(session=session)
            assignments = []
            for agent, info in murder_targets.items():
                assignments.append(
                    Murder(
                        agent=agent,
                        target=info["target"],
                        task=next(tasks),
                    )
                )

            session.add_all(assignments)

        with session.begin_nested():
            # Check Murder table, ensure every one is a agent and a target
            query = select(Murder)
            rows = session.execute(query).scalars()

            for row in rows:
                # print(agent)
                query = select(Murder).where(Murder.agent_id == row.target_id)
                try:
                    result = session.execute(query).one()
                except NoResultFound:
                    print(
                        f"Unable to find instance where {row.target.name}({row.target_id}) is the agent."
                    )

                query = select(Murder).where(Murder.target_id == row.agent_id)
                try:
                    result = session.execute(query).one()
                except NoResultFound:
                    print(
                        f"Unable to find instance where {row.agent.name}({row.agent_id}) is the target."
                    )
                except MultipleResultsFound:
                    print(
                        f"Found multiple instances where {row.agent.name}({row.agent_id}) is the target."
                    )

    pass


if __name__ == "__main__":
    initialise()
