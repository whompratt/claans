import streamlit as st
from pathlib import Path
from PIL import Image

def check_password():
    """Returns `True` if the user had the correct password."""
    def password_entered():
        """Checks whether a password entered by the user is correct."""
        if st.session_state["password"] == st.secrets["earth_password"]:
            st.session_state["earth_password_correct"] = True
            del st.session_state["password"]  # don't store password
        else:
            st.session_state["earth_password_correct"] = False

    if "earth_password_correct" not in st.session_state:
        # First run, show input for password.
        st.text_input(
            "Password", type="password", on_change=password_entered, key="password"
        )
        return False

    elif not st.session_state["earth_password_correct"]:
        # Password not correct, show input + error.
        st.text_input(
            "Password", type="password", on_change=password_entered, key="password"
        )
        st.error("😕 Password incorrect")
        return False

    else:
        # Password correct.
        return True

# Load the assets for the app
img_path = Path(__file__).parents[0]
claan_img = Image.open(f"{img_path}/Page_Images/Earth-striders-hex.png")

# Set the page title and icon and set layout to "wide" to minimise margains
st.set_page_config(page_title="Earth Striders", page_icon=":rock:")

if check_password():
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