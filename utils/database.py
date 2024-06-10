import random

import pymongo
import pymongo.collection
import pymongo.database
import streamlit as st
from faker import Faker

from .claans import Claans
from .record import Dice, Record, RecordType


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
    def get_database(cls, database: str) -> pymongo.database.Database:
        client = cls.get_client()
        return client.get_database(database)

    @classmethod
    @st.cache_resource
    def get_collection(cls, collection: str) -> pymongo.collection.Collection:
        database = cls.get_database("claans-db")
        return database.get_collection(collection)

    @classmethod
    @st.cache_data(ttl=600)
    def get_scores(cls) -> dict:
        scores = cls.get_collection("scores")

        return list(scores.find())

    @classmethod
    @st.cache_data(ttl=600)
    def get_quest_log(cls, claan: Claans = None, fortnight: bool = False) -> list[dict]:
        quest_log = cls.get_collection("quest_log")

        if claan is None:
            return list(quest_log.find())
        elif not fortnight:
            return list(quest_log.find({"claan": claan.name}))
        else:
            return list(quest_log.find({"claan": claan.name, "timestamp": {"$gt": ""}}))

    @classmethod
    @st.cache_data(ttl=86400)  # 24 hours
    def get_users(cls, claan: Claans = None) -> dict:
        users = cls.get_collection("users")

        if claan is None:
            return list(users.find())
        else:
            return list(users.find({"user_claan": claan.name}))

    @classmethod
    def update_scores(cls, record: Record) -> None:
        scores = cls.get_collection("scores")
        _ = cls.get_scores()  # This helps reduce full page reruns

        scores.find_one_and_update(
            filter={"claan": record.claan.name},
            update={"$inc": {"score": record.score}},
        )

        cls.get_scores.clear()
        st.session_state["scores"] = cls.get_scores()

    @classmethod
    def submit_quest(cls, record: Record) -> None:
        quest_log = cls.get_collection("quest_log")
        _ = cls.get_quest_log()

        quest_log.insert_one(record.as_dict())
        cls.update_scores(record)

        cls.get_quest_log.clear()
        st.session_state["quest_log"] = cls.get_quest_log()

    @classmethod
    def submit_quest_random(cls) -> None:
        record = Record(
            user="",
            claan=random.choice(list(Claans)),
            type=RecordType.QUEST,
            dice=random.choice(list(Dice)),
        )

        users = cls.get_users(record.claan)
        record.user = random.choice(users).get("user_name")

        cls.submit_quest(record)

    @classmethod
    def submit_user(cls) -> None:
        users = cls.get_collection("users")
        _ = cls.get_users()

        if (
            "user_name" not in st.session_state
            or "user_claan" not in st.session_state
            or st.session_state.get("user_name") == ""
        ):
            st.error("Error submitting user")
            return

        duplicate_check = (
            users.count_documents(
                {
                    "user_name": {"$eq": st.session_state["user_name"]},
                    "user_claan": {"$eq": st.session_state["user_claan"].name},
                }
            )
            == 0
        )

        if (
            users.count_documents(
                {
                    "user_name": {"$eq": st.session_state["user_name"]},
                    "user_claan": {"$eq": st.session_state["user_claan"].name},
                }
            )
            == 0
        ):
            users.insert_one(
                {
                    "user_name": st.session_state["user_name"],
                    "user_claan": st.session_state["user_claan"].name,
                }
            )
        else:
            st.error("User already exists")

        cls.get_users.clear()
        st.session_state["users"] = cls.get_users()

    @classmethod
    def submit_user_random(cls) -> bool:
        st.session_state["user_name"] = Faker().name()
        st.session_state["user_claan"] = random.choice(list(Claans))

        cls.submit_user()

    @classmethod
    def purge(cls) -> None:
        quest_log = cls.get_collection("quest_log")
        scores = cls.get_collection("scores")
        users = cls.get_collection("users")

        # Required to reduce full page reruns, unclear why
        _ = cls.get_scores()
        _ = cls.get_quest_log()
        _ = cls.get_users()

        quest_log.delete_many({})
        scores.delete_many({})
        users.delete_many({})

        for claan in Claans:
            scores.insert_one(
                {
                    "claan": claan.name,
                    "score": 0,
                }
            )

        cls.get_scores.clear()
        cls.get_quest_log.clear()
        cls.get_users.clear()

        st.session_state["scores"] = cls.get_scores()
        st.session_state["quest_log"] = cls.get_quest_log()
        st.session_state["users"] = cls.get_users()
