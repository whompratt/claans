import random
from itertools import cycle
from pathlib import Path
from typing import Optional

import streamlit as st
import toml
from sqlalchemy import create_engine, delete, select
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
        # ## Default season
        # with session.begin_nested():
        #     query_season_count = select(func.count()).select_from(Season)
        #     season_count = session.scalar(query_season_count)
        #     if season_count == 0:
        #         season = Season(name="Default", start_date=date(2024, 7, 29))
        #         session.add(season)

        # # If no users, populate each Claan with 3 test users
        # with session.begin_nested():
        #     fake = Faker()
        #     for claan in Claan:
        #         query_cnt = (
        #             select(func.count()).select_from(User).where(User.claan == claan)
        #         )
        #         count = session.scalar(query_cnt)

        #         if count < 1:
        #             this_user = User(name=fake.name(), claan=claan)
        #             session.add(this_user)

        # # If no quests, populate with test quests for each die
        # with session.begin_nested():
        #     query_cnt = (
        #         select(Task.dice, func.count())
        #         .select_from(Task)
        #         .where(Task.task_type == TaskType.QUEST)
        #         .group_by(Task.dice)
        #     )
        #     result = session.execute(query_cnt).all()
        #     quest_counts = {row.dice: row.count for row in result}
        #     for die in Dice:
        #         if quest_counts.get(die) is None:
        #             quest = Task(
        #                 description=f"Sample Quest {die.name}",
        #                 task_type=TaskType.QUEST,
        #                 dice=die,
        #                 ephemeral=False,
        #             )
        #             session.add(quest)

        # # If no activities, popeulate with test activities for each die bar D12
        # with session.begin_nested():
        #     query_cnt = (
        #         select(Task.dice, func.count())
        #         .select_from(Task)
        #         .where(Task.task_type == TaskType.ACTIVITY)
        #         .group_by(Task.dice)
        #     )
        #     result = session.execute(query_cnt).all()
        #     activity_counts = {row.dice: row.count for row in result}
        #     for die in [Dice.D4, Dice.D6, Dice.D8, Dice.D10]:
        #         if activity_counts.get(die) is None:
        #             activity = Task(
        #                 description=f"Sample Activity {die.name}",
        #                 task_type=TaskType.ACTIVITY,
        #                 dice=die,
        #                 ephemeral=False,
        #             )
        #             session.add(activity)

        # For game of Murder, if 'murder' table is empty, populate
        tasks = [
            "Get a picture of you giving your target bunny ears",
            "Get your target to tell you what Claan they're in, convince them you are in the same claan",
            "Get your target to chant 'AAFest is the AABest' with you",
            "Get your target to hold something for you then take a photo of them without them knowing",
            "Get your target to high-five you whilst shouting 'AA'",
            "Get a picture of you and your target wearing matching accessories (like hats or sunglasses)",
            "Get your target to lend you a pen or another small item which you must then lose dramatically",
            "Get a selfie with your target making a silly face whilst you look at them disapprovingly",
            "Get your target to tell you the time in Bali - the 'Bristol of Asia'",
            "Get your target to compliment you on something (like your shirt or hair). Be offended by whatever they say",
            "Get your target to draw something for you on paper",
            "Get your target to agree with an opinion you state (even if it's something trivial). Immediately change your stance and tell them they are wrong",
            "Get your target to hold the door open for you. Don't go through. Meow",
            "Get your target to teach you how to do something (e.g., tie a knot, do a dance move)",
            "Get your target to research facts about Bristol Naval History for you. Disagree with their findings.",
            "Get your target to laugh at a joke you tell. Immediately explain why the joke is funny",
            "Get your target to write something down for you",
            "Appear in a photo your target is in without them knowing",
            "Get your target to join you in an overly loud 'GO TEAM' celebration",
            "Get your target to spell their name or something else backwards, try to convince them they did it wrong",
            "Get your target to talk like they are from Bristol. 'Alright my lovaaaerrr'",
            "Convince your target to do a mindfulness exercise and take a selfie while their eyes are closed",
            "Challenge your target to a nerf shootout that you must deliberately lose without them knowing",
            "Convince your target to support your great new business idea which uses AI, get them to pitch the idea to Gavi or Terry with you",
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
            print("Generating assignments")
            for agent, info in murder_targets.items():
                assignment = Murder(
                    agent=agent,
                    target=info["target"],
                    task=next(tasks),
                )
                print(
                    f"{assignment.agent_id} -> {assignment.target_id}: {assignment.task}"
                )
                assignments.append(assignment)

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
