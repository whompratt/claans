from datetime import date, timedelta
from math import floor
from typing import Dict, Optional

import streamlit as st
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from src.models.season import Season


@st.cache_data(ttl=timedelta(weeks=2))
def get_season_start(_session: Session) -> date:
    query = select(func.max(Season.start_date))
    result = _session.execute(query).scalar_one()

    return result


# TODO: Docstring
@st.cache_data(ttl=timedelta(days=1))
def get_fortnight_number(
    _session: Session,
    timestamp: Optional[date] = None,
    season_start: Optional[date] = None,
) -> int:
    """Returns the integer representation of the current fortnight for the active season.

    :param _session: An optional instance of :class:`sqlalchemy.engine.base.Engine`.
    :param timestamp: An optional instance of :class:`datetime.date`, otherwise today will be used.
        .. note:: If no engine is provided, :meth:get_database_engine will be called with default parameters.
    :return: :class:`Tuple[date, int]` representation of the start date of the current season, and the number for current fortnight for this season, indexed to zero.
    """
    if timestamp is None:
        timestamp = date.today()

    if season_start is None:
        season_start = get_season_start(_session=_session)

    fortnight_number = floor((timestamp - season_start).days / 14)
    return fortnight_number


@st.cache_data(ttl=timedelta(days=1))
def get_fortnight_start(
    _session: Session,
    timestamp: Optional[date] = None,
    season_start: Optional[date] = None,
    fortnight_number: Optional[int] = None,
) -> date:
    if timestamp is None:
        timestamp = date.today()
    if season_start is None:
        season_start = get_season_start(_session=_session)
    if fortnight_number is None:
        fortnight_number = get_fortnight_number(
            _session=_session, timestamp=timestamp, season_start=season_start
        )

    fortnight_start = season_start + timedelta(weeks=(fortnight_number * 2))

    return fortnight_start


@st.cache_data(ttl=timedelta(days=1))
def get_fortnight_info(_session: Session) -> Dict[str, int | date]:
    """Returns a dict containing fortnight information.

    Dict contains fortnight number, start date, end date.
    """
    season_start = get_season_start(_session=_session)
    fortnight_number = get_fortnight_number(
        _session=_session, season_start=season_start
    )
    start_date = get_fortnight_start(
        _session=_session, season_start=season_start, fortnight_number=fortnight_number
    )
    end_date = start_date + timedelta(weeks=2)

    return {
        "fortnight_number": fortnight_number,
        "start_date": start_date,
        "end_date": end_date,
    }
