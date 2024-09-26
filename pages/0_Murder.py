import streamlit as st

from src.utils import data
from src.utils.database import Database


def init_page() -> None:
    st.set_page_config(page_title="MURDER", page_icon=":knife:")

    st.markdown(
        """<style>
        .st-emotion-cache-15zws4i, .st-emotion-cache-1j7f08p {
            color: #F5F5F5
        }
        </style>""",
        unsafe_allow_html=True,
    )

    with Database.get_session() as session:
        st.session_state["hit_list"] = data.get_hit_list(_session=session)

        st.header("There's been a MURDER!")
        st.subheader("AAFest - a bloody affair")

        st.divider()

        st.header("Rules")
        st.subheader("Keep your wits about you!")
        st.write(
            "During this Away Day, a company wide game of Murder will take place. Every person will be given a Target and a Task, and the goal is to 'kill' your target for Claan points.",
        )
        st.write(
            "If you're successful, you get a D4 for your Claan and inherit your target's target. If, however, you get killed first then you're out of the game!"
        )
        st.write(
            "However, you can come to me for another fun activity and a chance to earn some more points."
        )
        st.write(
            "If one agent remains by the end of the away day, they will earn BIG points for their Claan!"
        )

        st.divider()

        with st.container(border=True):
            st.header("Agents Remaining")
            st.metric("Count", len(st.session_state["hit_list"]))

        st.divider()

        with st.form(key="agent_form", clear_on_submit=False, border=True):
            st.header("Agent Login")
            st.selectbox(
                label="Agent",
                key="murder_agent",
                options=st.session_state["hit_list"],
                format_func=lambda row: row.agent.name,
            )
            st.form_submit_button(
                label="Authorize",
                on_click=data.get_agent_info,
                kwargs={"_session": Database.get_session()},
            )

        if "agent_info" in st.session_state:
            with st.container(border=True):
                st.header("Hello agent, you have an assignment.")
                st.divider()
                st.subheader("Your target is:")
                st.write(st.session_state["agent_info"]["target"]["user"].name)
                st.subheader("Complete the following:")
                st.write(st.session_state["agent_info"]["task"])
                if st.button(
                    label="Confirm Kill",
                    on_click=data.confirm_kill,
                    kwargs={"_session": Database.get_session()},
                ):
                    st.toast("Well done agent. A new target has been assigned to you.")
                st.write(
                    "If your target isn't present, please alert your handler (Jake) to refresh your assignemnt."
                )


def main() -> None:
    init_page()


if __name__ == "__main__":
    main()
