import logging
import os
import requests
import streamlit as st
from pathlib import Path
from PIL import Image
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
from streamlit_lottie import st_lottie
import time
import random
from openai import AzureOpenAI
import json

# Get relative path
img_path = Path(__file__).parents[0]
ROOM = "Room_4"

def load_players():
    """Function to load players and their scores from MongoDB and add them to the session_state
    """
    # Find "Type" field where value is Score in mongodb and convert to a list of dicts
    st.session_state.player_scores = [i for i in col.find({"Type": "Score"})]
    # Create a unique list of names from the found dictionaries
    st.session_state.player_names = list(set([i['Player'] for i in st.session_state.player_scores]))


def add_player():
    """Function to add a play to MongoDB if they have no already been added
    """
    # Check if the current player name is in the list of registered players in the DB
    if st.session_state.name not in st.session_state.player_names:
        # Add a Score document to the DB to initialise the player
        col.insert_one({"Type": "Score", "Player": st.session_state.name, "Score": 0})
        # Send them a notifaction to let them know it has worked!
        st.toast(f"Hi {st.session_state.name}, you should now be able to select your name in the list!")
        # Reload the players to keep a current list in the session state
        load_players()
    # If the are already there, send them a notifaction that they have already submitted
    else:
        st.toast("You might already be in the list, take another look...")


def get_game_state():
    """Function to find and control the game state based on Mode documents in the DB
    """
    # Get all round data from the DB
    session_data = [i for i in col.find({"Type": "Round"})]

    # If there haven't been any round yet set round to 0
    if session_data == []:
        st.session_state.round = 0
    # Continue if there has been at least one round registered
    else:
        # Get the most recent round entry from the DB and store it in the session state
        st.session_state.round = [i['Round'] for i in session_data][-1]
        # Get the most recent mode entry for the current round and save it in the session state
        st.session_state.mode = [i['Mode'] for i in col.find({"Type": "Game_Mode", "Round": st.session_state.round})][-1]

        # If it is currently in the prompting stage (where a random player suggests a prompt and generates an image)
        if st.session_state.mode == "Prompt":
            # Load the prompter from the database and store in session state!
            st.session_state.prompter = [i['Prompter'] for i in col.find({"Mode": "Prompt", "Round": st.session_state.round})][-1]

        # If it is currently the guessing stage (Where all other players try and guess a prompt for the given image)
        if st.session_state.mode == "Guess":
            # Get the prompt for the current round
            prompt_data = [i for i in col.find({"Type": "Prompt", "Round": st.session_state.round})][-1]
            # Save the prompt itself, and the prompter to the session state
            st.session_state.prompter = prompt_data["Prompter"]
            st.session_state.prompt = prompt_data["Prompt"]
            # Get all of the guesses for the current round 
            guesses = [i for i in col.find({"Type": "Guess", "Round": st.session_state.round})]
            # Save the players who have guessed to the session state
            st.session_state.guessers = [i["Player"] for i in guesses] + [st.session_state.prompter]

        # If it is curently the voting stage (where players vote on which they think is the real prompt)
        if st.session_state.mode == "Vote":
            # Get the prompt for the current round
            prompt_data = [i for i in col.find({"Type": "Prompt", "Round": st.session_state.round})][-1]
            # Save the prompt itself, and the prompter to the session state
            st.session_state.prompter = prompt_data["Prompter"]
            st.session_state.prompt = prompt_data["Prompt"]
            # Get all of the guesses for the current round 
            guesses = [i for i in col.find({"Type": "Guess", "Round": st.session_state.round})]
            st.session_state.guesses = [i["Guess"] for i in guesses] + [st.session_state.prompt]
            # Randomise the order of the list
            random.shuffle(st.session_state.guesses)
            # Get all the votes
            votes = [i for i in col.find({"Type": "Vote", "Round": st.session_state.round})]
            # Save the players who have guessed to the session state
            st.session_state.voters = [i["Player"] for i in votes] + [st.session_state.prompter]

        # If it is currently the scoring stage (where the votes are converted into points)
        if st.session_state.mode == "Score":
            # Get the prompt for the current round
            prompt_data = [i for i in col.find({"Type": "Prompt", "Round": st.session_state.round})][-1]
            # Save the prompt itself, and the prompter to the session state
            st.session_state.prompter = prompt_data["Prompter"]
            st.session_state.prompt = prompt_data["Prompt"]
            # Get all of the guesses for the current round 
            guesses = [i for i in col.find({"Type": "Guess", "Round": st.session_state.round})]
            st.session_state.guesses_dict = guesses
            # Get all the votes
            votes = [i for i in col.find({"Type": "Vote", "Round": st.session_state.round})]
            st.session_state.votes_dict = votes

def refresh_game():
    """Function to reload players and game state to update session state
    """
    load_players()
    get_game_state()


def start_game():
    """Function to start round one of the game!
    """
    # Add a round document to the DB
    col.insert_one({"Type": "Round", "Round": 1})
    # Generate a random player to be the prompter
    prompter = random.choice(st.session_state.player_names)
    # Insert the prompter into the DB in a game_mode document
    col.insert_one({"Type": "Game_Mode", "Mode": "Prompt", "Prompter": prompter, "Round": 1})
    # Refresh
    get_game_state()


def submit_prompt():
    """Function to submit a prompt to generate some art
    """
    with st.spinner("Generating image, please wait..."):
        client = AzureOpenAI(
            api_version="2024-02-01",
            api_key=st.secrets["AZURE_OPENAI_API_KEY"],
            azure_endpoint=st.secrets['AZURE_OPENAI_ENDPOINT']
        )

        result = client.images.generate(
            model="ab-aa-dalle3", # the name of your DALL-E 3 deployment
            prompt=st.session_state.prompt,
            n=1
        )

        json_response = json.loads(result.model_dump_json())

        # Set the directory for the stored image
        image_dir = os.path.join(img_path, '/Page_Images')

        # If the directory doesn't exist, create it
        if not os.path.isdir(image_dir):
            os.mkdir(image_dir)

        # Initialize the image path (note the filetype should be png)
        image_path = f'{img_path}/Page_Images/{ROOM}_Round_{st.session_state.round}.png'

        # Retrieve the generated image
        image_url = json_response["data"][0]["url"]  # extract image URL from response
        generated_image = requests.get(image_url).content  # download the image
        with open(image_path, "wb") as image_file:
            image_file.write(generated_image)

    # Add the prompt, prompter and round to a Prompt document in the DB
    col.insert_one({"Type": "Prompt", "Prompter": st.session_state.prompter, "Prompt": st.session_state.prompt, "Round": st.session_state.round})
    # Add a game_mode document to the DB to move the game onto the guessing stage
    col.insert_one({"Type": "Game_Mode", "Mode": "Guess", "Round": st.session_state.round})

    # Refresh
    get_game_state()


def submit_guess():
    """Function for a player to submit their guess as to the prompt that was used to generate the image
    """
    # Add a Guess document to the db with the player, the round, and the guess
    col.insert_one({"Type": "Guess", "Round": st.session_state.round, "Player": st.session_state.name, "Guess": st.session_state.guess})
    # Refresh
    get_game_state()


def submit_vote():
    """Function for a player to vote for what they think is the real prompt
    """
    # Add vote document to the db with the player, the round, and the vote
    col.insert_one({"Type": "Vote", "Round": st.session_state.round, "Player": st.session_state.name, "Vote": st.session_state.vote_option})
    get_game_state()


def continue_to_voting():
    """Function to move the game from guessing to voiting
    """
    # Add a Game_Mode document to the DB for voting mode for the current round
    col.insert_one({"Type": "Game_Mode", "Mode": "Vote", "Round": st.session_state.round})
    get_game_state()


def continue_to_scoring():
    """Function to move the game from voting to scoring
    """
    # Add a Game_Mode document to the DB for scoring mode for the current round
    col.insert_one({"Type": "Game_Mode", "Mode": "Score", "Round": st.session_state.round})
    get_game_state()


def continue_to_next_round():
    # Iterate over all of the votes and compare to the prompt, if they match the voter and the prompter get a point
    for vote in st.session_state.votes_dict:
        if st.session_state.prompt == vote["Vote"]:
            col.insert_one({"Type": "Score", "Player": st.session_state.prompter, "Score": 1})
            col.insert_one({"Type": "Score", "Player": vote["Player"], "Score": 1})

    # Iterate over all of the guesses and over all the votes, if a guess was voted for that player gets a point
    for guess in st.session_state.guesses_dict:
        for vote in st.session_state.votes_dict:
            if guess["Guess"] == vote["Vote"]:
                col.insert_one({"Type": "Score", "Player": guess["Player"], "Score": 1})
    # Add a round document to the DB
    col.insert_one({"Type": "Round", "Round": st.session_state.round + 1})
    # Generate a random player to be the prompter
    prompter = random.choice(st.session_state.player_names)
    # Insert the prompter into the DB in a game_mode document
    col.insert_one({"Type": "Game_Mode", "Mode": "Prompt", "Prompter": prompter, "Round": st.session_state.round + 1})
    # Refresh
    get_game_state()


# Set the Mongo DB username, password and URI
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
db = client["Claan_app"]
col = db[ROOM]

# Load images
logo_img = Image.open(f"{img_path}/Page_Images/Logo.png")

# Load players and get the game state
if "First_Run" not in st.session_state:
    get_game_state()
    st.session_state.First_Run = True
load_players()
# Set the page title and icon and set layout to "wide" to minimise margains
st.set_page_config(page_title="Claan ChAAos", page_icon=":dragon:")


def main():
    # Add sidebar content
    with st.sidebar:
        # Add a text input for the player to enter their name
        st.session_state.name = st.text_input("Please type your name (and press enter)")
        # Show them what the current input is
        st.info(f"Name set to: {st.session_state.name}")
        # Button to callback the add_player function and add the player to the DB
        st.button("Join", on_click=add_player)

        # Iterate over the player names
        for name in st.session_state.player_names:
            # Get a list of scores for the current player
            scores = [i['Score'] for i in st.session_state.player_scores if (i['Player']==name)]
            # Display a metric with their name and current score! 
            st.metric(label=name, value=sum(scores), delta=scores[-1])

    # Header section
    with st.container():
        # Create columns
        head_l, head_r = st.columns((2.5,1))

        with head_l:
            # Add a subheader
            st.subheader("Advancing Analytics")
            # Add a title
            st.title("Generative AI Game")
            # Add another subheader
            st.subheader("Room 1")

        with head_r:
            # Add logo
            st.image(logo_img)

        # Add description
        st.write("This is the Generative AI Game! A true test of your prompting ability, wit and deception!")
        st.write("Each player will take it in turns to write a prompt and generate an image, then the rest of the group will see the image and need to decide which prompt is the original!")
        st.write("If you guess the original prompters prompt you both get points, but if other people guess yours then you can snag bonus points ofr being sneaky!")
        st.write("You might need to press the refresh button from time to time and communicate with the people on your table, this game is a little rough and ready...")
        # Add spacer
        st.write("---")

        # Check if the player has entered their name 
        if st.session_state.name == "":
            # Add a subheader a description
            st.subheader("Please join the game by entering your name in the sidebar!")
            st.info("If you don't see your name in the list of scores you will also need to press join!")
        else:
            st.subheader(f"Welcome {st.session_state.name} to the GenAI game!")
            # Content to display is the round is 0
            if st.session_state.round == 0:
                st.write("Please wait for everyone on your table to enter the game! You can see who is currently in the game in the side bar! (Press refresh periodically to update)")
                st.success("Once you are all ready nominate someone to Start the Game!")
                st.button("Start game!", on_click=start_game)

            # Content to display if the round is anything greater than 0
            if st.session_state.round > 0:
                st.subheader(f"Round {st.session_state.round}")
                # Functionality for the prompt mode
                if st.session_state.mode == "Prompt":
                    # Display content for the prompter if the prompter name matches the player name
                    if st.session_state.prompter == st.session_state.name:
                        st.write(f"{st.session_state.name} you are the prompter!")
                        st.session_state.prompt = st.text_area("Please enter a prompt!")
                        st.info(f"Your prompt reads: {st.session_state.prompt}")
                        if st.session_state.prompt != "":
                            st.button("Submit", on_click=submit_prompt)
                    # Otherwise the player is a guesser, display content for guesser
                    else:
                        st.write(f"{st.session_state.prompter} is currently thinking of a prompt, please give them a second!")

                # Functionality for guess mode 
                elif st.session_state.mode == "Guess":
                    st.image(Image.open(f"{img_path}/Page_Images/{ROOM}_Round_{st.session_state.round}.png"), width=250)
                    # Display content for the guesser if the prompter name is not the same as the player name
                    if st.session_state.name != st.session_state.prompter:
                        # Check if they have submitted a guess or not
                        if st.session_state.name in st.session_state.guessers:
                            # If they have submitted a guess display some info and a tracker on the number of guesses
                            st.info("Thanks for submitting your guess! Please wait for everyone else to finish!")
                            st.metric("Guesses", f"{len(st.session_state.guessers)-1}/{len(st.session_state.player_names)-1}")
                        # If they have not submitted a guess
                        else:
                            # Display a text box for them to enter a prompt and as button to submit the guess
                            st.write("Please guess the prompt you think create the above image!")
                            st.session_state.guess = st.text_area("Enter guess")
                            st.info(f"Your prompt reads: {st.session_state.guess}")
                            if st.session_state.guess != "":
                                st.button("Submit", on_click=submit_guess)
                    # If they are a prompter displaya note and a tracker for the number of guesses
                    else:
                        st.write("Everyone else is writing their guess, please give them a second!")
                        st.metric("Guesses", f"{len(st.session_state.guessers)-1}/{len(st.session_state.player_names)-1}")
                        # Once the number of guesses equals the number of players show a continue button to move to vote mode
                        if len(st.session_state.guessers) == len(st.session_state.player_names):
                            st.button("Continue", on_click=continue_to_voting)

                # Functionality for voting mode
                elif st.session_state.mode == "Vote":
                    st.image(Image.open(f"{img_path}/Page_Images/{ROOM}_Round_{st.session_state.round}.png"), width=250)
                    # Display content for the guesser if the prompter name is not the same as the player name
                    if st.session_state.name != st.session_state.prompter:
                        # Check if they have submitted a guess or not
                        if st.session_state.name in st.session_state.voters:
                            # If they have submitted a guess display some info and a tracker on the number of guesses
                            st.info("Thanks for submitting your vote! Please wait for everyone else to finish!")
                            st.metric("Votes", f"{len(st.session_state.voters)-1}/{len(st.session_state.player_names)-1}")
                        # If they have not submitted a guess
                        else:
                            # Display a text box for them to enter a prompt and as button to submit the guess
                            st.write("Please vote for the prompt you think created the above image!")
                            st.session_state.vote_option = st.radio("Please select the prompt you wish to vote for", st.session_state.guesses)
                            st.button("Submit", on_click=submit_vote)
                    # If they are a prompter displaya note and a tracker for the number of guesses
                    else:
                        st.write("Everyone else is casting their vote, please give them a second!")
                        st.metric("Votes", f"{len(st.session_state.voters)-1}/{len(st.session_state.player_names)-1}")
                        # Once the number of guesses equals the number of players show a continue button to move to vote mode
                        if len(st.session_state.voters) == len(st.session_state.player_names):
                            st.button("Continue", on_click=continue_to_scoring)

                # Functionality for scoring mode!
                elif st.session_state.mode == "Score":
                    st.image(Image.open(f"{img_path}/Page_Images/{ROOM}_Round_{st.session_state.round}.png"), width=250)
                    st.write("You can now check out the points gained for this round! When you are ready ask the prompter to move on to the next round!")
                    # Create a counter to track the number of votes for the correct prompt
                    ctr = 0
                    # Iterate over all of the votes
                    for vote in st.session_state.votes_dict:
                            # If the vote matches the prompt increase the counter!
                            if st.session_state.prompt == vote["Vote"]:
                                ctr += 1
                    st.success(f"The correct prompt was: {st.session_state.prompt} and it recieved {ctr} votes!")
                    # Iterate over the players guesses
                    for guess in st.session_state.guesses_dict:
                        # Create a counter to track the number of votes
                        ctr = 0
                        # Iterate over all the votes, if the vote matches the current guess increase the counter!
                        for vote in st.session_state.votes_dict:
                            if guess["Guess"] == vote["Vote"]:
                                ctr += 1
                        # Display the number of votes for the current points
                        st.write(f"{guess['Player']}: \"{guess['Guess']}\" got {ctr} votes")
                    # Show the prompter the next round button!
                    if st.session_state.name == st.session_state.prompter:
                        st.info("Move the the game onto the next round when everyone at the table is ready!")
                        st.button("Next round!", on_click=continue_to_next_round)

        # Display button to refresh the page
        st.button("Refresh!", on_click=get_game_state)


if __name__ == "__main__":
    main()
