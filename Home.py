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

db = client["Claan_app"]
col = db["scores"]

# Get relative path
img_path = Path(__file__).parents[0]
# Load images
logo_img = Image.open(f"{img_path}/Images/Logo.png")
earth_img = Image.open(f"{img_path}/pages/Page_Images/Earth-striders-hex.png")
fire_img = Image.open(f"{img_path}/pages/Page_Images/Flame-dancers-hex.png")
thunder_img = Image.open(f"{img_path}/pages/Page_Images/Thunder-walkers-hex.png")
wave_img = Image.open(f"{img_path}/pages/Page_Images/Wave-riders-hex.png")

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

    # Load the scores for all claans
    scores = [i for i in col.find()]

    # Create column for each claan
    col1, col2, col3, col4 = st.columns((1,1,1,1))

    # Add content to first column
    with col1:
        # Add the claan image
        st.image(earth_img)
        # Get scores for the claan
        earth_scores = [i['Score'] for i in scores if (i['Claan']=="earth striders")]
        # Add metric for claan score
        st.metric(label="Earth Striders", value=sum(earth_scores), delta=earth_scores[-1])

    # Add content to second column
    with col2:
        # Add the claan image
        st.image(fire_img)
        # Get scores for the claan
        fire_scores = [i['Score'] for i in scores if (i['Claan']=="fire dancers")]
        # Add metric for claan score
        st.metric(label="Fire Dancers", value=sum(fire_scores), delta=fire_scores[-1])

    # Add content to third column
    with col3:
        # Add the claan image
        st.image(thunder_img)
        # Get scores for the claan
        thunder_scores = [i['Score'] for i in scores if (i['Claan']=="thunder walkers")]
        # Add metric for claan score
        st.metric(label="Thunder Walkers", value=sum(thunder_scores), delta=thunder_scores[-1])

    # Add content to last column
    with col4:
        # Add the claan image
        st.image(wave_img)
        # Get scores for the claan
        wave_scores = [i['Score'] for i in scores if (i['Claan']=="wave riders")]
        # Add metric for claan score
        st.metric(label="Wave Riders", value=sum(wave_scores), delta=wave_scores[-1])

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