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

    # Add description
    st.write("Welcome to seasion 3 of Claans at Advancing Analytics. This time around things have been shaken up and injected with a healthy dose of D&D flair!")
    st.write("Using the Claan Portal you can see the scores as they stand, see this fortnights quests, and access the Claan area to see your upgrades and dice pool!")

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
        # Get scores for the claan, using the sum of the scores, and the last entry as the delta
        earth_scores = [i['Score'] for i in scores if (i['Claan']=="earth striders")]
        # Add metric for claan score
        st.metric(label="Earth Striders", value=sum(earth_scores), delta=earth_scores[-1])

    # Add content to second column
    with col2:
        # Add the claan image
        st.image(fire_img)
        # Get scores for the claan
        fire_scores = [i['Score'] for i in scores if (i['Claan']=="fire dancers")]
        # Add metric for claan score, using the sum of the scores, and the last entry as the delta
        st.metric(label="Fire Dancers", value=sum(fire_scores), delta=fire_scores[-1])

    # Add content to third column
    with col3:
        # Add the claan image
        st.image(thunder_img)
        # Get scores for the claan
        thunder_scores = [i['Score'] for i in scores if (i['Claan']=="thunder walkers")]
        # Add metric for claan score, using the sum of the scores, and the last entry as the delta
        st.metric(label="Thunder Walkers", value=sum(thunder_scores), delta=thunder_scores[-1])

    # Add content to last column
    with col4:
        # Add the claan image
        st.image(wave_img)
        # Get scores for the claan
        wave_scores = [i['Score'] for i in scores if (i['Claan']=="wave riders")]
        # Add metric for claan score, using the sum of the scores, and the last entry as the delta
        st.metric(label="Wave Riders", value=sum(wave_scores), delta=wave_scores[-1])

    # Add spacer
    st.write("---")

# Add section for changes
with st.container():
    st.markdown(
"""
# Claan ChAAos
Welcome to season 3 of Claans at Advancing Analytics. This time around things have been shaken up and injected with a healthy dose of D&D flair! This season should feel like a mixture of a roller coaster and an adventure. There are a whole host of changes, but fundamentally it is the same: bond with you Claan mates, score points, and fight for a seat in the legendary all-you-claan-eat feast!

### Refreshed Claans
A new season brings fresh Claans. Bid farewell to you current Claan mates and share you final goodbyes in preparation for the grand reshuffling. There will be a Gathering of epic proportions as all names are thrown to the cosmic winds to let the universe decide the members of each Claan. 

You should also get ready to move and decorate! As you will be required to relocate your desk to the zone of your new Claan! This is a good opportunity for a spring clean and to rebrand yourself as the person with the coolest desk. Naturally there will be **Claan Dice** available for the best desk!

### A New Way of Scoring
**Claan Dice**? What are these mystical and magical objects I hear you ask?! Rather than having fixed numbers of points attached to the Claan effort, completeing quests will earn you Claan dice. 

Every fortnight there will be a list of quests published to the Claan portal for all members of the Claan to complete. These will range from the standard step count challenges, to solving Wordles, to spending bonusly points. 

Each time you complete one of these quests you can log it in the portal and earn a dice for you Claan. At the end of the fortnight you will have accumulated a pool of dice equal to the number of quests completed by the Claan.

The Claan will then roll the accumulated dice and convert the results into points! Best prepare your shrine to lady luck and make an offering in Tymora's name.

#### Upgrading the Claan Dice
The base Claan dice will be a D4, but for each different member of the Claan who contributes in a given fortnight the dice will go up one step. 

D4 -> D6 -> D8 -> D10 -> D12 -> D20

In order to maximise you score you will need 6 people in the Claan to complete at least one quest each week, so work as a team to make sure everyone is involved!

This app will have a home page with an overview of the total scores for each Claan, their members, and the current set of quests to be completed! Each Claan will then have their own page, locked behind a top secret password, where they can log their quests, see the number of dice in the current pool, and also track which step their Claan Dice are on. 

### Time Marches On
This season, time waits for no-one! quests will be up for a fortnight then the window will close and entries for that period of time will no longer be valid. So make sure to keep on top of things and log your quests as you complete them!

Just like this season we will also have Claanpions to help you remember what is going on and keep on top of the quests. This season they might even have *special powers*...


### Wild Magic
To add to the chaos already caused by the Claan shuffle and points being accumulated by rolling dice, season 3 will introduce wild magic!

At certain points throughout the season a roll on the wild magic table might be required, which can be both a blessing and a curse! To roll on the wild magic table simply roll a d100 and consult the table to see chaos is unleashed!

This effects can sometimes be positive or sometimes negative, but the higher the dice roll, the better the effect will likely be!


##### Sample Negative Effects
| Roll | Name | Effect |
|:---|:---:|:---:|
| 11 - 15 | Distorted Distribution | When scoring at the end of the fortnight, subtract 5 from the roll of the Dice pool. |
| 16 - 20 | Entropy Eclipse | Roll a d6 and subtract the result from your Claan score. |
| 21 - 25 | Dropout Dilemma |  Lose d4 die from your Claan Dice pool. |
| 26 - 30 | Model Misfit | Reduce the step of your Claan Dice pool by 1. |


##### Sample Positive Effects
| Roll | Name | Effect |
|:---|:---:|:---:|
| 66 - 70 | Precision Surge | Add a d20 to your Claan Dice pool. |
| 71 - 75 | Regression Resurgence | Add d4 dice to your Claan pool. |
| 76 - 80 | Insightful Overflow | Increase the step of your Claan DIce pool by 1. |
| 8 1- 85 | Data Harmony |  When scoring at the end of the fortnight add 5 to the roll of the Dice pool. |
| 86 - 90 | Algorithmic Advantage | Gain an extra dice with a boosted probability distribution for your Claan Dice pool. |

### Dice as Currency?!
To make Claan Dice even more valuable, they won't just be your primary mechanism for scoring points, they will also be exchangable for powerful claan items. Some of these items will have effects that last for the duration of the season, while others will be "consumable" and have effects that only grant a temporary effect.

Below are two of the items that are on offer:


#### Azure Aegis Shield
**Cost: 6d20**
For the rest of this season dice cannot be removed from your Claan Dice pool, even through the effects of wild magic.

#### Schema Shifting Elixir
**Cost: 3d8**
Merge your current dice pool with that of another Claan of your choice. Taking half the dice at random for each Claan.


Some of the items will require dice which are a number of steps above the base, which means if you Claan decide they want to buy them then a team effort will be required to increase the steps of the dice enough to become useable currency for the item. Buying an item that costs d20s means 6 Claan members will need to contribute.

### The Tez and Si Effect
This season Terry and Simon will be around to cause even more chaos during company events, they have the power to: grant Claan Dice, increase the dice step of a Claan, and even cause rolls on the Wild Magic table! 

Stay vigilant if they are around!
""")