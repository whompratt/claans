import streamlit as st
from pathlib import Path
from PIL import Image

# Load the assets for the app
img_path = Path(__file__).parents[0]
claan_img = Image.open(f"{img_path}/Page_Images/Earth-striders-hex.png")

# Set the page title and icon and set layout to "wide" to minimise margains
st.set_page_config(page_title="Earth Striders", page_icon=":rock:")

# Header section
with st.container():
    # Create columns
    head_l, head_r = st.columns((2.5,1))

    with head_l:
        # Add a subheader
        st.subheader("Advancing Analytics")
        # Add a title
        st.title("Earth Striders")

    with head_r:
        # Add logo
        st.image(claan_img)

    st.write("Welcome to the Earth Striders Claan area, check back in later for more goodies!")