from datetime import date, timedelta
from math import floor
from typing import Dict, List, Optional

import streamlit as st
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from src.models.claan import Claan
from src.models.dice import Dice
from src.models.market.portfolio import Portfolio
from src.models.record import Record
from src.models.season import Season
from src.models.task import Task
from src.models.user import User
from src.utils import stock_game
from src.utils.logger import LOGGER


@st.cache_data(ttl=600)
def get_scores(_session: Session) -> List[Record]:
    season_start = get_season_start(_session=_session)

    query = (
        select(Record.claan, func.sum(Record.score).label("score"))
        .where(Record.timestamp >= season_start)
        .group_by("claan")
    )
    result = _session.execute(query).all()

    scores: dict = {claan: 0 for claan in Claan}
    for row in result:
        scores[row.claan] = row.score

    return scores


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
    count = _session.execute(query_count).scalar_one_or_none()

    return {
        "score_season": score_season or 0,
        "score_fortnight": score_fortnight or 0,
        "task_count": count or 0,
    }


@st.cache_data
def get_historical_data(_session: Session, claan: Claan) -> None:
    season_start = get_season_start(_session=_session)

    query = (
        select(User.name, Task.description, Task.dice, Record.score, Record.timestamp)
        .join(Record.user)
        .join(Record.task)
        .where(Record.claan == claan)
        .where(Record.timestamp >= season_start)
        .order_by(Record.timestamp.desc())
    )
    records = _session.execute(query).all()

    return records


@st.cache_data()
def get_tasks(_session: Session) -> List[Task]:
    query = select(Task).order_by(Task.dice.asc())
    result = _session.execute(query).scalars().all()

    return result


@st.cache_data()
def get_active_tasks(_session: Session) -> List[Task]:
    query = select(Task).where(Task.active)
    result = _session.execute(query).scalars().all()

    return result


def add_task(_session: Session) -> Task:
    if st.session_state.keys() < {
        "add_task_description",
        "add_task_dice",
        "add_task_ephemeral",
    }:
        LOGGER.error("`add_task` called but required keys not in session state")
        st.warning("Unable to add task, missing keys in session state.")
        return

    task_description = st.session_state["add_task_description"]
    task_dice = st.session_state["add_task_dice"]
    task_ephemeral = st.session_state["add_task_ephemeral"]

    task = Task(
        description=task_description,
        dice=task_dice,
        ephemeral=task_ephemeral,
    )

    _session.add(task)
    _session.commit()

    if "tasks" in st.session_state:
        get_tasks.clear()
        st.session_state["tasks"] = get_tasks(_session=_session)

    return task


def delete_task(_session: Session) -> None:
    if st.session_state.keys() < {"delete_task_selection"}:
        LOGGER.error("`delete_task` called but no task in session state")
        st.warning("Unable to delete task, missing keys in session state.")
        return

    target = st.session_state["delete_task_selection"]
    task = _session.get(Task, target.id)
    _session.delete(task)
    _session.commit()

    if "tasks" in st.session_state:
        get_tasks.clear()
        st.session_state["tasks"] = get_users(_session=_session)

    if "active_task" in st.session_state and task in st.session_state["active_quest"]:
        get_active_tasks.clear()
        st.session_state["active_quest"] = get_active_tasks(_session=_session)


def set_active_task(_session: Session) -> None:
    if st.session_state.keys() < {
        "set_active_task_selection",
        "set_active_task_dice",
    }:
        LOGGER.error("`set_active_task` called but required keys not in session state")
        st.warning("Unable to set active task, missing keys in session state.")
        return

    query = (
        select(Task)
        .filter_by(
            active=True,
        )
        .limit(1)
    )
    task_current = _session.execute(query).scalar_one_or_none()
    task_new = _session.get(Task, st.session_state["set_active_task_selection"].id)

    if task_current is not None:
        task_current.active = False
    task_new.active = True

    _session.commit()

    if "tasks" in st.session_state:
        LOGGER.info("Reloading `tasks`")
        get_tasks.clear()
        st.session_state["tasks"] = get_tasks(_session=_session)

    if "active_task" in st.session_state:
        LOGGER.info("Reloading `active_task")
        get_active_tasks.clear()
        st.session_state["active_task"] = get_active_tasks(_session=_session)


@st.cache_data(ttl=timedelta(weeks=2))
def get_season_start(_session: Session) -> date:
    query = select(func.max(Season.start_date))
    result = _session.execute(query).scalar_one()

    return result


# TODO: Docstring
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


@st.cache_data(ttl=timedelta(days=1))
def get_fortnight_info(_session: Session) -> Dict[str, int | date]:
    """Returns a dict containing fortnight information.

    Dict contains fortnight number, start date, end date.
    """
    season_start = get_season_start(_session=_session)
    fortnight_number = get_fortnight_number(
        _session=_session, season_start=season_start
    )
    start_date = get_fortnight_start(
        _session=_session, season_start=season_start, fortnight_number=fortnight_number
    )
    end_date = start_date + timedelta(weeks=2)

    return {
        "fortnight_number": fortnight_number,
        "start_date": start_date,
        "end_date": end_date,
    }


def submit_record(_session: Session) -> Record:
    if st.session_state.keys() < {
        "task_user",
        "task_selection",
    }:
        LOGGER.error("`submit_record` called but required keys not in session state")
        st.warning(
            "Something went wrong, record could not be submitted, please report this issue."
        )
        return

    record_claan = st.session_state["task_user"].claan
    record_dice = st.session_state["task_selection"].dice

    record = Record(
        task=st.session_state["task_selection"],
        user=st.session_state["task_user"],
        claan=record_claan,
        dice=record_dice,
    )

    # Fortnightly quest
    result = None
    if record_dice == Dice.D12:
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
        st.warning(
            "Unable to submit record, looks like you've submitted this task too recently!"
        )
        return

    _session.add(record)
    _session.commit()

    st.success(f"Task logged! Roll: {record.score}")

    if "scores" in st.session_state:
        LOGGER.info("Reloading `scores`")
        get_scores.clear()
        st.session_state["scores"] = get_scores(_session=_session)

    if f"data_{record_claan.name}" in st.session_state:
        LOGGER.info("Reloading `data`")
        stock_game.get_corporate_data.clear(claan=record_claan)
        st.session_state[f"data_{record_claan.name}"] = stock_game.get_corporate_data(
            _session=_session, claan=record_claan
        )

    return record


@st.cache_data()
def get_users(_session: Session) -> List[User]:
    query = select(User).order_by(User.name.asc())
    result = _session.execute(query).scalars().all()

    return result


# TODO: Add claan table with backpopulated users field and populate this way?
@st.cache_data()
def get_claan_users(_session: Session, claan: Claan) -> List[User]:
    query = select(User).where(User.claan == claan)
    result = _session.execute(query).scalars().all()

    return result


def get_portfolio(_session: Session, _user: User) -> Portfolio:
    portfolio_query = select(Portfolio).where(Portfolio.user_id == _user.id)
    portfolio = _session.execute(portfolio_query).scalars().one()

    return portfolio


def update_vote(_session: Session, _portfolio: Portfolio) -> None:
    portfolio = _session.get(Portfolio, _portfolio.id)
    portfolio.board_vote = st.session_state["portfolio_vote"]
    _session.commit()
    st.toast("Vote updated")


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

    if "users" in st.session_state:
        LOGGER.info("Reloading `users`")
        get_users.clear()
        st.session_state["users"] = get_users(_session=_session)

    if f"users_{user.claan.name}" in st.session_state:
        LOGGER.info(f"Reloading `users_{user.claan.name}`")
        get_claan_users.clear(claan=user.claan)
        if f"users_{user.claan.name}" in st.session_state:
            st.session_state[f"users_{user.claan.name}"] = get_claan_users(
                _session=_session, claan=user.claan
            )

    return user


def update_user(_session: Session) -> User:
    if st.session_state.keys() < {
        "update_user_user",
        "update_user_name",
        "update_user_long_name",
        "update_user_id",
        "update_user_claan",
        "update_user_email",
        "update_user_active",
    }:
        LOGGER.error("`update_user` called but key contents were missing.")
        st.warning(
            "Unable to update user, as keys were missing from the session state."
        )
        return

    user = _session.get(User, st.session_state["update_user_id"])

    user.long_name = st.session_state["update_user_long_name"]
    user.name = st.session_state["update_user_name"]
    user.email = st.session_state["update_user_email"]
    user.claan = st.session_state["update_user_claan"]
    user.active = st.session_state["update_user_active"]

    _session.commit()

    if "users" in st.session_state:
        LOGGER.info("Reloading `users`")
        get_users.clear()
        st.session_state["users"] = get_users(_session=_session)

    if f"users_{st.session_state["update_user_claan"].name}" in st.session_state:
        LOGGER.info(f"Reload `users_{st.session_state["update_user_claan"].name}")
        get_claan_users.clear(claan=st.session_state["update_user_claan"])
        if f"users_{st.session_state["update_user_claan"]}" in st.session_state:
            st.session_state[f"users_{st.session_state["update_user_claan"]}"] = (
                get_claan_users(
                    _session=_session, claan=st.session_state["update_user_claan"]
                )
            )


def delete_user(_session: Session) -> None:
    if st.session_state.keys() < {"delete_user_selection"}:
        LOGGER.error("`delete_user` called but no user in session state")
        st.warning("Unable to delete user, missing keys in session state.")
        return

    target = st.session_state["delete_user_selection"]
    user = _session.get(User, target.id)
    _session.delete(user)
    _session.commit()

    if "users" in st.session_state:
        LOGGER.info("Reloading `users`")
        get_users.clear()
        st.session_state["users"] = get_users(_session=_session)

    if f"users_{target.claan.name}" in st.session_state:
        LOGGER.info(f"Reloading `users_{target.claan.name}`")
        get_claan_users.clear(claan=target.claan)
        st.session_state[f"users_{target.claan.name}"] = get_claan_users(
            _session=_session, claan=target.claan
        )
