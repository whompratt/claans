import logging
import os
import requests
import streamlit as st
from pathlib import Path
from PIL import Image
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
from streamlit_lottie import st_lottie

# Set the page title and icon and set layout to "wide" to minimise margains
st.set_page_config(page_title="Claan ChAAos", page_icon=":dragon:")


if "home_db" not in st.session_state:
    mongo_user = st.secrets["MONGO_USER"]
    mongo_pass = st.secrets["MONGO_PASS"]
    uri = f"mongodb+srv://{mongo_user}:{mongo_pass}@claanapp.l2vlfwo.mongodb.net/?retryWrites=true&w=majority"
    # Create a new client and connect to the server
    client = MongoClient(uri, server_api=ServerApi('1'))
    # Send a ping to confirm a successful connection
    try:
        client.admin.command('ping')
        print("Pinged your deployment. You successfully connected to MongoDB!")
    except Exception as e:
        print(e)

    # Set the database and collection
    st.session_state.home_db = client["Claan_app"]
    st.session_state.home_col = st.session_state.home_db["scores2"]

# Get relative path
img_path = Path(__file__).parents[0]
# Load images
logo_img = Image.open(f"{img_path}/Images/Logo.png")
earth_img = Image.open(f"{img_path}/pages/Page_Images/Earth-striders-hex.png")
fire_img = Image.open(f"{img_path}/pages/Page_Images/Flame-dancers-hex.png")
thunder_img = Image.open(f"{img_path}/pages/Page_Images/Thunder-walkers-hex.png")
wave_img = Image.open(f"{img_path}/pages/Page_Images/Wave-riders-hex.png")


def main():
    # Header section
    with st.container():
        # Create columns
        head_l, head_r = st.columns((2.5,1))

        with head_l:
            # Add a subheader
            st.subheader("Advancing Analytics")
            # Add a title
            st.title("Season 3 - Claan Caalm")

        with head_r:
            # Add logo
            st.image(logo_img)

        # Add description
        st.write("Welcome to seasion 4 of Claans at Advancing Analytics. This time around things are taking a more relaxed turn but retaining a healthy dose of that Claans flair!")
        st.write("Using the Claan Portal you can see the scores as they stand, see this fortnights quests, and access the Claan area log quests, steps and activities!")

        # Add spacer
        st.write("---")

    # Add section for Claan scores
    with st.container():
        # Add title
        st.header("Scores")

        # Load the scores for all claans
        scores = [i for i in st.session_state.home_col.find()]

        # Create column for each claan
        col1, col2, col3, col4 = st.columns((1,1,1,1))

        # Add content to first column
        with col1:
            # Add the claan image
            st.image(earth_img)
            # Get scores for the claan, using the sum of the scores, and the last entry as the delta
            earth_scores = [i['Score'] for i in scores if (i['Claan']=="Earth Striders")]
            print(earth_scores)
            # Add metric for claan score
            st.metric(label="Earth Striders", value=sum(earth_scores), delta=earth_scores[-1])

        # Add content to second column
        with col2:
            # Add the claan image
            st.image(fire_img)
            # Get scores for the claan
            fire_scores = [i['Score'] for i in scores if (i['Claan']=="Fire Dancers")]
            # Add metric for claan score, using the sum of the scores, and the last entry as the delta
            st.metric(label="Fire Dancers", value=sum(fire_scores), delta=fire_scores[-1])

        # Add content to third column
        with col3:
            # Add the claan image
            st.image(thunder_img)
            # Get scores for the claan
            thunder_scores = [i['Score'] for i in scores if (i['Claan']=="Thunder Walkers")]
            # Add metric for claan score, using the sum of the scores, and the last entry as the delta
            st.metric(label="Thunder Walkers", value=sum(thunder_scores), delta=thunder_scores[-1])

        # Add content to last column
        with col4:
            # Add the claan image
            st.image(wave_img)
            # Get scores for the claan
            wave_scores = [i['Score'] for i in scores if (i['Claan']=="Wave Riders")]
            # Add metric for claan score, using the sum of the scores, and the last entry as the delta
            st.metric(label="Wave Riders", value=sum(wave_scores), delta=wave_scores[-1])

        # Add spacer
        st.write("---")

    # Add section for changes
    with st.container():
        st.title("How it works!")
        st.write("Claans and the Claan competition are here as a tool to encourage a healthy work life balance, and to promote practicing self care! Plus it is a great opportunity to socialise and cooperate with others in the company who aren't in your department and project teams!")
        st.subheader("Quests")
        st.write("Each fortnight there will be 5 quests for each member member of the Claan to complete. The reward for each quest will be a dice, ranging from D4 to D10 points. It will be automatically rolled and the result added to your Claan's score.")
        st.info("D4 - D10 Quests can now be completed daily!")
        st.info("The D12 quest will always be a Claan Challenge, it is generally completed as a team and can only completed once per person")
        st.subheader("Steps")
        st.write("Step counting is back, and this time it is simple! If you complete 10,000 steps or more in a day, you can log it in the portal and claim yourself D4 points!")
        st.subheader("Activities")
        st.write("Activities are also back! Each week different activities will be incentivised but by default 45 minutes of indoor exercise will net you D6 points, 45 minutes of outdoor exercise will net you D8 points, and participating in a team sport will net you D10 points!")
        st.info("All activities can be logged daily too!")


if __name__ == "__main__":
    main()