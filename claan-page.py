import pathlib

import streamlit as st

from claans import Claans
from database import Database


class ClaanPage:
    def __init__(self, claan: Claans) -> None:
        self.claan = claan

        st.session_state["scores"] = Database.get_scores()
        st.set_page_config(
            page_title=claan.value,
            page_icon=self.claan.get_icon(),
            layout="wide",
        )
        self.build_claan_page()

    def check_password(self):
        def password_entered():
            if st.session_state["password"] == st.secrets["passwords"][self.claan.name]:
                st.session_state[f"{self.claan.name}_password_correct"] = True
                del st.session_state["password"]
            else:
                st.session_state[f"{self.claan.name}_password_correct"] = False

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
                col_1.metric("Overall Score", sum(st.session_state.get("scores")))
                col_2.metric("Fortnight Score", 0)
                col_2.metric("Quests Completed", 0)
                col_3.metric("Activities Completed", 0)
            with header_right:
                st.image(str(pathlib.Path(f"{self.claan.name.lower()}_hex.png")))
