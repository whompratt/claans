from itertools import cycle
from typing import Any, Dict

import pandas as pd
from sqlalchemy import select
from sqlalchemy.exc import MultipleResultsFound, NoResultFound
from sqlalchemy.orm import Session

from src.models.claan import Claan
from src.models.user import User


def generate_targets(session: Session) -> Dict[int, Dict[str, Any]]:
    """Generates the target list for a game of Murder.

    Output is formatted as a dictionary or dictionaries, where the top level key is the agent's user id.
    The top level value dictionary contains the target's user id, task to be completed, etc.
    """
    attendees = pd.read_csv("./temp/attendees.csv")

    all_users = []

    for id, attendee in attendees.iterrows():
        try:
            search = f"%{attendee["First Name"]}%"
            query = select(User).where(User.name.like(search))
            result = session.execute(query.where(User.name.like(search))).scalar_one()
            all_users.append(result)
        except MultipleResultsFound:
            try:
                search = f"%{attendee["First Name"]} {attendee["Last Name"][0]}%"
                query = select(User).where(User.name.like(search))
                result = session.execute(
                    query.where(User.name.like(search))
                ).scalar_one()
                all_users.append(result)
            except MultipleResultsFound:
                print(
                    f"Attemped last initial search but multiple results found for {search}"
                )
            except NoResultFound:
                print(f"No result found for last initial search {search}")
        except NoResultFound:
            print(f"No result found for input {search}")

    users = {
        Claan.EARTH_STRIDERS: [],
        Claan.FIRE_DANCERS: [],
        Claan.THUNDER_WALKERS: [],
        Claan.WAVE_RIDERS: [],
    }

    for user in all_users:
        users[user.claan].append(user)

    claans = cycle(
        [
            Claan.EARTH_STRIDERS,
            Claan.FIRE_DANCERS,
            Claan.THUNDER_WALKERS,
            Claan.WAVE_RIDERS,
        ]
    )

    next_claan = next(claans)
    this_user = users[next_claan].pop()
    first_user = this_user

    targets = {}

    while True:
        next_claan = next(claans)

        if len(users[next_claan]) > 0:
            next_user = users[next_claan].pop()
        else:
            next_claan = next(claans)
            if len(users[next_claan]) > 0:
                next_user = users[next_claan].pop()
            else:
                next_claan = next(claans)
                if len(users[next_claan]) > 0:
                    next_user = users[next_claan].pop()
                else:
                    targets[this_user.id] = {"target": first_user.id, "task": None}
                    break

        targets[this_user.id] = {"target": next_user.id, "task": None}
        this_user = next_user

    return targets
