import datetime
import json
import random
import numpy as np
import streamlit as st
from pathlib import Path
from PIL import Image
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi

CLAAN = "Thunder Walkers"

# Set the page title and icon and set layout to "wide" to minimise margains
st.set_page_config(page_title=CLAAN, page_icon=":lightning_cloud:", layout="wide")

# Load the assets for the app
img_path = Path(__file__).parents[0]
claan_img = Image.open(f"{img_path}/Page_Images/Thunder-walkers-hex.png")


def check_password():
    """Returns `True` if the user had the correct password."""
    def password_entered():
        """Checks whether a password entered by the user is correct."""
        if st.session_state["password"] == st.secrets["thunder_password"]:
            st.session_state["thunder_password_correct"] = True
            del st.session_state["password"]  # don't store password
        else:
            st.session_state["thunder_password_correct"] = False

    if "thunder_password_correct" not in st.session_state:
        # First run, show input for password.
        st.text_input(
            "Password", type="password", on_change=password_entered, key="password"
        )
        return False

    elif not st.session_state["thunder_password_correct"]:
        # Password not correct, show input + error.
        st.text_input(
            "Password", type="password", on_change=password_entered, key="password"
        )
        st.error("😕 Password incorrect")
        return False

    else:
        # Password correct.
        return True



if "db" not in st.session_state:
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
    st.session_state.db = client["Claan_app"]
    st.session_state.col = st.session_state.db["thunder_walkers"]
    st.session_state.score_col = st.session_state.db["scores2"]

if "settings" not in st.session_state:
    with open(f"{img_path}/settings.json") as fp:
        # Load the .json file of settings
        st.session_state.settings = json.load(fp)
        st.session_state.settings[CLAAN].sort()


def get_data():
    st.session_state.total_score = [i['Score'] for i in st.session_state.score_col.find({"Claan": CLAAN})]
    scores = [i for i in st.session_state.score_col.find({"Date": {"$gte": datetime.datetime.strptime(st.session_state.settings['Fortnight Start Date'], ("%d/%m/%Y"))}, "Claan": CLAAN})]
    print(scores)
    # Create counters for the scores and activity counters
    fortnight_score = 0
    fortnight_quests = 0
    fortnight_activities = 0

    # Iterate over scores and increment relevant counters
    for i in scores:
        fortnight_score += i['Score']

        if "Type" in i and i['Type'] == "Quest":
            fortnight_quests += 1
        elif "Type" in i and i['Type'] == "Activity":
            fortnight_activities += 1
    
    # Set session_state variables
    st.session_state.fortnight_score = fortnight_score
    st.session_state.fortnight_quests = fortnight_quests
    st.session_state.fortnight_activities = fortnight_activities

    st.session_state.submissions = [i for i in st.session_state.col.find({"Date": {"$gte": datetime.datetime.strptime(st.session_state.settings['Fortnight Start Date'], ("%d/%m/%Y"))}}, { "_id": 0})]


def submit_quest():
    if st.session_state.qname == "Please select your name":
        st.toast("Please select your name!!")

    else:
        roll = random.randint(1, st.session_state.settings["Quests"][st.session_state.quest])
        
        # Create submission for quest log
        submission = {
            "Name": st.session_state.qname,
            "Date": datetime.datetime.now(),
            "Quest/Activity": st.session_state.quest,
            "Dice step": st.session_state.settings["Quests"][st.session_state.quest],
            "Roll": roll
        }

        # Create submission for scores
        score_submission = {
            "Claan": CLAAN,
            "Score": roll,
            "Type": "Quest",
            "Date": datetime.datetime.now()
        }

        # Get today's date at midnight (00:00:00)
        today_start = datetime.datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        # Get tomorrow's date at midnight (00:00:00)
        tomorrow_start = today_start + datetime.timedelta(days = 1)

        # Find documents where the creation time falls within today's range
        query = {}

        temp_lookup = [i for i in st.session_state.col.find({"Date": {"$gte": today_start, "$lt": tomorrow_start}, "Name": st.session_state.qname, "Quest": st.session_state.quest}, { "_id": 0})]

        # Attempt to upload response to DB
        try:
            if len(temp_lookup) >= 1: 
                st.toast("You have already completed that quest today!")
            else:
                st.session_state.col.insert_one(submission)
                st.session_state.score_col.insert_one(score_submission)
                st.toast(f"Submitted for {roll} points!")
                get_data()
        except Exception as e:
            print(e)
            st.toast("Submission failed!")

def submit_activity():
    if st.session_state.aname == "Please select your name":
        st.toast("Please select your name!!")

    else:
        roll = random.randint(1, st.session_state.settings["Activities"][st.session_state.activity])

        # Create submission for quest log
        submission = {
            "Name": st.session_state.aname,
            "Date": datetime.datetime.now(),
            "Quest/Activity": st.session_state.activity,
            "Dice step": st.session_state.settings["Activities"][st.session_state.activity],
            "Roll": roll
        }

        # Create submission for scores
        score_submission = {
            "Claan": CLAAN,
            "Score": roll,
            "Type": "Activity",
            "Date": datetime.datetime.now()
        }

        # Get today's date at midnight (00:00:00)
        today_start = datetime.datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        # Get tomorrow's date at midnight (00:00:00)
        tomorrow_start = today_start + datetime.timedelta(days = 1)

        # Find documents where the creation time falls within today's range
        query = {}

        temp_lookup = [i for i in st.session_state.col.find({"Date": {"$gte": today_start, "$lt": tomorrow_start}, "Name": st.session_state.aname, "Activity": st.session_state.activity}, { "_id": 0})]

        # Attempt to upload response to DB
        try:
            if len(temp_lookup) >= 1: 
                st.toast("You have already completed that activity today!")
            else:
                st.session_state.col.insert_one(submission)
                st.session_state.score_col.insert_one(score_submission)
                st.toast(f"Submitted for {roll} points!")
                get_data()
        except Exception as e:
            print(e)
            st.toast("Submission failed!")


if "scores" not in st.session_state:
    get_data()


def main():
    if check_password():
        # Header section
        with st.container():
            # Create columns
            head_l, head_r = st.columns((3,1))

            with head_l:
                # Add a subheader
                st.subheader("Advancing Analytics")
                # Add a title
                st.title(CLAAN)
                st.write(f"Welcome to the {CLAAN} Claan area! Here you can log quests, activities and steps!")

                st.subheader("Fortnight Breakdown!")
                col1, col2, col3, col4 = st.columns((1,1,1,1))
                with col1: 
                    st.metric("Overall Score!", sum(st.session_state.total_score))
                with col2:
                    st.metric("Score", st.session_state.fortnight_score)
                with col3:
                    st.metric("Quest Completed", st.session_state.fortnight_quests)
                with col4:
                    st.metric("Activities Completed", st.session_state.fortnight_activities)
            with head_r:
                # Add logo
                st.image(claan_img)

            st.write("---")

        with st.container():
            # Create columns for logging the two 
            log_l, log_r = st.columns((1,1))

            with log_l:
                # Add heading
                st.header("Complete a quest")

                # Name
                st.session_state.qname = st.selectbox('Please tell me who you are!',
                                    tuple(["Please select your name"] + st.session_state.settings[CLAAN]), key=0
                                )

                # Acitivity/challenge
                st.session_state.quest = st.radio('What quest did you complete?',
                                st.session_state.settings["Quests"]
                            )
                st.button("Submit Quest.", on_click=submit_quest)

            with log_r:
                # Add heading
                st.header("Log steps or activities")

                # Name
                st.session_state.aname = st.selectbox('Please tell me who you are!',
                                    tuple(["Please select your name"] + st.session_state.settings[CLAAN]), key=1
                                )

                # Acitivity/challenge
                st.session_state.activity = st.radio('What quest did you complete?',
                                st.session_state.settings["Activities"]
                            )
                st.button("Log activity.", on_click=submit_activity)

            st.write("---")

        with st.container():
            # Add some text
            st.header("Detailed View")
            st.write("Press the button below to see the details of what people have been up to! (It is hidden by default as it can be a little slow to load!)")
            # Add button to display claan activity when pressed
            if st.button('View'):
                st.table(st.session_state.submissions)


if __name__ == "__main__":
     main()