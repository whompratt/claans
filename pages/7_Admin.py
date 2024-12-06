import pandas as pd
import streamlit as st

from src.models.claan import Claan
from src.models.task_reward import TaskReward
from src.models.user import User
from src.utils.data.scores import get_scores
from src.utils.data.stocks import (
    add_user,
    delete_unowned_company_share,
    get_all_shares,
    get_instruments,
    issue_company_share,
    issue_credit,
    process_escrow,
)
from src.utils.data.tasks import add_task, delete_task, get_tasks, set_active_task
from src.utils.data.users import (
    delete_user,
    get_claan_users,
    get_users,
    update_user,
)
from src.utils.database import Database, initialise


def load_data():
    if "db_session" not in st.session_state:
        st.session_state["db_session"] = Database.get_session()
    st.session_state["tasks"] = get_tasks(_session=st.session_state["db_session"])
    st.session_state["users"] = get_users(_session=st.session_state["db_session"])
    st.session_state["scores"] = get_scores(_session=st.session_state["db_session"])
    st.session_state["instruments"] = get_instruments(
        _session=st.session_state["db_session"]
    )
    st.session_state["shares"] = get_all_shares(_session=st.session_state["db_session"])

    for claan in Claan:
        st.session_state[f"users_{claan}"] = get_claan_users(
            _session=st.session_state["db_session"], claan=claan
        )


def refresh_data():
    """Hard refresh of all data, including clearing data cache."""
    st.cache_data.clear()
    load_data()


def check_password():
    def password_entered():
        if st.session_state["admin_password"] == st.secrets["passwords"]["admin"]:
            st.session_state["admin_password_correct"] = True
            del st.session_state["admin_password"]
        else:
            st.session_state["admin_password_correct"] = False

    if st.session_state.get("admin_password_correct", False) or st.secrets.get(
        "env"
    ).get("debug", False):
        return True

    st.text_input(
        "Admin Password",
        type="password",
        on_change=password_entered,
        key="admin_password",
    )

    if "password_correct" in st.session_state:
        st.error("Incorrect Admin Password.")

    return False


@st.fragment
def update_user_form():
    with st.container(border=True):
        st.subheader("Update User")
        user: User = st.selectbox(
            label="User",
            key="update_user_user",
            options=sorted(st.session_state["users"]),
        )
        if user:
            if user.claan:
                claan_index = list(Claan).index(user.claan)
            else:
                claan_index = None
            st.text_input(
                label="Name",
                key="update_user_name",
                value=user.name,
            )
            st.text_input(
                label="Long name",
                key="update_user_long_name",
                value=user.long_name,
                disabled=True,
            )
            st.text_input(
                label="Id",
                key="update_user_id",
                value=user.id,
                disabled=True,
            )
            st.selectbox(
                label="Claan",
                key="update_user_claan",
                options=Claan,
                format_func=lambda claan: claan.value,
                index=claan_index,
            )
            st.text_input(label="Email", key="update_user_email", value=user.email)
            st.checkbox(
                label="Active",
                value=user.active,
                key="update_user_active",
            )

            st.button(
                label="Submit",
                key="update_user_button",
                type="primary",
                on_click=update_user,
                kwargs={"_session": st.session_state["db_session"]},
            )


@st.fragment
def delete_user_form():
    with st.container(border=True):
        st.subheader("Delete User")
        claan = st.selectbox(
            label="Claan",
            key="delete_user_claan",
            options=Claan,
            format_func=lambda claan: claan.value,
        )
        user = None
        if claan:
            user = st.selectbox(
                label="User",
                key="delete_user_selection",
                options=st.session_state[
                    f"users_{st.session_state["delete_user_claan"]}"
                ],
                format_func=lambda user: user.name,
            )

        submit_enabled = claan and user
        if st.button(
            "Submit",
            type="primary",
            disabled=not submit_enabled,
            on_click=delete_user,
            kwargs={"_session": st.session_state["db_session"]},
        ):
            st.rerun()


def user_management() -> None:
    with st.container(border=True):
        st.subheader("User Management")

        col_forms, col_df = st.columns(2)

        with col_forms:
            with st.form(key="add_user", clear_on_submit=True, border=True):
                st.subheader("Add User")
                st.text_input(
                    label="Name", key="add_user_long_name", placeholder="John Doe"
                )
                st.text_input(
                    label="Email",
                    key="add_user_email",
                    placeholder="john.doe@advancinganalytics.co.uk",
                )
                st.selectbox(
                    label="Claan",
                    key="add_user_claan",
                    options=Claan,
                    format_func=lambda claan: claan.value,
                )
                st.form_submit_button(
                    label="Submit",
                    on_click=add_user,
                    kwargs={"_session": st.session_state["db_session"]},
                )
            update_user_form()
            delete_user_form()
        with col_df:
            df_users = pd.DataFrame.from_records(
                data=[vars(user) for user in st.session_state["users"]]
            )
            if "_sa_instance_state" in df_users.columns:
                df_users.drop("_sa_instance_state", inplace=True, axis=1)
            if "claan" in df_users.columns:
                df_users["claan"] = df_users["claan"].apply(
                    lambda x: x.value if x is not None else "None"
                )

            st.dataframe(
                data=df_users,
                use_container_width=True,
                hide_index=True,
                column_config={"name": "Name", "claan": "Claan"},
            )


@st.fragment
def set_active_task_form():
    with st.container(border=True):
        st.subheader("Set Active Tasks")
        quest_reward = st.selectbox(
            label="Dice to Update",
            key="set_active_task_reward",
            options=list(TaskReward),
            format_func=lambda dice: dice.name,
        )
        quest_selection = None
        if quest_reward:
            quest_selection = st.selectbox(
                label="Quest",
                key="set_active_task_selection",
                options=[
                    task
                    for task in st.session_state["tasks"]
                    if task.reward == quest_reward
                ],
                format_func=lambda task: task.description,
            )
        if st.button(
            label="Submit",
            key="set_active_task_submit",
            disabled=not (quest_reward and quest_selection),
            on_click=set_active_task,
            kwargs={"_session": st.session_state["db_session"]},
        ):
            st.rerun()


def task_management() -> None:
    with st.container(border=True):
        st.subheader("Task Management")

        with st.container(border=True):
            st.header("Claan Info")
            cols = st.columns(len(list(Claan)))
            for claan in Claan:
                with cols[list(Claan).index(claan)]:
                    st.metric(
                        label=claan.name,
                        value=len(
                            [
                                user
                                for user in st.session_state["users"]
                                if user.claan == claan
                            ]
                        ),
                    )
                    st.metric(label="Score", value=st.session_state["scores"][claan])

        col_df, col_forms = st.columns(2)

        with col_df:
            df_tasks = pd.DataFrame.from_records(
                data=[vars(task) for task in st.session_state["tasks"]]
            )
            if "_sa_instance_state" in df_tasks.columns:
                df_tasks.drop("_sa_instance_state", inplace=True, axis=1)
            if "reward" in df_tasks.columns:
                df_tasks["reward"] = df_tasks["reward"].apply(lambda x: x.value)
            st.dataframe(
                data=df_tasks,
                use_container_width=True,
                hide_index=True,
            )
        with col_forms:
            set_active_task_form()
            with st.form(key="add_task", clear_on_submit=True, border=True):
                st.subheader("Add Task")
                st.text_input(label="Description", key="add_task_description")
                st.selectbox(
                    label="Dice",
                    key="add_task_dice",
                    options=TaskReward,
                    format_func=lambda die: die.name,
                )
                st.toggle(
                    label="Ephemeral",
                    key="add_task_ephemeral",
                    help="When true, task may only be active once",
                )
                st.form_submit_button(
                    label="Submit",
                    on_click=add_task,
                    kwargs={"_session": st.session_state["db_session"]},
                )
            with st.form(key="delete_task", clear_on_submit=True, border=True):
                st.subheader("Delete Task")
                st.selectbox(
                    label="Task",
                    key="delete_task_selection",
                    options=list(st.session_state["tasks"]),
                    format_func=lambda task: task.description,
                )
                st.form_submit_button(
                    label="Submit",
                    on_click=delete_task,
                    kwargs={"_session": st.session_state["db_session"]},
                )


def share_management() -> None:
    with st.container(border=True):
        st.header("Share Management")

        with st.container(border=True):
            cols = st.columns(len(st.session_state["instruments"]))
            for instrument in st.session_state["instruments"]:
                with cols[st.session_state["instruments"].index(instrument)]:
                    st.metric(
                        label=instrument.ticker,
                        value=len(
                            [
                                share
                                for share in st.session_state["shares"]
                                if share.instrument_id == instrument.id
                            ]
                        ),
                    )

        instrument = st.selectbox(
            label="Select Instrument",
            key="instrument",
            options=st.session_state["instruments"],
            format_func=lambda instrument: instrument.ticker,
            index=None,
        )

        if st.button(
            label="Process Escrow",
            key="process_escrow",
        ):
            process_escrow(_session=st.session_state["db_session"])

        credit_value = float(
            st.number_input(
                label="Credit amount",
                min_value=1.0,
                max_value=50.0,
                value=10.0,
                step=0.1,
                key="credit_amount",
            )
        )
        if st.button(
            label="Issue Credit",
            key="issue_credit",
        ):
            issue_credit(
                _session=st.session_state["db_session"], value=round(credit_value, 2)
            )

        if instrument:
            st.number_input(
                label="Amount",
                min_value=1,
                max_value=50,
                value=1,
                step=1,
                key="issue_amount",
            )
            if st.button(
                label="Issue share",
                key="issue_share",
            ):
                issue_company_share(
                    _session=st.session_state["db_session"], instrument=instrument
                )
            if st.button(
                label="Delete share",
                key="delete_share",
            ):
                delete_unowned_company_share(
                    _session=st.session_state["db_session"], instrument=instrument
                )


def init_page() -> None:
    st.set_page_config(page_title="Admin", layout="wide")

    if not check_password():
        st.stop()

    load_data()

    with st.container(border=True):
        st.header("Admin Page")

        st.button(
            label="Initialise Database",
            key="button_init_data",
            on_click=initialise,
        )
        st.button(
            label="Refresh Data", key="button_refresh_data", on_click=refresh_data
        )

        user_management()
        task_management()
        share_management()


if __name__ == "__main__":
    init_page()
