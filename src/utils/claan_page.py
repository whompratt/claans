import pathlib

import pandas as pd
import streamlit as st

from src.models.claan import Claan
from src.models.market.portfolio import BoardVote
from src.utils import data, stock_game
from src.utils.database import Database


class ClaanPage:
    def __init__(self, claan: Claan) -> None:
        self.claan = claan

        st.set_page_config(
            page_title=claan.value,
            page_icon=self.claan.get_icon(),
            layout="wide",
        )

        st.markdown(
            """<style>
            .st-emotion-cache-15zws4i, .st-emotion-cache-1j7f08p, .st-emotion-cache-1j34uyg, .st-bm {
                color: #F5F5F5
            }
            </style>""",
            unsafe_allow_html=True,
        )

        with Database.get_session() as session:
            if "active_tasks" not in st.session_state:
                st.session_state["active_tasks"] = data.get_active_tasks(
                    _session=session
                )
            st.write(f"Active tasks: {len(st.session_state["active_tasks"])}")
            if f"users_{self.claan.name}" not in st.session_state:
                st.session_state[f"users_{self.claan.name}"] = data.get_claan_users(
                    _session=session, claan=self.claan
                )
            if f"portfolios_{self.claan.name}" not in st.session_state:
                st.session_state[f"portfolios_{self.claan.name}"] = {
                    user.id: data.get_portfolio(session, user)
                    for user in st.session_state[f"users_{self.claan.name}"]
                }
            if "scores" not in st.session_state:
                st.session_state["scores"] = data.get_scores(_session=session)
            if f"data_{self.claan.name}" not in st.session_state:
                st.session_state[f"data_{self.claan.name}"] = (
                    stock_game.get_corporate_data(_session=session, claan=self.claan)
                )
            if f"historical_{self.claan.name}" not in st.session_state:
                st.session_state[f"historical_{self.claan.name}"] = (
                    data.get_historical_data(_session=session, claan=self.claan)
                )
            if "fortnight_info" not in st.session_state:
                st.session_state["fortnight_info"] = data.get_fortnight_info(
                    _session=session
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
                    f"Welcome to the {self.claan.value} Claan Area! Here you can log tasks!"
                )
                st.subheader("Fortnight Breakdown!")

                col_1, col_2, col_3, col_4 = st.columns(4)
                with col_1:
                    st.metric(
                        label="Banked Funds",
                        value=f"${float(st.session_state[f"data_{self.claan.name}"]["funds"] or 0.0)}",
                    )
                    st.metric(
                        label="Fortnight Number",
                        value=st.session_state["fortnight_info"].get(
                            "fortnight_number"
                        ),
                    )
                with col_2:
                    st.metric(
                        "In Escrow",
                        value=f"${float(st.session_state[f"data_{self.claan.name}"]["escrow"] or 0.0)}",
                    )
                    st.metric(
                        label="Started",
                        value=str(st.session_state["fortnight_info"].get("start_date")),
                    )
                with col_3:
                    st.metric(
                        "Tasks Completed",
                        value=st.session_state[f"data_{self.claan.name}"]["task_count"],
                    )
                    st.metric(
                        label="Ends",
                        value=str(st.session_state["fortnight_info"].get("end_date")),
                    )
            with header_right:
                claan_img = pathlib.Path(
                    f"./assets/images/{self.claan.name.lower()}_hex.png"
                )
                if claan_img.exists():
                    st.image(str(claan_img))

        st.divider()

        # =-- SUBMISSION --= #

        with st.container(border=True):
            user = st.selectbox(
                label="Your name",
                key="task_user",
                options=st.session_state[f"users_{self.claan.name}"],
                format_func=lambda user: user.name,
            )

            col_task, col_portfolio = st.columns(2)
            with col_task:
                with st.form(key="form_submit_task"):
                    st.header("Tasks")

                    st.radio(
                        label="Tasks",
                        options=st.session_state["active_tasks"],
                        format_func=lambda task: f"${task.reward.value}: {task.description}",
                        key="task_selection",
                    )

                    st.form_submit_button(
                        label="Submit",
                        on_click=data.submit_record,
                        kwargs={
                            "_session": Database.get_session(),
                        },
                    )

            with col_portfolio:
                st.session_state["portfolio"] = portfolio = st.session_state[
                    f"portfolios_{self.claan.name}"
                ][user.id]
                with st.form(key="form_activities"):
                    st.header("Wallet")
                    st.metric(
                        label="Wallet Cash", value=f"${round(portfolio.cash or 0.0, 2)}"
                    )
                    st.radio(
                        label="Board Vote",
                        key="portfolio_vote",
                        options=list(BoardVote),
                        format_func=lambda vote_type: vote_type.name.title(),
                    )
                    st.form_submit_button(
                        label="Update Vote",
                        on_click=data.update_vote,
                        kwargs={
                            "_session": Database.get_session(),
                            "_portfolio": portfolio,
                        },
                    )

        with st.expander("Record History"):
            if st.button(
                label="Refresh",
                key="history_button_refresh",
                help="Click to refresh historical data",
            ):
                data.get_historical_data.clear(claan=self.claan)
                st.session_state[f"historical_{self.claan.name}"] = (
                    data.get_historical_data(
                        _session=Database.get_session(), claan=self.claan
                    )
                )

            df_historical = pd.DataFrame.from_records(
                columns=("Name", "Task", "Dice", "Score", "Timestamp"),
                data=st.session_state[f"historical_{self.claan.name}"],
            )
            if "_sa_instance_state" in df_historical.columns:
                df_historical.drop("_sa_instance_state", inplace=True, axis=1)
            if "Dice" in df_historical.columns:
                df_historical["Dice"] = df_historical["Dice"].apply(lambda x: x.name)

            st.dataframe(
                data=df_historical,
                use_container_width=True,
                hide_index=True,
            )
