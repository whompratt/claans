import pandas as pd
import streamlit as st

from database import Database


class Debug:
    def __init__(self):
        if "scores" not in st.session_state:
            st.session_state["scores"] = Database.get_scores()
        if "quests" not in st.session_state:
            st.session_state["quests"] = Database.get_quests()

        self.build_debug_interface()

    def build_debug_interface(self):
        with st.container(border=True):
            st.info("DEBUG MODE")
            tab_scores, tab_quests = st.tabs(["Scores", "Quests"])

            with tab_scores:
                with st.container(border=True):
                    st.header("Database Tools")

                    col_1, col_2, col_3 = st.columns(3)
                    col_1.button(
                        label="Purge",
                        help="This will remove _all_ records from the scores collection, use with care",
                        on_click=Database.purge_scores,
                        key="purge_scores",
                    )
                    col_2.button(
                        label="Populate",
                        help="This will repopulate the scores collection, replacing any missing claans",
                        on_click=Database.populate_scores,
                        key="populate_scores",
                    )
                    col_3.button(
                        label="Randomize",
                        help="This will randomize claan scores, overwriting existing values.",
                        on_click=Database.randomize_scores,
                        key="randomize_scores",
                    )

                    st.table(
                        pd.DataFrame.from_dict(
                            st.session_state.get("scores"), orient="index"
                        )
                    )

            with tab_quests:
                with st.container(border=True):
                    st.header("Database Tools")

                    col_1, col_2, col_3 = st.columns(3)
                    col_1.button(
                        label="Purge",
                        help="This will remove _all_ records from the quests collection, use with care",
                        on_click=Database.purge_quests,
                        key="purge_quests",
                    )
                    col_2.button(
                        label="Generate Randomg Entry",
                        help="This will creating and submit a new random entry to the quest log.",
                        on_click=Database.randomize_quests,
                        key="randomize_quests",
                    )
                    # col_2.button(
                    #     label="Populate",
                    #     help="This will repopulate the scores collection, replacing any missing claans",
                    #     on_click=Database.populate_scores,
                    # )
                    # col_3.button(
                    #     label="Randomize",
                    #     help="This will randomize claan scores, overwriting existing values.",
                    #     on_click=Database.randomize_scores,
                    # )

                    st.table(
                        pd.DataFrame.from_dict(
                            st.session_state.get("quests"), orient="index"
                        )
                    )
