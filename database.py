import random

import pymongo
import pymongo.collection
import pymongo.database
import streamlit as st

from claans import Claans
from record import Record


class Database:
    @classmethod
    @st.cache_resource
    def get_client(cls) -> pymongo.MongoClient:
        client = pymongo.MongoClient(**st.secrets["mongo"])
        try:
            client.admin.command("ping")
        except pymongo.errors.ConnectionFailure as e:
            st.error("Fatal error getting database connection")
            st.exception(e)
        else:
            return client

    @classmethod
    @st.cache_resource
    def get_database(cls) -> pymongo.database.Database:
        client = cls.get_client()
        return client.get_database("claans-db")

    @classmethod
    @st.cache_resource
    def get_collection(cls, collection: str):
        database = cls.get_database()
        return database.get_collection(collection)

    @classmethod
    @st.cache_data(ttl=600)
    def get_scores(cls) -> dict:
        collection = cls.get_collection("scores")
        documents = list(collection.find())

        scores = {
            document.get("claan"): document.get("score")
            for document in [
                document
                for document in documents
                if "claan" in document and "score" in document
            ]
            if document.get("claan").upper() in [claan.name for claan in Claans]
        }

        return scores
    
    @classmethod
    def update_score(cls, record: Record) -> bool:
        

        return False

    @classmethod
    def purge_scores(cls):
        collection = cls.get_collection("scores")
        scores = cls.get_scores()

        for claan in Claans:
            if claan.name in scores:
                collection.delete_one({"claan": claan.name})

        cls.get_scores.clear()
        st.session_state["scores"] = cls.get_scores()

    @classmethod
    def populate_scores(cls):
        collection = cls.get_collection("scores")
        scores = cls.get_scores()

        for claan in Claans:
            if claan.name not in scores:
                collection.insert_one({"claan": claan.name, "score": 0})

        cls.get_scores.clear()
        st.session_state["scores"] = cls.get_scores()

    @classmethod
    def randomize_scores(cls):
        collection = cls.get_collection("scores")
        scores = cls.get_scores()

        for claan in Claans:
            if claan.name in scores:
                collection.update_one(
                    filter={"claan": claan.name},
                    update={"$set": {"score": random.randint(1, 999)}},
                )

        cls.get_scores.clear()
        st.session_state["scores"] = cls.get_scores()

    @classmethod
    @st.cache_data(ttl=600)
    def get_quests(cls, claan: Claans = None) -> list[dict]:
        collection = cls.get_collection("quests")
        documents = list(collection.find())

        quests = [
            {
                "claan": document.get("claan"),
                "user": document.get("user"),
                "quest_id": document.get("quest_id"),
                "date": document.get("date"),
            }
            for document in documents
        ]

        if claan is not None:
            quests = [quest for quest in quests if quest.get("claan") == claan.name]

        return quests

    @classmethod
    def purge_quests(cls):
        collection = cls.get_collection("quests")

        collection.delete_many({})

        cls.get_quests.clear()
        st.session_state["quests"] = cls.get_quests()

    @classmethod
    def submit_record(cls, record: Record):
        pass
