import pandas as pd
import streamlit as st

from .database import Database


class Debug:
    def __init__(self):
        if "scores" not in st.session_state:
            st.session_state["scores"] = Database.get_documents(collection="scores")
        if "quest_log" not in st.session_state:
            st.session_state["quest_log"] = Database.get_documents(
                collection="quest_log"
            )
        if "users" not in st.session_state:
            st.session_state["users"] = Database.get_documents(collection="users")
        self.build_debug_interface()

    def build_debug_interface(self):
        with st.container(border=True):
            st.info("DEBUG MODE")

            with st.container(border=True):
                st.header("Scores, Quests, and Activities")

                col_1, col_2, col_3 = st.columns(3)
                # col_1.button(
                #     label="Purge",
                #     help="This will remove _all_ records from the quests collection, use with care",
                #     on_click=Database.purge,
                #     key="button_purge",
                #     use_container_width=True,
                # )
                # col_2.button(
                #     label="Random Quest",
                #     help="This will create and submit a new random entry to the quest log",
                #     on_click=Database.submit_quest_random,
                #     key="button_submit_random",
                #     use_container_width=True,
                # )
                # col_3.button(
                #     label="Random User",
                #     help="This will create and submit a new random user to the users collection",
                #     on_click=Database.submit_user_random,
                #     key="button_users_random",
                #     use_container_width=True,
                # )

                st.dataframe(
                    data=pd.DataFrame.from_dict(st.session_state.get("scores")),
                    use_container_width=True,
                    hide_index=True,
                    column_config={"_id": None},
                )

                st.dataframe(
                    data=pd.DataFrame.from_records(st.session_state.get("quest_log")),
                    use_container_width=True,
                    hide_index=True,
                    column_config={"_id": None},
                )

            with st.container(border=True):
                st.header("Users")

                # with st.form(key="create_new_user", clear_on_submit=True, border=True):
                #     st.subheader("New User")
                #     st.text_input(
                #         label="User name", key="user_name", placeholder="John Doe"
                #     )
                #     st.selectbox(
                #         label="Claan",
                #         key="user_claan",
                #         options=Claans,
                #         format_func=lambda claan: claan.value,
                #     )
                #     st.form_submit_button(
                #         label="Create User",
                #         on_click=Database.submit_user,
                #     )

                st.dataframe(
                    data=pd.DataFrame.from_records(st.session_state.get("users")),
                    use_container_width=True,
                    hide_index=True,
                )
