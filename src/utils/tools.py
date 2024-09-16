## Load data
import json
import random
from typing import List, Tuple

from sqlalchemy import Row, desc, func, select

from src.models.claan import Claan
from src.models.record import Record
from src.models.user import User
from src.utils import data
from src.utils.database import Database

with Database.get_session() as session:
    pass
    season_start = data.get_season_start(session)
    query = (
        select(User.name, Record.user_id, func.sum(Record.score).label("score"))
        .select_from(Record)
        .join(User)
        .where(Record.timestamp >= season_start)
        .where(User.active)
        .group_by(Record.user_id, User.name)
        .order_by(desc("score"))
    )
    users = session.execute(query).all()

    groups: List[Tuple[Row[Tuple[str, int, int]]]] = []
    for i in range(0, len(users), 6):
        groups.append(tuple(users[i : i + 6]))

    result = {}
    for claan in list(Claan):
        result[claan.name] = {}
    for group in groups:
        claans = list(Claan)
        for user in group:
            result[claans.pop(claans.index(random.choice(claans))).name][
                user.user_id
            ] = user.name

    with open("new_claans.json", "w") as f:
        f.write(json.dumps(result, indent=2))
