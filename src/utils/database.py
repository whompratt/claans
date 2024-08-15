from datetime import date, timedelta
from functools import wraps
from math import floor
from pathlib import Path
from typing import Dict, List, Optional, Type

import toml
from faker import Faker
from sqlalchemy import create_engine, delete, func, select
from sqlalchemy.engine import URL
from sqlalchemy.engine.base import Engine
from sqlalchemy.orm import Session, sessionmaker

from src.models.base import Base
from src.models.claan import Claan
from src.models.dice import Dice
from src.models.record import Record
from src.models.season import Season
from src.models.task import Task, TaskType
from src.models.user import User
from src.utils.logger import LOGGER


class Database:
    class _Decorators:
        @classmethod
        def with_session(cls, func):
            """Decorator for any action requiring an active database session.

            This decorator wraps the input func in a `with` clause that will create and begin a database session if no session is provided.
            The conditional logic for creating the session exists to allow manual handling of sessions without the need to modify this decorator or remove references to it.
            """

            @wraps(func)
            def _wrapper(*args, session: Optional[Session] = None, **kwargs):
                nested = True if session is not None else False
                with Database.get_session() if session is None else session as session, session.begin(
                    nested=nested
                ):
                    result = func(*args, session=session, **kwargs)
                return result

            return _wrapper

    @classmethod
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
        maker = sessionmaker(bind=engine)

        return maker()

    @classmethod
    @_Decorators.with_session
    def insert(cls, row: Type[Base], session: Optional[Session] = None) -> None:
        session.add(row)

    # TODO: Can this be overloaded to handle either a filter or a sequence of objects?
    @classmethod
    @_Decorators.with_session
    def delete(
        cls,
        model: Type[Base],
        filter: Optional[Dict] = {},
        session: Optional[Session] = None,
    ) -> None:
        query = delete(model)
        for key, value in filter.items():
            query = query.where(key == value)
        session.execute(query)

    @classmethod
    @_Decorators.with_session
    def get_all_rows(
        cls, model: Type[Base], session: Optional[Session] = None
    ) -> List[Type[Base]]:
        query = select(model)
        result = session.scalars(query).all()
        session.expunge_all()
        return result

    @classmethod
    @_Decorators.with_session
    def get_rows(
        cls,
        model: Type[Base],
        filter: Optional[dict] = None,
        session: Optional[Session] = None,
    ) -> List[Type[Base]]:
        """Return a :class:`List[sqlalchemy.engine.Row]` models that match the input query.

        :example: Filter can be formatted as follows:

        .. code-block:: python
            filter: dict = {
                User.name: "John Doe"
            }

        .. code-block:: python
            filter: dict = {
                Claan.claan: Claans.EARTH_STRIDERS
            }


        :param model: The model to return, must inherit :class:`models.Base`.

        :param filter: An optional :class:`dict` defining the filter, where keys are :class:`Base.Column` and values are the value the key should match.

            .. note:: If no filter is provided, all rows are returned.

        :return: List of :class:`sqlalchemy.engine.Row` models that matched the query filter.
        """
        if filter is None:
            return cls.get_all_rows(model, session)

        query = select(model)
        for k, v in filter.items():
            query = query.where(k == v)

        result = session.scalars(query).all()
        session.expunge_all()
        return result

    @classmethod
    @_Decorators.with_session
    def get_claan_scores(cls, session: Optional[Session] = None) -> Dict[Claan, int]:
        """Returns a formatted dict of Claans and their scores for the current Season."""
        query_season = select(func.max(Season.start_date))
        this_season = session.scalar(query_season)

        query = (
            select(Record.claan, func.sum(Record.score).label("score"))
            .where(Record.timestamp >= this_season)
            .group_by("claan")
        )
        result = session.execute(query).all()

        scores: dict = {claan: 0 for claan in Claan}
        for row in result:
            scores[row.claan] = row.score

        return scores

    @classmethod
    @_Decorators.with_session
    def get_active_quests(cls, session: Optional[Session] = None) -> List[Task]:
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
    @_Decorators.with_session
    def get_active_activities(cls, session: Optional[Session] = None) -> List[Task]:
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
    @_Decorators.with_session
    def get_fortnight(
        cls, timestamp: Optional[date] = None, session: Optional[Session] = None
    ) -> int:
        """Returns the integer representation of the current fortnight for the active season.

        :param date: An optional instance of :class:`datetime.date`, otherwise today will be used.
        :param engine: An optional instance of :class:`sqlalchemy.engine.base.Engine`.
            .. note:: If no engine is provided, :meth:get_database_engine will be called with default parameters.
        :return: :class:`int` representation of current fortnight for this season, indexed to zero.
        """
        if timestamp is None:
            timestamp = date.today()

        season_start: date = session.execute(
            select(func.max(Season.start_date))
        ).scalar_one()

        weeks = floor((timestamp - season_start).days / 7)
        LOGGER.info(f"Weeks: {weeks}")
        weeks = floor(weeks / 2)
        LOGGER.info(f"Weeks: {weeks}")

    @classmethod
    @_Decorators.with_session
    def submit_record(
        cls, task: Task, user: User, session: Optional[Session] = None
    ) -> bool:
        LOGGER.info(
            f"Beginning record submission for {user.name} with {task.description}"
        )
        if task.dice == Dice.D12:
            LOGGER.info("Die is D12, checking fortnight")
            # Check fortnight
            fortnight = Database.get_fortnight(timestamp=date.today(), session=session)
            LOGGER.info(f"This fortnight number: {fortnight}")
            query = select(func.max(Season.start_date))
            LOGGER.info(f"QUERY:\n{query}")
            season_start: date = session.execute(query).scalar_one()
            LOGGER.info(f"Season start date defined as {season_start}")
            fortnight_start = season_start + timedelta(weeks=(fortnight * 2))
            LOGGER.info(f"From this, fortnight start: {fortnight_start}")
            query = select(Record).where(
                Record.user_id == user.id,
                Record.task_id == task.id,
                Record.timestamp >= fortnight_start,
            )
            LOGGER.info(f"QUERY:\n{query}")
            result = session.execute(query).scalar_one_or_none()
            LOGGER.info(f"Result for lookup: {result}")
            pass
        else:
            # Check day
            LOGGER.info("Die not D12, checking daily")
            query = select(Record).where(
                Record.user_id == user.id,
                Record.task_id == task.id,
                Record.timestamp >= date.today(),
            )
            LOGGER.info(f"QUERY:\n{query}")
            result = session.execute(query).scalar_one_or_none()
            LOGGER.info(f"Result for lookup: {result}")

        if result is not None:
            LOGGER.warning(
                f"Daily/Fortnight check failed, result is not None: {result}"
            )
            return False

        LOGGER.info("No existing record found, will submit")
        record = Record(task=task, user=user, claan=user.claan, dice=task.dice)
        LOGGER.info(f"Record to submit:\n{vars(record)}")
        session.add(record)
        LOGGER.info("SUBMISSION DONE\n")
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

                if count < 3:
                    for _ in range(3 - count):
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
