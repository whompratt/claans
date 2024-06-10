import pathlib

import streamlit as st

from utils.claans import Claans
from utils.database import Database
from utils.debug import Debug

# Set the page title and icon and set layout to "wide" to minimise margains
st.set_page_config(page_title="Claan ChAAos", page_icon=":dragon:")


def init_page() -> None:
    if "scores" not in st.session_state:
        st.session_state["scores"] = Database.get_scores()
    if "quest_log" not in st.session_state:
        st.session_state["quest_log"] = Database.get_quest_log

    # --- HEADER --- #
    with st.container():
        col_header, col_logo = st.columns((3, 0.8))

        with col_logo:
            path_img_logo = pathlib.Path("./assets/images/logo.png")
            if path_img_logo.exists():
                st.image(str(path_img_logo))
        with col_header:
            st.header("Advancing Analytics")
            st.subheader("Season 4 - Claan Calm")

        st.header("Welcome")
        st.write(
            "Welcome to season 4 of Claans at Advancing Analytics. This time around things are taking a more relaxed turn, but we're retaining a healthy dose of that Claans flair!"
        )
        st.write(
            "Using the Claan Portal you can see the scores as they currently stand, this fortnights quests, and also access the Claan area to log quests, steps, and activities!"
        )
    # --- HEADER ---#

    st.divider()

    # --- SCORES --- #
    with st.container():
        st.header("Scores")

        cols = zip(Claans, st.columns(len(Claans)))
        for claan, col in cols:
            with col:
                st.image(
                    str(pathlib.Path(f"./assets/images/{claan.name.lower()}_hex.png"))
                )
                st.metric(
                    label=claan.value,
                    value=next(
                        document["score"]
                        for document in st.session_state["scores"]
                        if document["claan"] == claan.name
                    ),
                )
    # --- SCORES --- #

    st.divider()

    # --- INFO --- #
    with st.container():
        st.header("How It Works")
        st.write(
            "Claans and the Claan Competition exist to encourage a healthy work-life balance, promote practising self-care, and facilitate socialisation and cooperation within Advancing Analytics."
        )
        st.write(
            "Every fortnight, a new set of quests and activities can be completed to get points for your Claan, and as everyone knows, 'Points Mean Prizes', so make sure to get those points logged!"
        )

        st.subheader("Quests")
        st.write(
            "Quests are the first way you can earn points for your Claan. Every fortnight, a set of 5 quests will be made available for completion."
        )
        st.write(
            "Each quest will offer a dice as a reward, with the number of sides on the dice corresponding to the quest difficulty."
        )
        st.write(
            "After completing a quest, the dice is automatically rolled and the result is added to your Claan's score."
        )
        st.write(
            "D4-D10: quests with a reward between D4 and D10 can be completed _daily_, meaning there are a lot of points available!"
        )
        st.write(
            "D12: quests with a reward of D12 are considered a 'Claan Challenge', and can only be submitted once per person per fortnight."
        )

        st.subheader("Steps")
        st.write(
            "Steps are back! If you complete 10,000 or more steps in a day, then you can submit that quest and get a D4!"
        )

        st.subheader("Activities")
        st.write(
            "Activites are back too! Every day you can earn points for being active, with a D6, D8, and D10 available for 45 minutes of indoor, outdoor, or team sport participation respectively."
        )
        st.write(
            "The nature of these activities will change on a regular basis, to keep things fresh and interesting."
        )
    # --- INFO --- #


def main() -> None:
    if st.secrets.env.get("debug"):
        Debug()

    init_page()


if __name__ == "__main__":
    main()
