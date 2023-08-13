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

def load_assets(url: str) -> dict:
    """Function load asset from a http get request

    Args:
        url (str): URL of the asset to load

    Returns:
        dict: Dictionary to be rendered into a lottie gif.
    """
    asset = requests.get(url)
    if asset.status_code != 200:
        logging.error("Failed to load asset")
        return None

    else:
        logging.info("Asset loaded successfully")
        return asset.json()

# mongo_user = st.secrets["MONGO_USER"]
# mongo_pass = st.secrets["MONGO_PASS"]
# uri = f"mongodb+srv://{mongo_user}:{mongo_pass}@attendeedb.wbslhme.mongodb.net/?retryWrites=true&w=majority"
# # Create a new client and connect to the server
# client = MongoClient(uri, server_api=ServerApi('1'))
# # Send a ping to confirm a successful connection
# try:
#     client.admin.command('ping')
#     print("Pinged your deployment. You successfully connected to MongoDB!")
# except Exception as e:
#     print(e)

# db = client[""]
# col = db[""]

# Load assets
lottie_fire = load_assets("https://assets8.lottiefiles.com/packages/lf20_uu7qI3.json")

img_path = Path(__file__).parents[0]
logo_img = Image.open(f"{img_path}/Images/Logo.png")
claans_img = Image.open(f"{img_path}/Images/Combined_Hex.png")


# Header section
with st.container():
    # Create columns
    head_l, head_r = st.columns((2.5,1))

    with head_l:
        # Add a subheader
        st.subheader("Advancing Analytics")
        # Add a title
        st.title("Season 3 - Claan ChAAos")

    with head_r:
        # Add logo
        st.image(logo_img)

    st.write("Welcome to seasion 3 of Claans at Advancing Analytics. This time around things have been shaken up and injected with a healthy dose of D&D flair!")
    st.write("Using the Claan Portal you can see the scores as they stand, see this fortnights challenges and activities, and access the Claan area to see your upgrades and dice pool!")

    # Add spacer
    st.write("---")

# Add section for Claan scores
with st.container():
    # Add title
    st.header("Scores")
    # Add Claan Logo
    st.image(claans_img)

    # Create column for each claan
    col1, col2, col3, col4 = st.columns((1,1,1,1))

    # Add metrics with the score for each claan
    with col1:
        st.metric(label="Earth Striders", value=0, delta=0)
    with col2:
        st.metric(label="Fire Dancers", value=0, delta=0)
    with col3:
        st.metric(label="Thunder Walkers", value=0, delta=0)
    with col4:
        st.metric(label="Wave Riders", value=0, delta=0)

    # Add spacer
    st.write("---")

# Add a section for the weekly challenges
with st.container():
    # Add title
    st.header("Challenges and Activities")

    st.write("Check back once the season begins for the challenges and activities!")

    # Add spacer
    st.write("---")

# Footer section
with st.container():
    st.write("""
    **Author**: Alex.B, :wave: [LinkedIn](https://www.linkedin.com/in/alexander-billington-29488b118/) 
    :books: [Github](https://github.com/IoT-Gardener) :computer: [Website](https://abmlops.streamlit.app)
    """)