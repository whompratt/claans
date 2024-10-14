import pathlib

import pandas as pd
import streamlit as st

from src.models.claan import Claan
from src.models.market.portfolio import BoardVote
from src.utils.data.scores import get_historical_data, get_scores, submit_record
from src.utils.data.seasons import get_fortnight_info
from src.utils.data.stocks import (
    get_corporate_data,
    get_ipo_count,
    get_portfolio,
    get_shares,
    update_vote,
)
from src.utils.data.tasks import get_active_tasks
from src.utils.data.users import get_claan_users
from src.utils.database import Database
from src.utils.logger import LOGGER


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
                LOGGER.info("Loading `active_tasks`")
                st.session_state["active_tasks"] = get_active_tasks(_session=session)
            if f"users_{self.claan.name}" not in st.session_state:
                st.session_state[f"users_{self.claan.name}"] = get_claan_users(
                    _session=session, claan=self.claan
                )
            if f"portfolios_{self.claan.name}" not in st.session_state:
                LOGGER.info(f"Loading `portfolios_{self.claan.name}`")
                st.session_state[f"portfolios_{self.claan.name}"] = {
                    user.id: get_portfolio(session, user_id=user.id)
                    for user in st.session_state[f"users_{self.claan.name}"]
                }
            if f"shares_{self.claan.name}" not in st.session_state:
                LOGGER.info(f"Loading `shares_{self.claan.name}`")
                st.session_state[f"shares_{self.claan.name}"] = {
                    portfolio.id: get_shares(session, portfolio.id)
                    for _, portfolio in st.session_state[
                        f"portfolios_{self.claan.name}"
                    ].items()
                }
            if f"ipo_{self.claan.name}" not in st.session_state:
                LOGGER.info(f"Loading `ipo_{self.claan.name}`")
                st.session_state[f"ipo_{self.claan.name}"] = get_ipo_count(
                    session, self.claan
                )
            if "scores" not in st.session_state:
                LOGGER.info("Loading `scores`")
                st.session_state["scores"] = get_scores(_session=session)
            if f"data_{self.claan.name}" not in st.session_state:
                LOGGER.info(f"Loading `data_{self.claan.name}`")
                st.session_state[f"data_{self.claan.name}"] = get_corporate_data(
                    _session=session, claan=self.claan
                )
            if f"historical_{self.claan.name}" not in st.session_state:
                LOGGER.info(f"Loading `historical_{self.claan.name}`")
                st.session_state[f"historical_{self.claan.name}"] = get_historical_data(
                    _session=session, claan=self.claan
                )
            if "fortnight_info" not in st.session_state:
                LOGGER.info("Loading `fortnight_info`")
                st.session_state["fortnight_info"] = get_fortnight_info(
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
                with col_4:
                    st.metric(
                        "Share in IPO", value=st.session_state[f"ipo_{self.claan.name}"]
                    )
            with header_right:
                claan_img = pathlib.Path(
                    f"./assets/images/{self.claan.name.lower()}.png"
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
                        on_click=submit_record,
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
                    st.metric(
                        label="Current Vote", value=portfolio.board_vote.name.title()
                    )
                    st.radio(
                        label="Board Vote",
                        key="portfolio_vote",
                        options=list(BoardVote),
                        format_func=lambda vote_type: vote_type.name.title(),
                        index=list(BoardVote).index(portfolio.board_vote),
                    )
                    st.form_submit_button(
                        label="Update Vote",
                        on_click=update_vote,
                        kwargs={
                            "_session": Database.get_session(),
                            "_portfolio": portfolio,
                            "_claan": self.claan,
                        },
                    )
                    df_shares = pd.DataFrame.from_records(
                        data=st.session_state[f"shares_{self.claan.name}"][portfolio.id]
                    )
                    if "_sa_instance_state" in df_shares.columns:
                        df_shares.drop("_sa_instance_state", inplace=True, axis=1)
                    if "claan" in df_shares.columns:
                        df_shares["claan"] = df_shares["claan"].apply(lambda x: x.value)
                    st.dataframe(
                        data=df_shares, use_container_width=True, hide_index=True
                    )

        with st.expander("Record History"):
            if st.button(
                label="Refresh",
                key="history_button_refresh",
                help="Click to refresh historical data",
            ):
                get_historical_data.clear(claan=self.claan)
                st.session_state[f"historical_{self.claan.name}"] = get_historical_data(
                    _session=Database.get_session(), claan=self.claan
                )

            df_historical = pd.DataFrame.from_records(
                columns=("Name", "Task", "Reward", "Timestamp"),
                data=st.session_state[f"historical_{self.claan.name}"],
            )
            if "_sa_instance_state" in df_historical.columns:
                df_historical.drop("_sa_instance_state", inplace=True, axis=1)
            if "Reward" in df_historical.columns:
                df_historical["Reward"] = df_historical["Reward"].apply(
                    lambda x: f"${x}"
                )

            st.dataframe(
                data=df_historical,
                use_container_width=True,
                hide_index=True,
            )
