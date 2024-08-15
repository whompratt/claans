from typing import List

import mongoengine
import streamlit as st

from src.models.claan import Claan
from src.models.record import Record
from src.models.task import Task


class Data:
    """Handles communication between the Database and Streamlit pages."""

    @classmethod
    def init_data(cls) -> None:
        # Scores
        for claan in Claan:
            if not Claan.objects.get(claan=claan):
                Claan(claan=Claan(claan)).save()

    @classmethod
    def load_data(cls) -> None:
        """Convenience function to load most of the relevant data at once."""
        if "records" not in st.session_state:
            st.session_state["records"] = Data.get_records()
        if "scores" not in st.session_state:
            st.session_state["scores"] = Data.get_scores()
        if "tasks" not in st.session_state:
            st.session_state["tasks"] = Data.get_tasks()
        if "active" not in st.session_state:
            st.session_state["active"] = Data.get_tasks({"active": True})
        if "users" not in st.session_state:
            st.session_state["users"] = Data.get_users()

    @classmethod
    def refresh_all(cls) -> None:
        st.session_state["records"] = Data.get_records()
        st.session_state["scores"] = Data.get_scores()
        st.session_state["tasks"] = Data.get_tasks()
        st.session_state["users"] = Data.get_users()

    @classmethod
    def get_records(cls, filter: dict = None) -> List[Record]:
        """Returns all documents from the records collection in the database."""
        if filter is not None:
            return Record.objects(**filter)
        else:
            return Record.objects()

    @classmethod
    def get_scores(cls, filter: dict = None) -> dict:
        """Returns all documents from the scores collection in the database."""
        if filter is not None:
            return Claan.objects(**filter)
        else:
            return Claan.objects()

    @classmethod
    def set_score(cls) -> None:
        """Reads claan and value from session state and sets that claan to that score."""
        Claan.objects(claan=st.session_state["set_score_claan"]).update(
            score=st.session_state["set_score_value"]
        )
        st.session_state["scores"] = Data.get_scores()

    @classmethod
    def get_tasks(cls, filter: dict = None) -> List[Task]:
        """
        Returns all documents from the tasks collection in the database.

        Define a filter as a dict, where key is column to filter on, and value is value to filter for.
        This dict will be **'d into the objects filters.

        E.g.
        filter = {
            "type": RecordType.Quest,
            "dice": [Dice.D4, Dice.D6],
        }
        will become
        Tasks.objects(type=RecordType.Quest, dice=[Dice.D4, Dice.D6])
        """
        if filter is not None:
            return Task.objects(**filter)
        else:
            return Task.objects()

    @classmethod
    def add_task(cls) -> bool:
        """Reads task data from session state and submits new task to the database."""

        task = Task(
            description=st.session_state["add_task_description"],
            task_type=st.session_state["add_task_type"],
            dice=st.session_state["add_task_dice"],
            ephemeral=st.session_state["add_task_ephemeral"],
            last=None,
        )

        try:
            task.validate()
        except mongoengine.errors.ValidationError as e:
            st.error("Task submission failed validation")
            st.exception(e)
        else:
            try:
                task.save()
            except mongoengine.errors.NotUniqueError as e:
                st.error("Task definition is not unique.")
                st.exception(e)

        st.session_state["tasks"] = cls.get_tasks()

    @classmethod
    def delete_task(cls) -> None:
        """Reads task from session state and deletes it from the database."""
        task = Task.objects(
            description=st.session_state["delete_task_description"].description
        )
        task.delete()

        st.session_state["tasks"] = cls.get_tasks()

    @classmethod
    def get_users(cls, filter: dict = None) -> List[User]:
        """Returns all documents from the users collection in the database."""
        if filter is not None:
            return User.objects(**filter)
        else:
            return User.objects()

    @classmethod
    def add_user(cls) -> None:
        """Uses content in session state to submit a new user."""
        user = User(
            name=st.session_state["add_user_name"],
            claan=st.session_state["add_user_claan"],
        )

        try:
            user.validate()
        except mongoengine.errors.ValidationError as e:
            st.error("User name is a required field")
            st.exception(e)
        else:
            try:
                user.save()
                st.session_state["users"] = cls.get_users()
                st.session_state[f"users_{user.claan.name}"] = cls.get_users(
                    {"claan": user.claan}
                )
            except mongoengine.errors.NotUniqueError as e:
                st.error("User name and claan combo must be unique")
                st.exception(e)

    @classmethod
    def delete_user(cls) -> None:
        """Deletes the user found in the session state."""
        user = cls.get_users(
            {
                "claan": st.session_state["delete_user_claan"],
                "name": st.session_state["delete_user_name"].name,
            }
        )
        user.delete()

        st.session_state["users"] = cls.get_users()
