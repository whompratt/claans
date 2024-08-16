import pathlib

import streamlit as st

from src.models.claan import Claan
from src.models.record import Record
from src.models.user import User
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
            if "active_quests" not in st.session_state:
                st.session_state["active_quests"] = Database.get_active_quests(
                    _session=session
                )
            if "active_activities" not in st.session_state:
                st.session_state["active_activities"] = Database.get_active_activities(
                    _session=session
                )
            if f"users_{self.claan.name}" not in st.session_state:
                st.session_state[f"users_{self.claan.name}"] = Database.get_rows(
                    model=User, filter={"claan": self.claan}, _session=session
                )
            if "scores" not in st.session_state or True:
                st.session_state["scores"] = Record.get_claan_scores(_session=session)
            session.expunge_all()

        self.build_page()

    def submit_quest(self):
        task = st.session_state["quest_selection"]
        user = st.session_state["quest_user"]
        result = Database.submit_record(task=task, user=user)
        if not result:
            st.warning(
                "Error submitting quest, it looks like you've already submitted this quest..."
            )
        else:
            st.success("Quest submitted!")

    def submit_activity(self):
        task = st.session_state["activity_selection"]
        user = st.session_state["activity_user"]
        result = Database.submit_record(task=task, user=user)
        if not result:
            st.warning(
                "Error submitting activity, it looks like you've already submitted this activity..."
            )
        else:
            st.success("Activity submitted!")

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
                    value=next(
                        score
                        for claan, score in st.session_state["scores"].items()
                        if claan == self.claan
                    ),
                )
                col_2.metric("Fortnight Score", 0)
                col_3.metric("Tasks Completed", 0)
                col_4.metric("Activities Completed", 0)
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
                    options=st.session_state["active_quests"],
                    format_func=lambda task: task.description,
                    key="quest_selection",
                )

                st.form_submit_button(label="Submit", on_click=self.submit_quest)

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
                    options=st.session_state["active_activities"],
                    format_func=lambda task: task.description,
                    key="activity_selection",
                )

                st.form_submit_button(label="Sumit", on_click=self.submit_activity)
