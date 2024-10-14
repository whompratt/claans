import pathlib

import streamlit as st

from src.models.claan import Claan
from src.utils.data.scores import get_scores
from src.utils.data.stocks import get_corporate_data
from src.utils.database import Database


def init_page() -> None:
    st.set_page_config(page_title="Claans Corporate Claash", page_icon=":dragon:")

    st.markdown(
        """<style>
        .st-emotion-cache-15zws4i, .st-emotion-cache-1j7f08p {
            color: #F5F5F5
        }
        </style>""",
        unsafe_allow_html=True,
    )

    with Database.get_session() as session:
        if "scores" not in st.session_state:
            st.session_state["scores"] = get_scores(_session=session)
        for claan in Claan:
            if f"data_{claan.name}" not in st.session_state:
                st.session_state[f"data_{claan.name}"] = get_corporate_data(
                    _session=session, claan=claan
                )
        session.expunge_all()

    # --- HEADER --- #
    with st.container():
        col_header, col_logo = st.columns((3, 0.8))

        with col_logo:
            path_img_logo = pathlib.Path("./assets/images/logo.png")
            if path_img_logo.exists():
                st.image(str(path_img_logo))
        with col_header:
            st.header("Advancing Analytics")
            st.subheader("Season 5 - Corporate Claash")
    # --- HEADER ---#

    st.divider()

    # --- SCORES --- #
    with st.container():
        st.header("Scores")

        cols = zip(Claan, st.columns(len(Claan)))
        for claan, col in cols:
            with col:
                claan_img = pathlib.Path(f"./assets/images/{claan.name.lower()}.png")
                if claan_img.exists():
                    st.image(str(claan_img))

                st.metric(
                    label="Share Price",
                    value=f"${float(st.session_state[f"data_{claan.name}"]["instrument"] or 0.0)}",
                )
                st.metric(
                    label="Stash",
                    value=f"${float(st.session_state[f"data_{claan.name}"]["funds"] or 0.0)}",
                )
                st.metric(
                    label="Escrow",
                    value=f"${float(st.session_state[f"data_{claan.name}"]["escrow"] or 0.0)}",
                )
    # --- SCORES --- #

    st.divider()

    # --- INFO --- #
    with st.container():
        st.header("Claans - Corporate Claash")
        st.subheader("Welcome")
        st.write(
            """
Welcome to Season 5 of Claans, 'Corporate Claash', where this time we'll be fighting for financial dominance!
            """
        )

        st.divider()

        st.subheader("How it Works")
        st.write(
            """
Every Claan is a corporation, and Claan Members are Board Members.
\nEvery time you complete a quest you are given a reward which is then locked up in escrow.
\nAt the end of each fortnight, Board Member votes will be tallied to decide whether those funds should go straight into the Claan's Stash, or divided amongst the shareholders.
\nClaans that pay out enough money will see their share price increase, but those that withold will instead see it drop.
            """
        )

        st.divider()

        st.subheader("Claan Stock Market")
        st.write(
            """
Each Claan has been issues 50 shares initially, with 2 shares given to each Board Member, however, the Claan hasn't gone public yet!
\nAs Claans reach a value threshold, they will become publicly listed and their shares will be available to purchase.
\nBeware though! Initially all of a Claan's shares will be in IPO, and any funds that these shares would pay out are instead paid into the Claan stash!
\n\nAs shares are bought, they will first come out of the IPO and enter the market.
\nAs shares are sold, though, they instead go to the Bank, and any dividends these would pay are lost, so be careful!
            """
        )
    # --- INFO --- #

    # --- FAQ --- #
    st.divider()
    with st.container():
        st.header("FAQ")

        st.subheader("What happens if we vote 'Withold'?")
        st.write(
            "If a Claan votes to withold funds, then all money in escrow will go straight into the Stash, but shareholders won't receive any more and the share price will decrease."
        )

        st.subheader("What happens if we vote 'Payout'?")
        st.write(
            "If a Claan votes to payout funds, then all money in escrow will be divided and distributed amongst all shareholders, and if the money paid out is high enough, then share price will increase."
        )

        st.subheader("What does it means if shares are in IPO?")
        st.write(
            "Shares in IPO are owned by the Claan, so if the Claan votes to pay out, then dividends will be paid into the Claan's stash."
        )
    # --- FAQ --- #


def main() -> None:
    init_page()


if __name__ == "__main__":
    main()
