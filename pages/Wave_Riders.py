import datetime
import json
import numpy as np
import streamlit as st
from pathlib import Path
from PIL import Image
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi

def check_password():
    """Returns `True` if the user had the correct password."""
    def password_entered():
        """Checks whether a password entered by the user is correct."""
        if st.session_state["password"] == st.secrets["wave_password"]:
            st.session_state["wave_password_correct"] = True
            del st.session_state["password"]  # don't store password
        else:
            st.session_state["wave_password_correct"] = False

    if "wave_password_correct" not in st.session_state:
        # First run, show input for password.
        st.text_input(
            "Password", type="password", on_change=password_entered, key="password"
        )
        return False

    elif not st.session_state["wave_password_correct"]:
        # Password not correct, show input + error.
        st.text_input(
            "Password", type="password", on_change=password_entered, key="password"
        )
        st.error("😕 Password incorrect")
        return False

    else:
        # Password correct.
        return True

# Get the secret mongo username and password
mongo_user = st.secrets["MONGO_USER"]
mongo_pass = st.secrets["MONGO_PASS"]
# Create the connection string
uri = f"mongodb+srv://{mongo_user}:{mongo_pass}@claanapp.l2vlfwo.mongodb.net/?retryWrites=true&w=majority"
# Create a new client and connect to the server
client = MongoClient(uri, server_api=ServerApi('1'))
# Send a ping to confirm a successful connection
try:
    client.admin.command('ping')
    print("Pinged your deployment. You successfully connected to MongoDB!")
except Exception as e:
    print(e)

# Set database and collection
db = client["Claan_app"]
col = db["wave_riders"]

# Load the assets for the app
img_path = Path(__file__).parents[0]
d4_img = Image.open(f"{img_path}/Page_Images/d4.png")
d6_img = Image.open(f"{img_path}/Page_Images/d6.png")
d8_img = Image.open(f"{img_path}/Page_Images/d8.png")
d10_img = Image.open(f"{img_path}/Page_Images/d10.png")
d12_img = Image.open(f"{img_path}/Page_Images/d12.png")
d20_img = Image.open(f"{img_path}/Page_Images/d20.png")
claan_img = Image.open(f"{img_path}/Page_Images/Wave-riders-hex.png")
sah = Image.open(f"{img_path}/Page_Images/Sparks_Arcane_Hourglass.png")
aso = Image.open(f"{img_path}/Page_Images/Azure_Sentinel_Ointment.png")

with open(f"{img_path}/settings.json") as fp:
    # Load the .json file of settings
    settings = json.load(fp)
    settings["Wave Riders"].sort()

# Set the page title and icon and set layout to "wide" to minimise margains
st.set_page_config(page_title="Wave Riders", page_icon=":ocean:")

if check_password():
    # Header section
    with st.container():
        # Create columns
        head_l, head_r = st.columns((2.5,1))

        with head_l:
            # Add a subheader
            st.subheader("Advancing Analytics")
            # Add a title
            st.title("Wave Riders")

        with head_r:
            # Add logo
            st.image(claan_img)

        st.write("Welcome to the Wave Rider Claan area! Here you can find all of the dice you have accumulated for the current fortnight, your magic items, and submit any quests that you have been working on!")
        st.write("---")


    with st.container():
        # Add a heading and a description
        st.header("Dice Pool")
        st.write("Here you can keep track of all of the dice you team have earned this fortnight!")

        # Get all submissions for current claan
        submissions = [i for i in col.find({"Date": {"$gte": datetime.datetime.strptime(settings['Fortnight Start Date'], ("%d/%m/%Y"))}}, { "_id": 0})]
        # Get unique members by using the set() operator on list of names
        contributors = list(set([i['Name'] for i in submissions])) 
        # Get dice step by getting the number of unique claan members who have submitted 
        dice_step = len(contributors)
        if dice_step > 6:
            dice_step = 6
        # Create columns to display the current dice step
        col_l, col_r = st.columns((2,1))
        with col_l:
            # Add some text
            st.subheader("You current dice step is:")
        with col_r:
            # Add the relevant dice image based on the dice step
            if dice_step <= 1:
                st.image(d4_img)
            elif dice_step == 2:
                st.image(d6_img)
            elif dice_step == 3:
                st.image(d8_img)
            elif dice_step == 4:
                st.image(d10_img)
            elif dice_step == 5:
                st.image(d12_img)
            elif dice_step >= 6:
                st.image(d20_img)


        # Create column for each claan
        d4, d6, d8, d10, d12, d20 = st.columns((1,1,1,1,1,1))

        # Add metrics with the score for each claan
        with d4:
            # Get the number of dice for the current step
            d4_count = len([i for i in submissions if (i['Dice step'] <= 1)])
            st.metric(label="D4s", value=d4_count)
        with d6:
            # Get the number of dice for the current step
            d6_count = len([i for i in submissions if (i['Dice step'] == 2)])
            st.metric(label="D6s", value=d6_count)
        with d8:
            # Get the number of dice for the current step
            d8_count = len([i for i in submissions if (i['Dice step'] == 3)])
            st.metric(label="D8s", value=d8_count)
        with d10:
            # Get the number of dice for the current step
            d10_count = len([i for i in submissions if (i['Dice step'] == 4)])
            st.metric(label="D10s", value=d10_count)
        with d12:
            # Get the number of dice for the current step
            d12_count = len([i for i in submissions if (i['Dice step'] == 5)])
            st.metric(label="D12s", value=d12_count)
        with d20:
            # Get the number of dice for the current step
            d20_count = len([i for i in submissions if (i['Dice step'] >= 6)])
            st.metric(label="D20s", value=d20_count)

        # Add spacer
        st.write("---")


    with st.container():
        # Add heading
        st.header("Complete a quest")

                # Name
        name = st.selectbox('Please tell me who you are!',
                            tuple(["Please select your name"] + settings['Wave Riders'])
                        )

        # Acitivity/challenge
        quest = st.radio('What quest did you complete?',
                        settings["Quests"]
                    )

        if quest == "Access your Claan's secret phrase using NordLayer":
            answer = st.text_input("Please enter the Secret Phrase")

        if quest == "Complete the winter scavenger hunt":
            answer = st.text_input("Please enter the solution to the winter scavenger hunt")

        # Add a button
        if st.button('Submit'):
            # Check if new contributor to increment dice step
            if name not in contributors and dice_step < 6:
                dice_step+=1
            # Create dictionary of responses
            submission = {
                "Name": name,
                "Date": datetime.datetime.now(),
                "Quest": quest,
                "Dice step": dice_step
            }
            temp_lookup = [i for i in col.find({"Name": name, "Quest": quest}, { "_id": 0})]
            # Attempt to upload response to DB
            try:
                if name == "Please select your name":
                    st.write("Please tell me who you are!")
                elif len(temp_lookup) >= 1 and quest != "Take a short walk before work, or during lunch and share a photo of something cool that you see with your Claan":
                    st.write("You have already completed that quest!")
                elif quest == "Take a short walk before work, or during lunch and share a photo of something cool that you see with your Claan" and len(temp_lookup) >= 2:
                    st.write("You have already completed that quest twice!")
                elif submissions != [] and submissions[-1]['Date'] > datetime.datetime.now() + datetime.timedelta(seconds = -20):
                    st.write("You have already made a submission in the last 20seconds!")
                elif quest == "Access your Claan's secret phrase using NordLayer" and answer != st.secrets["wave_phrase"]:
                    st.write("Secret phrase is either missing, or incorrect!")
                elif quest == "Complete the winter scavenger hunt" and answer != st.secrets["winter_scav"]:
                    st.write("Solution is either missing, or incorrect!")
                else:
                    col.insert_one(submission)
                    st.experimental_rerun()
            except Exception as e:
                print(e)
                st.write("Submission failed!")

        st.write("---")

    with st.container():
        # Add heading
        st.header("View Claan Activity!")
        # Add some text
        st.write("Press the button below to see what people have been up to! (It is hidden by default as it can be a little slow to load!)")
        # Add button to display claan activity when pressed
        if st.button('View'):
            st.table(submissions)

    with st.container():
        # Add a title
        st.header("Claan Magic Items")

        # Add columns for magic item title, text and image
        item1_l, item1_r = st.columns((2,1))
        with item1_l:
            st.subheader("Spark's Arcane Hourglass")
            st.write("Each fortnight chose a quest, each member of your Claan can complete it twice.")
        with item1_r:
            st.image(sah)

        # Add columns for magic item title, text and image
        item2_l, item2_r = st.columns((2,1))
        with item2_l:
            st.subheader("Azure Sentinel Ointment")
            st.write("One use only. Negate the effects of one effect suffered due to wild magic.")
        with item2_r:
            st.image(aso)
