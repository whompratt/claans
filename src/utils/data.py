from datetime import date
from typing import List

import streamlit as st
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from src.models.claan import Claan
from src.models.record import Record
from src.models.season import Season
from src.models.task import Task, TaskType
from src.models.user import User
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
