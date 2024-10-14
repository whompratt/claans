from typing import List

import streamlit as st
from sqlalchemy import select
from sqlalchemy.orm import Session

from src.models.task import Task
from src.utils.data.users import get_users
from src.utils.logger import LOGGER


@st.cache_data()
def get_tasks(_session: Session) -> List[Task]:
    query = select(Task).order_by(Task.reward.asc())
    result = _session.execute(query).scalars().all()

    return result


@st.cache_data()
def get_active_tasks(_session: Session) -> List[Task]:
    query = select(Task).where(Task.active).order_by(Task.reward)
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
        reward=task_dice,
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
        "set_active_task_reward",
    }:
        LOGGER.error("`set_active_task` called but required keys not in session state")
        st.warning("Unable to set active task, missing keys in session state.")
        return

    query = (
        select(Task)
        .where(Task.active)
        .where(Task.reward == st.session_state["set_active_task_reward"])
    )
    task_current = _session.execute(query).scalar_one_or_none()
    task_new = _session.get(Task, st.session_state["set_active_task_selection"].id)

    if task_current is not None:
        task_current.active = False
    task_new.active = True

    _session.commit()

    if "active_tasks" in st.session_state:
        LOGGER.info("Reloading `active_tasks`")
        get_active_tasks.clear()
        st.session_state["active_tasks"] = get_active_tasks(_session=_session)
    if "tasks" in st.session_state:
        LOGGER.info("Reloading `tasks`")
        get_tasks.clear()
        st.session_state["tasks"] = get_tasks(_session=_session)
