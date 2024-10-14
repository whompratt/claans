from datetime import date
from typing import Dict

import streamlit as st
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from src.models.claan import Claan
from src.models.record import Record
from src.models.task import Task
from src.models.user import User
from src.utils.data.seasons import get_fortnight_start, get_season_start
from src.utils.data.stocks import get_corporate_data
from src.utils.logger import LOGGER


@st.cache_data(ttl=600)
def get_scores(_session: Session) -> Dict[Claan, int]:
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


@st.cache_data(ttl=43200)
def get_historical_data(_session: Session, claan: Claan) -> None:
    season_start = get_season_start(_session=_session)

    query = (
        select(User.name, Task.description, Record.score, Record.timestamp)
        .join(Record.user)
        .join(Record.task)
        .where(Record.claan == claan)
        .where(Record.timestamp >= season_start)
        .order_by(Record.timestamp.desc())
    )
    records = _session.execute(query).all()

    return records


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
    record_reward = st.session_state["task_selection"].reward

    record = Record(
        task=st.session_state["task_selection"],
        user=st.session_state["task_user"],
        claan=record_claan,
        reward=record_reward,
    )
    # Fortnightly quest
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

    st.success(f"Task logged! ${record.score} added to escrow")

    if "scores" in st.session_state:
        LOGGER.info("Reloading `scores`")
        get_scores.clear()
        st.session_state["scores"] = get_scores(_session=_session)

    if f"data_{record_claan.name}" in st.session_state:
        LOGGER.info("Reloading `data`")
        get_corporate_data.clear(claan=record_claan)
        st.session_state[f"data_{record_claan.name}"] = get_corporate_data(
            _session=_session, claan=record_claan
        )

    return record
