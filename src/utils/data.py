from datetime import date, timedelta
from math import floor
from typing import List, Optional

import streamlit as st
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from src.models.claan import Claan
from src.models.dice import Dice
from src.models.record import Record
from src.models.season import Season
from src.models.task import Task, TaskType
from src.models.user import User
from src.utils.logger import LOGGER
from src.utils.timer import timer


@timer
@st.cache_data(ttl=600)
def get_scores(_session: Session) -> List[Record]:
    query = select(func.max(Season.start_date))
    season: date = _session.scalar(query)

    query = (
        select(Record.claan, func.sum(Record.score).label("score"))
        .where(Record.timestamp >= season)
        .group_by("claan")
    )
    result = _session.execute(query).all()

    scores: dict = {claan: 0 for claan in Claan}
    for row in result:
        scores[row.claan] = row.score

    return scores


@timer
@st.cache_data(ttl=600)
def get_claan_data(_session: Session, claan: Claan):
    """Returns some stats about the given Claan.

    Return is a dict containing some data about the given claan, such as total score,
    delta score this fortnight, total quests submitted, total activities submittied.
    """
    season_start = get_season_start(_session=_session)
    fortnight_start = get_fortnight_start(_session=_session)

    query_score = select(func.sum(Record.score)).where(Record.claan == claan)
    score_season = _session.execute(
        query_score.where(Record.timestamp >= season_start)
    ).scalar_one_or_none()
    score_fortnight = _session.execute(
        query_score.where(Record.timestamp >= fortnight_start)
    ).scalar_one_or_none()

    query_count = (
        select(func.count())
        .select_from(Record)
        .join(Record.task)
        .where(Record.claan == claan)
    )
    count_quest = _session.execute(
        query_count.where(Task.task_type == TaskType.QUEST)
    ).scalar_one_or_none()
    count_activity = _session.execute(
        query_count.where(Task.task_type == TaskType.ACTIVITY)
    ).scalar_one_or_none()

    return {
        "score_season": score_season or 0,
        "score_fortnight": score_fortnight or 0,
        "count_quest": count_quest or 0,
        "count_activity": count_activity or 0,
    }


@timer
@st.cache_data()
def get_tasks(_session: Session) -> List[Task]:
    query = select(Task)
    result = _session.execute(query).scalars().all()

    return result


@timer
@st.cache_data()
def get_active_tasks(_session: Session, task_type: TaskType) -> List[Task]:
    query = select(Task).where(Task.active, Task.task_type == task_type)
    result = _session.execute(query).scalars().all()

    return result


@timer
def add_task(_session: Session) -> Task:
    if st.session_state.keys() < {
        "add_task_description",
        "add_task_type",
        "add_task_dice",
        "add_task_ephemeral",
    }:
        LOGGER.error("`add_task` called but required keys not in session state")
        st.warning("Unable to add task, missing keys in session state.")
        return

    task_description = st.session_state["add_task_description"]
    task_type = st.session_state["add_task_type"]
    task_dice = st.session_state["add_task_dice"]
    task_ephemeral = st.session_state["add_task_ephemeral"]

    task = Task(
        description=task_description,
        task_type=task_type,
        dice=task_dice,
        ephemeral=task_ephemeral,
    )

    _session.add(task)
    _session.commit()

    get_tasks.clear()
    st.session_state["tasks"] = get_tasks(_session=_session)

    return task


@timer
def delete_task(_session: Session) -> None:
    if st.session_state.keys() < {"delete_task_selection"}:
        LOGGER.error("`delete_task` called but no task in session state")
        st.warning("Unable to delete task, missing keys in session state.")
        return

    target = st.session_state["delete_task_selection"]
    task = _session.get(Task, target.id)
    _session.delete(task)
    _session.commit()

    get_tasks.clear()
    st.session_state["tasks"] = get_users(_session=_session)

    if "active_quest" in st.session_state and task in st.session_state["active_quest"]:
        get_active_tasks.clear(task_type=TaskType.QUEST)
        st.session_state["active_quest"] = get_active_tasks(
            _session=_session, task_type=TaskType.QUEST
        )
    if (
        "active_activity" in st.session_state
        and task in st.session_state["active_activity"]
    ):
        get_active_tasks.clear(task_type=TaskType.ACTIVITY)
        st.session_state["active_activity"] = get_active_tasks(
            _session=_session, task_type=TaskType.ACTIVITY
        )


@timer
def set_active_task(_session: Session, task_type: TaskType) -> None:
    if st.session_state.keys() < {
        f"set_active_{task_type.value}_selection",
        f"set_active_{task_type.value}_dice",
    }:
        LOGGER.error("`set_active_task` called but required keys not in session state")
        st.warning("Unable to set active task, missing keys in session state.")
        return

    query = (
        select(Task)
        .filter_by(
            task_type=task_type,
            dice=st.session_state[f"set_active_{task_type.value}_dice"],
            active=True,
        )
        .limit(1)
    )
    task_current = _session.execute(query).scalar_one_or_none()
    task_new = _session.get(
        Task, st.session_state[f"set_active_{task_type.value}_selection"].id
    )

    task_current.active = False
    task_new.active = True

    _session.commit()

    LOGGER.info("Reloading `tasks`")
    get_tasks.clear()
    st.session_state["tasks"] = get_tasks(_session=_session)

    LOGGER.info(f"Reloading `active_{task_type.value}")
    get_active_tasks.clear(task_type=task_type)
    st.session_state[f"active_{task_type.value}"] = get_active_tasks(
        _session=_session, task_type=task_type
    )


@timer
@st.cache_data(ttl=timedelta(weeks=2))
def get_season_start(_session: Session) -> date:
    query = select(func.max(Season.start_date))
    result = _session.execute(query).scalar_one()

    return result


# TODO: Docstring
@timer
@st.cache_data(ttl=timedelta(days=1))
def get_fortnight_number(
    _session: Session,
    timestamp: Optional[date] = None,
    season_start: Optional[date] = None,
) -> int:
    """Returns the integer representation of the current fortnight for the active season.

    :param _session: An optional instance of :class:`sqlalchemy.engine.base.Engine`.
    :param timestamp: An optional instance of :class:`datetime.date`, otherwise today will be used.
        .. note:: If no engine is provided, :meth:get_database_engine will be called with default parameters.
    :return: :class:`Tuple[date, int]` representation of the start date of the current season, and the number for current fortnight for this season, indexed to zero.
    """
    if timestamp is None:
        timestamp = date.today()

    if season_start is None:
        season_start = get_season_start(_session=_session)

    fortnight_number = floor((timestamp - season_start).days / 14)
    return fortnight_number


@st.cache_data(ttl=timedelta(days=1))
def get_fortnight_start(
    _session: Session,
    timestamp: Optional[date] = None,
    season_start: Optional[date] = None,
    fortnight_number: Optional[int] = None,
) -> date:
    if timestamp is None:
        timestamp = date.today()
    if season_start is None:
        season_start = get_season_start(_session=_session)
    if fortnight_number is None:
        fortnight_number = get_fortnight_number(
            _session=_session, timestamp=timestamp, season_start=season_start
        )

    fortnight_start = season_start + timedelta(weeks=(fortnight_number * 2))

    return fortnight_start


@timer
def submit_record(_session: Session, task_type: TaskType) -> Record:
    if st.session_state.keys() < {
        f"{task_type.value}_user",
        f"{task_type.value}_selection",
    }:
        LOGGER.error("`submit_record` called but required keys not in session state")
        st.warning(
            "Something went wrong, record could not be submitted, please report this issue."
        )
        return

    record = Record(
        task=st.session_state[f"{task_type.value}_selection"],
        user=st.session_state[f"{task_type.value}_user"],
        claan=st.session_state[f"{task_type.value}_user"].claan,
        dice=st.session_state[f"{task_type.value}_selection"].dice,
    )
    user = _session.get(User, record.user_id)
    task = _session.get(Task, record.task_id)

    # Fortnightly quest
    result = None
    if task.dice == Dice.D12:
        season_start = get_season_start(_session=_session)
        fortnight_number = get_fortnight_number(_session=_session)
        query = (
            select(func.count())
            .select_from(Record)
            .where(
                Record.user_id == record.user_id,
                Record.task_id == record.task_id,
                Record.timestamp
                >= (season_start + timedelta(weeks=(fortnight_number * 2))),
            )
        )
        result = _session.execute(query).scalar_one_or_none()
    else:
        query = (
            select(func.count())
            .select_from(Record)
            .where(
                Record.user_id == record.user_id,
                Record.task_id == record.task_id,
                Record.timestamp >= date.today(),
            )
        )
        result = _session.execute(query).scalar_one_or_none()

    if result >= 1:
        LOGGER.info(f"User {user.name} attempted to submit a record too frequently")
        st.warning(
            "Unable to submit record, looks like you've submitted this task too recently!"
        )
        return

    _session.add(record)
    _session.commit()

    LOGGER.info("Reloading `scores`")
    get_scores.clear()
    st.session_state["scores"] = get_scores(_session=_session)

    if f"data_{user.claan.name}" in st.session_state:
        LOGGER.info("Reloading `data`")
        get_claan_data.clear(claan=user.claan)
        st.session_state[f"data_{user.claan.name}"] = get_claan_data(
            _session=_session, claan=user.claan
        )

    return record


@timer
@st.cache_data()
def get_users(_session: Session) -> List[User]:
    query = select(User)
    result = _session.execute(query).scalars().all()

    return result


# TODO: Add claan table with backpopulated users field and populate this way?
@timer
@st.cache_data()
def get_claan_users(_session: Session, claan: Claan) -> List[User]:
    query = select(User).where(User.claan == claan)
    result = _session.execute(query).scalars().all()

    return result


@timer
def add_user(_session: Session) -> User:
    if st.session_state.keys() < {"add_user_name", "add_user_claan"}:
        LOGGER.error("`add_user` called but required keys not in session state")
        st.warning("Unable to add user, missing keys in session state.")
        return

    user = User(
        name=st.session_state["add_user_name"],
        claan=st.session_state["add_user_claan"],
    )

    _session.add(user)
    _session.commit()

    LOGGER.info("Reloading `users`")
    get_users.clear()
    st.session_state["users"] = get_users(_session=_session)

    LOGGER.info(f"Reloading `users_{user.claan.name}`")
    get_claan_users.clear(claan=user.claan)
    if f"users_{user.claan.name}" in st.session_state:
        st.session_state[f"users_{user.claan.name}"] = get_claan_users(
            _session=_session, claan=user.claan
        )

    return user


@timer
def delete_user(_session: Session) -> None:
    if st.session_state.keys() < {"delete_user_selection"}:
        LOGGER.error("`delete_user` called but no user in session state")
        st.warning("Unable to delete user, missing keys in session state.")
        return

    target = st.session_state["delete_user_selection"]
    user = _session.get(User, target.id)
    _session.delete(user)
    _session.commit()

    LOGGER.info("Reloading `users`")
    get_users.clear()
    st.session_state["users"] = get_users(_session=_session)

    LOGGER.info(f"Reloading `users_{target.claan.name}`")
    get_claan_users.clear(claan=target.claan)
    if f"users_{target.claan.name}" in st.session_state:
        st.session_state[f"users_{target.claan.name}"] = get_claan_users(
            _session=_session, claan=target.claan
        )
