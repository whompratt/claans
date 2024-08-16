from datetime import date, timedelta
from math import floor
from pathlib import Path
from typing import List, Optional, Type

import streamlit as st
import toml
from faker import Faker
from sqlalchemy import create_engine, func, select
from sqlalchemy.engine import URL
from sqlalchemy.engine.base import Engine
from sqlalchemy.orm import Session, sessionmaker

from src.models.base import Base
from src.models.dice import Dice
from src.models.record import Record
from src.models.season import Season
from src.models.task import Task, TaskType
from src.models.user import User
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

    @classmethod
    @st.cache_data(ttl=3600)
    def get_rows(
        cls,
        _session: Session,
        model: Type[Base],
        filter: Optional[dict] = None,
    ) -> List[Type[Base]]:
        """Return a :class:`List[sqlalchemy.engine.Row]` models that match the input query.

        :example: Filter can be formatted as follows:

        .. code-block:: python
            filter: dict = {
                "name": "John Doe"
            }

        .. code-block:: python
            filter: dict = {
                "claan": Claans.EARTH_STRIDERS
            }


        :param model: The model to return, must inherit :class:`models.Base`.

        :param filter: An optional :class:`dict` defining the filter, where keys are :class:`str` column names and values are the value the key should match.

            .. note:: If no filter is provided, all rows are returned.

        :return: List of :class:`sqlalchemy.engine.Row` models that matched the query filter.
        """
        query = select(model)
        for k, v in filter.items():
            query = query.where(getattr(model, k) == v)

        result = _session.execute(query).scalars().all()
        return result

    # @classmethod
    # @st.cache_data(ttl=3600)
    # def get_claan_scores(cls, _session: Session) -> Dict[Claan, int]:
    #     """Returns a formatted dict of Claans and their scores for the current Season."""
    #     session = cls.get_session() if _session is None else _session
    #     query = select(func.max(Season.start_date))
    #     season = session.scalar(query)

    #     query = (
    #         select(Record.claan, func.sum(Record.score).label("score"))
    #         .where(Record.timestamp >= season)
    #         .group_by("claan")
    #     )
    #     result = session.execute(query).all()

    #     scores: dict = {claan: 0 for claan in Claan}
    #     for row in result:
    #         scores[row.claan] = row.score

    #     return scores

    @classmethod
    @st.cache_data(ttl=3600)
    def get_active_quests(cls, _session: Session) -> List[Task]:
        session = cls.get_session() if _session is None else _session
        query = (
            select(Task)
            .where(Task.active)
            .where(Task.task_type == TaskType.QUEST)
            .order_by(Task.dice.asc())
        )
        result = session.scalars(query).all()
        session.expunge_all()
        return result

    @classmethod
    @st.cache_data(ttl=3600)
    def get_active_activities(cls, _session: Session) -> List[Task]:
        session = cls.get_session() if _session is None else _session
        query = (
            select(Task)
            .where(Task.active)
            .where(Task.task_type == TaskType.ACTIVITY)
            .order_by(Task.dice.asc())
        )
        result = session.scalars(query).all()
        session.expunge_all()
        return result

    @classmethod
    @st.cache_data(ttl=3600)
    def get_fortnight(
        cls,
        _session: Session,
        timestamp: Optional[date] = None,
    ) -> int:
        """Returns the integer representation of the current fortnight for the active season.

        :param date: An optional instance of :class:`datetime.date`, otherwise today will be used.
        :param engine: An optional instance of :class:`sqlalchemy.engine.base.Engine`.
            .. note:: If no engine is provided, :meth:get_database_engine will be called with default parameters.
        :return: :class:`int` representation of current fortnight for this season, indexed to zero.
        """
        session = cls.get_session() if _session is None else _session
        if timestamp is None:
            timestamp = date.today()

        season_start: date = session.execute(
            select(func.max(Season.start_date))
        ).scalar_one()

        weeks = floor((timestamp - season_start).days / 7)
        weeks = floor(weeks / 2)

    @classmethod
    def submit_record(cls, _session: Session, task: Task, user: User) -> bool:
        if task.dice == Dice.D12:
            # Check fortnight
            fortnight = Database.get_fortnight(
                timestamp=date.today(), _session=_session
            )
            query = select(func.max(Season.start_date))
            season_start: date = _session.execute(query).scalar_one()
            fortnight_start = season_start + timedelta(weeks=(fortnight * 2))
            query = select(Record).where(
                Record.user_id == user.id,
                Record.task_id == task.id,
                Record.timestamp >= fortnight_start,
            )
            result = _session.execute(query).scalar_one_or_none()
            pass
        else:
            # Check day
            query = select(Record).where(
                Record.user_id == user.id,
                Record.task_id == task.id,
                Record.timestamp >= date.today(),
            )
            result = _session.execute(query).scalar_one_or_none()

        if result is not None:
            LOGGER.warning(
                f"Daily/Fortnight check failed, result is not None: {result}"
            )
            return False

        record = Record(task=task, user=user, claan=user.claan, dice=task.dice)
        _session.add(record)
        return True


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
