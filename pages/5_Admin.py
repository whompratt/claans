import mongoengine
import pandas as pd
import streamlit as st

from models.record import RecordType
from utils.claans import Claans
from utils.data import Data
from utils.dice import Dice


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


@st.experimental_fragment
def delete_user_form():
    with st.container(border=True):
        st.subheader("Delete User")
        claan = st.selectbox(
            label="Claan",
            key="delete_user_claan",
            options=Claans,
            format_func=lambda claan: claan.value,
        )
        user = None
        if claan:
            claan_users = Data.get_users(
                {"claan": st.session_state["delete_user_claan"]}
            )
            user = st.selectbox(
                label="User",
                key="delete_user_name",
                options=list(claan_users),
                format_func=lambda user: user.name,
            )

        submit_enabled = claan and user
        if st.button(
            "Submit",
            type="primary",
            disabled=not submit_enabled,
            on_click=Data.delete_user,
        ):
            st.rerun()


@st.experimental_fragment
def set_active_form():
    with st.container(border=True):
        st.subheader("Set Active Tasks")
        st.selectbox


def user_management() -> None:
    with st.container(border=True):
        st.subheader("User Management")

        col_df, col_forms = st.columns(2)

        with col_df:
            df_users = pd.DataFrame.from_records(
                data=list(st.session_state["users"].as_pymongo())
            )
            if "_id" in df_users.keys():
                df_users.drop("_id", axis=1, inplace=True)
            st.dataframe(
                data=df_users,
                use_container_width=True,
                hide_index=True,
                column_config={"name": "Name", "claan": "Claan"},
            )
        with col_forms:
            with st.form(key="add_user", clear_on_submit=True, border=True):
                st.subheader("Add User")
                st.text_input(label="Name", key="add_user_name", placeholder="John Doe")
                st.selectbox(
                    label="Claan",
                    key="add_user_claan",
                    options=Claans,
                    format_func=lambda claan: claan.value,
                )
                st.form_submit_button(
                    label="Submit",
                    on_click=Data.add_user,
                )
            delete_user_form()


def score_management() -> None:
    with st.container(border=True):
        st.subheader("Score Management")

        col_df, col_forms = st.columns(2)

        with col_df:
            df_scores = pd.DataFrame.from_records(
                data=list(st.session_state["scores"].as_pymongo())
            )
            if "_id" in df_scores.keys():
                df_scores.drop("_id", axis=1, inplace=True)
            st.dataframe(
                data=df_scores,
                use_container_width=True,
                hide_index=True,
            )
        with col_forms:
            with st.form(key="set_score", clear_on_submit=True, border=True):
                st.subheader("Set Score")
                st.selectbox(
                    label="Claan",
                    key="set_score_claan",
                    options=Claans,
                    format_func=lambda claan: claan.value,
                )
                st.number_input(
                    label="Score",
                    key="set_score_value",
                    placeholder=0,
                    min_value=0,
                    step=1,
                )
                st.form_submit_button(
                    label="Submit",
                    on_click=Data.set_score,
                )


def task_management() -> None:
    with st.container(border=True):
        st.subheader("Task Management")

        col_df, col_forms = st.columns(2)

        with col_df:
            df_tasks = pd.DataFrame.from_records(
                data=list(st.session_state["tasks"].as_pymongo())
            )
            if "_id" in df_tasks.keys():
                df_tasks.drop("_id", axis=1, inplace=True)
            st.dataframe(data=df_tasks, use_container_width=True, hide_index=True)
        with col_forms:
            with st.form(key="add_task", clear_on_submit=True, border=True):
                st.subheader("Add Task")
                st.text_input(label="Description", key="add_task_description")
                st.selectbox(
                    label="Type",
                    key="add_task_type",
                    options=RecordType,
                    format_func=lambda type: type.name.capitalize(),
                )
                st.multiselect(
                    label="Dice",
                    key="add_task_dice",
                    options=Dice,
                    format_func=lambda die: die.name,
                )
                st.toggle(
                    label="Ephemeral",
                    key="add_task_ephemeral",
                    help="When true, task may only be active once",
                )
                st.form_submit_button(
                    label="Submit",
                    on_click=Data.add_task,
                )
            with st.form(key="delete_task", clear_on_submit=True, border=True):
                st.subheader("Delete Task")
                st.selectbox(
                    label="Task",
                    key="delete_task_description",
                    options=list(st.session_state["tasks"]),
                    format_func=lambda task: task.description,
                )
                st.form_submit_button(
                    label="Submit",
                    on_click=Data.delete_task,
                )

    with st.container(border=True):
        st.subheader("Active Tasks")

        col_df, col_forms = st.columns(2)

        # with col_df:
        # df_active = pd.DataFrame.from_records(
        #     data=list(st.session_state["active"].as_pymongo())
        # )
        # if "_id" in df_active.keys():
        #     df_active.drop("_id", axis=1, inplace=True)
        # st.dataframe(data=df_active, use_container_width=True, hide_index=True)


def init_page() -> None:
    st.set_page_config(page_title="Admin", layout="wide")
    mongoengine.connect(**st.secrets["mongo"])

    Data.load_data()

    if not check_password():
        st.stop()

    with st.container(border=True):
        st.header("Admin Page")

        st.button(
            label="Initialise Database",
            key="button_init_data",
            on_click=Data.init_data,
        )

        st.button(
            label="Refresh All Data",
            key="button_refresh_all",
            on_click=Data.refresh_all,
        )

        user_management()
        score_management()
        task_management()


if __name__ == "__main__":
    init_page()
