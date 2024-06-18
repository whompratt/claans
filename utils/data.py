import streamlit as st

from utils.database import Database
from utils.quests import Quest
from utils.record import Record


class Data:
    """Handles communication between Database and Streamlit pages."""

    @classmethod
    def submit_record(cls, record: Record) -> bool:
        """
        Submits a new document to the `quest_log` collection recording the completion of a quest or activity.

        This function _inserts_ a new document, so no filter is performed against the collection in order to keep this class as streamlined as possible.
        As such, validation of whether a user should be able to submit this quest or activity should be performed before calling this function.

        Args:
            record: instance of class `Record` defining the data to submit.

        Returns:
            bool: True on successful submission.
        """
        quest_log = Database.get_collection("quest_log")
        _ = Database.get_documents(collection="quest_log")  # Prevents reloads

        result = quest_log.insert_one(record.to_dict())

        # TODO: Should this be an exception? Once we're in this state we're fucked.
        if result.acknowledged:
            if not cls.update_score(record):
                st.warning("Quest or activity submitted, but failed to update scores.")

        Database.get_documents.clear(collection="quest_log")
        st.session_state["quest_log"] = Database.get_documents(collection="quest_log")

        return result.acknowledged

    @classmethod
    def update_score(cls, record: Record) -> bool:
        return True

    @classmethod
    def define_quest(cls, quest: Quest) -> bool:
        """
        Submits a quest or activity definition to the database.

        Takes an instance of Quest as input, ensuring format consistency across definitions.

        Returns:
            bool: True on successful submission.
        """
        quests = Database.get_collection("quests")

        result = quests.insert_one(quest.to_dict())
        pass
