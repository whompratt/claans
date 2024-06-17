from typing import List

import pymongo
import pymongo.collection
import pymongo.database
import streamlit as st

from .record import Record


class Database:
    """Handles direct interactions with the mongo database"""

    @classmethod
    @st.cache_resource
    def get_client(cls) -> pymongo.MongoClient:
        """
        Gets a pymongo.MongoClient.

        This function is cached in streamlit, meaning if this function was called previously with matching args the previously cached result will be returned.
        If no cached instance is found, a new one is created.

        Returns:
            pymongo.MongoClient object which can be used to interact with the mongo instance.

        Raises:
            pymongo.errors.ConnectionFailure: Client could not run command 'ping' against the mongo instance.
        """
        client: pymongo.MongoClient = pymongo.MongoClient(**st.secrets["mongo"])

        try:
            client.get_database("admin").command("ping")
        except pymongo.errors.ConnectionFailure as e:
            st.error("Fatal error: Mongo client cannot connect")
            st.exception(e)
        except Exception as e:
            st.error("Unknown error")
            st.exception(e)
        else:
            return client

    @classmethod
    @st.cache_resource
    def get_database(cls, database: str) -> pymongo.database.Database:
        """
        Returns a reference to the input mongo database.

        This function is cached in streamlit, meaning if this function was called previously with matching args the previously cached result will be returned.
        If no cached instance is found, a new one is created.
        If the target database does not already exist, a database object will still be returned.
        The database will then be created once data is written.

        Args:
            database: name of the target database.

        Returns:
            pymongo.database.Database object which can be used to interact with collections in the database.
        """
        client = cls.get_client()
        return client.get_database(database)

    @classmethod
    @st.cache_resource
    def get_collection(
        cls, collection: str, database: str = "claans-db"
    ) -> pymongo.collection.Collection:
        """
        Returns a refernce to the input database collection.

        This function is cached in streamlit, meaning if this function was called previously with matching args the previously cached result will be returned.
        If no cached instance is found, a new one is created.
        If the target collection and/or database don't already exist in mongo, then a reference will still be returned.
        The database and collection will then be created as required once data is written.

        Args:
            collection: name of the target collection.
            database (optional): name of the target database, defaults to 'claans-db'.

        Returns:
            pymongo.collection.Collection object which can be used to interact with documents in the collection.
        """
        database = cls.get_database(database)
        return database.get_collection(collection)

    @classmethod
    @st.cache_data(ttl=3600)
    def get_documents(
        cls, collection: str, filter: dict = {}, database: str = "claans-db"
    ) -> List[dict]:
        """
        Returns a documents from a collection as a list of dictionaries.

        This function is cached in streamlit, with a time to live set. This means that is this function was called with matching args in the last ttl seconds, return the cached result.
        If no cached result exists, or ttl has been exceeded, the collection will be queried again for its documents.
        Caching serves to reduce load on both the database and the platform, however given the nature of the data that could be stored (e.g. scores), there exists a risk the cache could be outdated.
        As such, whenever a function is called that modifies the contents of a collection, this function's cache _must_ be cleared.
        To clear all cached arg variations of this function, call get_documents.clear().
        Passing args into clear will clear the cache, but only for a run that matched those args.

        Args:
            collection: name of the target collection.
            filter (optional): dictionary defining the filter to apply, defaults to '{}' meaning all records.
            database (optional): name of the target database, defaults to 'claans-db'.

        Returns:
            List[dict] object where each dict is a document.
        """
        collection = cls.get_collection(collection, database)
        return list(collection.find(filter))

    @classmethod
    def submit_quest(cls, record: Record) -> bool:
        """
        Submits a new document to the `quest_log` collection recording the completion of a quest or activity.

        This function _inserts_ a new document, so no filter is performed against the collection in order to keep this class as streamlined as possible.
        As such, validation of whether a user should be able to submit this quest or activity should be performed before calling this function.

        Args:
            record: instance of class `Record` defining the data to submit.

        Returns:
            bool: True on successful submission.
        """
        quest_log = cls.get_collection("quest_log")
        _ = cls.get_documents(collection="quest_log")  # Prevents reloads

        result = quest_log.insert_one(record.as_dict())

        # TODO: Should this be an exception? Once we're in this state we're fucked.
        if result.acknowledged:
            if not cls.update_score(record):
                st.warning("Quest or activity submitted, but failed to update scores.")

        cls.get_documents.clear(collection="quest_log")
        st.session_state["quest_log"] = cls.get_documents(collection="quest_log")

        return result.acknowledged

    @classmethod
    def update_score(cls, record: Record) -> bool:
        """
        Updates an existing document in the `scores` collection, incrementing is value by some amount.

        Uses pymongo.collection.Collection's `find_one_and_update` to find an existing document and update its contents.
        If no existing document is found, no update will occur and this function will return false.

        Args:
            record: instance of class `Record` defining the data to submit.

        Returns:
            bool: True is record updated, False otherwise.
        """
        scores = cls.get_collection("scores")
        _ = cls.get_documents(collection="scores")  # Prevents reloads

        # Unclear, but find_one_and_update returns None if no document found, so any return is good.
        if scores.find_one_and_update(filter={"claan": record.claan.name}) is None:
            st.warning("Failed updating scores, no document matching given filter.")
            return False

        cls.get_documents.clear(collection="scores")
        st.session_state["scores"] = cls.get_documents(collection="scores")

        return True

    @classmethod
    # TODO
    def submit_user(cls) -> None:
        # TODO: When a user is submitted for a given claan, should all get_document queries be cleared from cache, or the no filter and this claan results?
        # i.e.
        # cls.get_document.clear()
        # or
        # cls.get_documents.clear(collection="users") AND cls.get_documents.clear(collection="users", filter={"claan": claan.name})
        st.error("Not yet implemented, sorry")
        pass


# class OldDatabase:
# @classmethod
# @st.cache_data(ttl=600)
# def get_scores(cls) -> dict:
#     scores = cls.get_collection("scores")

#     return list(scores.find())

# @classmethod
# @st.cache_data(ttl=600)
# def get_quest_log(cls, claan: Claans = None, fortnight: bool = False) -> list[dict]:
#     quest_log = cls.get_collection("quest_log")

#     if claan is None:
#         return list(quest_log.find())
#     elif not fortnight:
#         return list(quest_log.find({"claan": claan.name}))
#     else:
#         return list(quest_log.find({"claan": claan.name, "timestamp": {"$gt": ""}}))

# @classmethod
# @st.cache_data(ttl=86400)  # 24 hours
# def get_users(cls, claan: Claans = None) -> dict:
#     users = cls.get_collection("users")

#     if claan is None:
#         return list(users.find())
#     else:
#         return list(users.find({"user_claan": claan.name}))

# @classmethod
# def submit_quest(cls, record: Record) -> None:
#     quest_log = cls.get_collection("quest_log")
#     _ = cls.get_quest_log()

#     quest_log.insert_one(record.as_dict())
#     cls.update_scores(record)

#     cls.get_quest_log.clear()
#     st.session_state["quest_log"] = cls.get_quest_log()

# @classmethod
# def submit_quest_random(cls) -> None:
#     record = Record(
#         user="",
#         claan=random.choice(list(Claans)),
#         type=RecordType.QUEST,
#         dice=random.choice(list(Dice)),
#     )

#     users = cls.get_users(record.claan)
#     record.user = random.choice(users).get("user_name")

#     cls.submit_quest(record)

# @classmethod
# def submit_user(cls) -> None:
#     users = cls.get_collection("users")
#     _ = cls.get_users()

#     if (
#         "user_name" not in st.session_state
#         or "user_claan" not in st.session_state
#         or st.session_state.get("user_name") == ""
#     ):
#         st.error("Error submitting user")
#         return

#     duplicate_check = (
#         users.count_documents(
#             {
#                 "user_name": {"$eq": st.session_state["user_name"]},
#                 "user_claan": {"$eq": st.session_state["user_claan"].name},
#             }
#         )
#         == 0
#     )

#     if (
#         users.count_documents(
#             {
#                 "user_name": {"$eq": st.session_state["user_name"]},
#                 "user_claan": {"$eq": st.session_state["user_claan"].name},
#             }
#         )
#         == 0
#     ):
#         users.insert_one(
#             {
#                 "user_name": st.session_state["user_name"],
#                 "user_claan": st.session_state["user_claan"].name,
#             }
#         )
#     else:
#         st.error("User already exists")

#     cls.get_users.clear()
#     st.session_state["users"] = cls.get_users()

# @classmethod
# def submit_user_random(cls) -> bool:
#     st.session_state["user_name"] = Faker().name()
#     st.session_state["user_claan"] = random.choice(list(Claans))

#     cls.submit_user()

# @classmethod
# def purge(cls) -> None:
#     quest_log = cls.get_collection("quest_log")
#     scores = cls.get_collection("scores")
#     users = cls.get_collection("users")

#     # Required to reduce full page reruns, unclear why
#     _ = cls.get_scores()
#     _ = cls.get_quest_log()
#     _ = cls.get_users()

#     quest_log.delete_many({})
#     scores.delete_many({})
#     users.delete_many({})

#     for claan in Claans:
#         scores.insert_one(
#             {
#                 "claan": claan.name,
#                 "score": 0,
#             }
#         )

#     cls.get_scores.clear()
#     cls.get_quest_log.clear()
#     cls.get_users.clear()

#     st.session_state["scores"] = cls.get_scores()
#     st.session_state["quest_log"] = cls.get_quest_log()
#     st.session_state["users"] = cls.get_users()
