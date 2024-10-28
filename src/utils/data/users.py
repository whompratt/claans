from typing import List

import streamlit as st
from sqlalchemy import select
from sqlalchemy.orm import Session

from src.models.claan import Claan
from src.models.user import User
from src.utils.logger import LOGGER


@st.cache_data()
def get_users(_session: Session) -> List[User]:
    query = select(User).order_by(User.name.asc())
    result = _session.execute(query).scalars().all()

    return result


@st.cache_data()
def get_claan_users(_session: Session, claan: Claan) -> List[User]:
    query = select(User).where(User.claan == claan).order_by(User.name)
    result = _session.execute(query).scalars().all()

    return result


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
        if f"users_{st.session_state["update_user_claan"].name}" in st.session_state:
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
