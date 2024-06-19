import json
import pathlib

import streamlit as st

from utils.claans import Claans
from utils.database import Database
from utils.record import RecordSchema
from utils.user import UserSchema


class ClaanPage:
    with open("./settings.json") as settings_file:
        settings = json.load(settings_file)

    def __init__(self, claan: Claans) -> None:
        self.claan = claan

        st.set_page_config(
            page_title=claan.value,
            page_icon=self.claan.get_icon(),
            layout="wide",
        )

        if "scores" not in st.session_state:
            scores = Database.get_documents(collection="scores")
            st.session_state["scores"] = scores
        if "quest_log" not in st.session_state:
            quest_log = Database.get_documents(collection="quest_log")
            st.session_state["quest_log"] = RecordSchema().load(quest_log, many=True)
        if "users" not in st.session_state:
            users = Database.get_documents(collection="users")
            st.session_state["users"] = UserSchema().load(users, many=True)
        if f"users_{self.claan.name}" not in st.session_state:
            this_claan_users = Database.get_documents(
                collection="users", filter={"user_claan": self.claan.name}
            )
            st.session_state[f"users_{self.claan.name}"] = UserSchema().load(
                this_claan_users, many=True
            )

        self.build_claan_page()

    def check_password(self):
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

    def build_claan_page(self):
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
                    "Overall Score",
                    next(
                        document["score"]
                        for document in st.session_state["scores"]
                        if document["claan"] == self.claan.name
                    ),
                )
                col_2.metric("Fortnight Score", 0)
                col_3.metric("Quests Completed", 0)
                col_4.metric("Activities Completed", 0)
            with header_right:
                st.image(
                    str(
                        pathlib.Path(
                            f"./assets/images/{self.claan.name.lower()}_hex.png"
                        )
                    )
                )

        st.divider()

        # =-- SUBMISSION --= #

        col_quest, col_activity = st.columns(2)

        with col_quest:
            with st.form(key="form_submit_quest"):
                st.header("Quests")

                st.selectbox(
                    label="Your name",
                    key="user_name",
                    options=st.session_state[f"users_{self.claan.name}"],
                    format_func=lambda user: user.get("user_name"),
                )

                st.form_submit_button("Submit")

        with col_activity:
            with st.form(key="form_activities"):
                st.header("Activities")
                st.form_submit_button("Submit")
