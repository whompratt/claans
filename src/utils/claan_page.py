import pathlib

import streamlit as st

from src.models.claan import Claan
from src.models.task import TaskType
from src.utils import data
from src.utils.database import Database


class ClaanPage:
    def __init__(self, claan: Claan) -> None:
        self.claan = claan

        st.set_page_config(
            page_title=claan.value,
            page_icon=self.claan.get_icon(),
            layout="wide",
        )

        with Database.get_session() as session:
            if "active_quest" not in st.session_state:
                st.session_state["active_quest"] = data.get_active_tasks(
                    _session=session, task_type=TaskType.QUEST
                )
            if "active_activity" not in st.session_state:
                st.session_state["active_activity"] = data.get_active_tasks(
                    _session=session, task_type=TaskType.ACTIVITY
                )
            if f"users_{self.claan.name}" not in st.session_state:
                st.session_state[f"users_{self.claan.name}"] = data.get_claan_users(
                    _session=session, claan=self.claan
                )
            if "scores" not in st.session_state:
                st.session_state["scores"] = data.get_scores(_session=session)
            if f"data_{self.claan.name}" not in st.session_state:
                st.session_state[f"data_{self.claan.name}"] = data.get_claan_data(
                    _session=session, claan=self.claan
                )
            session.expunge_all()

        self.build_page()

    def check_password(self) -> bool:
        def password_entered():
            if st.session_state["password"] == st.secrets["passwords"][self.claan.name]:
                st.session_state[f"{self.claan.name}_password_correct"] = True
                del st.session_state["password"]
            else:
                st.session_state[f"{self.claan.name}_password_correct"] = False

        if st.secrets.env.get("debug"):
            return True

        if f"{self.claan.name}_password_correct" not in st.session_state:
            st.text_input(
                "Password", type="password", on_change=password_entered, key="password"
            )
            return False

        elif not st.session_state[f"{self.claan.name}_password_correct"]:
            st.text_input(
                "Password", type="password", on_change=password_entered, key="password"
            )
            st.error("😕 Password incorrect")
            return False

        else:
            return True

    def submit_quest(self):
        with Database.get_session() as session:
            task = st.session_state["quest_selection"]
            user = st.session_state["quest_user"]
            result = Database.submit_record(_session=session, task=task, user=user)
            if not result:
                st.warning(
                    "Error submitting quest, it looks like you've already submitted this quest..."
                )
            else:
                st.success("Quest submitted!")
                session.commit()
                data.get_scores.clear()
                st.session_state["scores"] = data.get_scores(_session=session)

    def submit_activity(self):
        with Database.get_session() as session:
            task = st.session_state["activity_selection"]
            user = st.session_state["activity_user"]
            result = Database.submit_record(_session=session, task=task, user=user)
            if not result:
                st.warning(
                    "Error submitting activity, it looks like you've already submitted this activity..."
                )
            else:
                st.success("Activity submitted!")
                session.commit()
                data.get_scores.clear()
                st.session_state["scores"] = data.get_scores(_session=session)

    def build_page(self):
        if not self.check_password():
            return

        # =-- HEADER --= #
        with st.container():
            header_left, header_right = st.columns((3, 1))

            with header_left:
                st.subheader("Advancing Analytics")
                st.title(self.claan.value)
                st.write(
                    f"Welcome to the {self.claan.value} Claan Area! Here you can log quests, activities, and steps!"
                )
                st.subheader("Fortnight Breakdown!")

                col_1, col_2, col_3, col_4 = st.columns(4)
                col_1.metric(
                    label="Overall Score",
                    value=st.session_state[f"data_{self.claan.name}"]["score_season"],
                )
                col_2.metric(
                    "Fortnight Score",
                    value=st.session_state[f"data_{self.claan.name}"][
                        "score_fortnight"
                    ],
                )
                col_3.metric(
                    "Tasks Completed",
                    value=st.session_state[f"data_{self.claan.name}"]["count_quest"],
                )
                col_4.metric(
                    "Activities Completed",
                    value=st.session_state[f"data_{self.claan.name}"]["count_activity"],
                )
            with header_right:
                claan_img = pathlib.Path(
                    f"./assets/images/{self.claan.name.lower()}_hex.png"
                )
                if claan_img.exists():
                    st.image(str(claan_img))

        st.divider()

        # =-- SUBMISSION --= #

        col_quest, col_activity = st.columns(2)

        with col_quest:
            with st.form(key="form_submit_quest"):
                st.header("Quests")

                st.selectbox(
                    label="Your name",
                    key="quest_user",
                    options=st.session_state[f"users_{self.claan.name}"],
                    format_func=lambda user: user.name,
                )

                st.radio(
                    label="Quests",
                    options=st.session_state["active_quest"],
                    format_func=lambda task: task.description,
                    key="quest_selection",
                )

                st.form_submit_button(
                    label="Submit",
                    on_click=data.submit_record,
                    kwargs={
                        "_session": Database.get_session(),
                        "task_type": TaskType.QUEST,
                    },
                )

        with col_activity:
            with st.form(key="form_activities"):
                st.header("Activities")

                st.selectbox(
                    label="Your name",
                    key="activity_user",
                    options=st.session_state[f"users_{self.claan.name}"],
                    format_func=lambda user: user.name,
                )

                st.radio(
                    label="Activities",
                    options=st.session_state["active_activity"],
                    format_func=lambda task: task.description,
                    key="activity_selection",
                )

                st.form_submit_button(
                    label="Submit",
                    on_click=data.submit_record,
                    kwargs={
                        "_session": Database.get_session(),
                        "task_type": TaskType.ACTIVITY,
                    },
                )
