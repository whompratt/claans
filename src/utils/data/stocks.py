from typing import Dict, List

import streamlit as st
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from src.models.claan import Claan
from src.models.market.company import Company
from src.models.market.instrument import Instrument
from src.models.market.portfolio import BoardVote, Portfolio
from src.models.market.share import Share
from src.models.market.transaction import Transaction
from src.models.record import Record
from src.models.task import Task
from src.utils.logger import LOGGER


class ShareAlreadyOwnedError(Exception):
    pass


class ShareNotOwnedError(Exception):
    pass


class CannotAffordError(Exception):
    pass


@st.cache_data(ttl=600)
def get_portfolio(_session: Session, user_id: int) -> Portfolio:
    portfolio_query = select(Portfolio).where(Portfolio.user_id == user_id)
    portfolio = _session.execute(portfolio_query).scalars().one()

    return portfolio


def update_vote(_session: Session, _portfolio: Portfolio, _claan: Claan) -> None:
    portfolio = _session.get(Portfolio, _portfolio.id)
    portfolio.board_vote = st.session_state["portfolio_vote"]
    _session.commit()
    st.toast("Vote updated")

    get_portfolio.clear(user_id=_portfolio.user_id)
    st.session_state[f"portfolios_{_claan.name}"][_portfolio.user_id] = get_portfolio(
        _session=_session, user_id=_portfolio.user_id
    )


@st.cache_data(ttl=600)
def get_corporate_data(_session: Session, claan: Claan) -> Dict[str, float]:
    company_query = select(Company).where(Company.claan == claan)
    company = _session.execute(company_query).scalar_one()

    instrument_query = select(Instrument.price).where(
        Instrument.company_id == company.id
    )
    instrument = _session.execute(instrument_query).scalar_one()

    funds_query = (
        select(func.sum(Transaction.value))
        .select_from(Transaction)
        .where(Transaction.company_id == company.id)
    )
    funds = _session.execute(funds_query).scalar_one()

    escrow_query = select(func.sum(Record.score)).where(Record.claan == company.claan)
    escrow = _session.execute(escrow_query).scalar_one()

    quests_query = (
        select(func.count())
        .select_from(Record)
        .join(Task)
        .where(Record.claan == company.claan)
    )
    quests = _session.execute(quests_query).scalar_one()

    return {
        "instrument": instrument,
        "funds": funds,
        "escrow": escrow,
        "task_count": quests,
    }


@st.cache_data(ttl=600)
def get_owned_shares(_session: Session, claan: Claan) -> Dict[int, Dict[Claan, int]]:
    sq_earth = (
        select(Share.owner_id)
        .join(Instrument)
        .join(Company)
        .where(Company.claan == Claan.EARTH_STRIDERS)
    ).subquery()
    sq_fire = (
        select(Share.owner_id)
        .join(Instrument)
        .join(Company)
        .where(Company.claan == Claan.FIRE_DANCERS)
    ).subquery()
    sq_thunder = (
        select(Share.owner_id)
        .join(Instrument)
        .join(Company)
        .where(Company.claan == Claan.THUNDER_WALKERS)
    ).subquery()
    sq_wave = (
        select(Share.owner_id)
        .join(Instrument)
        .join(Company)
        .where(Company.claan == Claan.WAVE_RIDERS)
    ).subquery()
    sq_beast = (
        select(Share.owner_id)
        .join(Instrument)
        .join(Company)
        .where(Company.claan == Claan.BEAST_RUNNERS)
    ).subquery()
    sq_iron = (
        select(Share.owner_id)
        .join(Instrument)
        .join(Company)
        .where(Company.claan == Claan.IRON_STALKERS)
    ).subquery()

    query = (
        select(
            Portfolio.id.label("portfolio"),
            func.count(sq_earth.c.owner_id).label("count_earth"),
            func.count(sq_fire.c.owner_id).label("count_fire"),
            func.count(sq_thunder.c.owner_id).label("count_thunder"),
            func.count(sq_wave.c.owner_id).label("count_wave"),
            func.count(sq_beast.c.owner_id).label("count_beast"),
            func.count(sq_iron.c.owner_id).label("count_iron"),
        )
        .select_from(Portfolio)
        .join(Company, onclause=Portfolio.company_id == Company.id)
        .join(
            sq_earth,
            onclause=Portfolio.id == sq_earth.c.owner_id,
            isouter=True,
        )
        .join(
            sq_fire,
            onclause=Portfolio.id == sq_fire.c.owner_id,
            isouter=True,
        )
        .join(
            sq_thunder,
            onclause=Portfolio.id == sq_thunder.c.owner_id,
            isouter=True,
        )
        .join(
            sq_wave,
            onclause=Portfolio.id == sq_wave.c.owner_id,
            isouter=True,
        )
        .join(
            sq_beast,
            onclause=Portfolio.id == sq_beast.c.owner_id,
            isouter=True,
        )
        .join(
            sq_iron,
            onclause=Portfolio.id == sq_iron.c.owner_id,
            isouter=True,
        )
        .group_by(
            Portfolio.id,
        )
        .where(Company.claan == claan)
    )

    response = _session.execute(query).all()
    result = {
        portfolio_id: {
            Claan.EARTH_STRIDERS: {
                "count": count_earth,
            },
            Claan.FIRE_DANCERS: {
                "count": count_fire,
            },
            Claan.THUNDER_WALKERS: {
                "count": count_thunder,
            },
            Claan.WAVE_RIDERS: {
                "count": count_wave,
            },
            Claan.BEAST_RUNNERS: {
                "count": count_beast,
            },
            Claan.IRON_STALKERS: {
                "count": count_iron,
            },
        }
        for (
            portfolio_id,
            count_earth,
            count_fire,
            count_thunder,
            count_wave,
            count_beast,
            count_iron,
        ) in [row.tuple() for row in response]
    }

    return result


def issue_share(_session: Session, portfolio: Portfolio) -> None:
    instrument_query = (
        select(Instrument)
        .join(Company)
        .join(Portfolio)
        .where(Portfolio.id == portfolio.id)
    )
    instrument = _session.execute(instrument_query).scalar_one()

    share_query = (
        select(Share)
        .where(Share.owner_id.is_(None))
        .where(Share.instrument_id == instrument.id)
    )
    share = _session.execute(share_query).scalars().first()

    share.owner_id = portfolio.id
    share.ipo = False

    if not _session.in_nested_transaction():
        _session.commit()


@st.cache_data(ttl=600)
def get_shares_for_sale(_session: Session, instrument_id: int) -> List[Share]:
    share_query = (
        select(Share)
        .where(not Share.owner_id)
        .where(Share.instrument_id == instrument_id)
    )
    shares = _session.execute(share_query).scalars().all()

    return shares


@st.cache_data(ttl=600)
def get_ipo_count(_session: Session, claan: Claan) -> int:
    ipo_query = (
        select(func.count(Share.ipo))
        .select_from(Company)
        .join(Instrument)
        .join(Share)
        .where(Company.claan == claan)
        .where(Share.ipo)
    )
    ipo = _session.execute(ipo_query).scalar_one()

    return ipo


def buy_share(_session: Session, share: Share, portfolio: Portfolio) -> None:
    instrument_query = select(Instrument).where(Instrument.id == share.instrument_id)
    instrument = _session.execute(instrument_query).scalars().one()

    if share not in _session:
        share = _session.get(Share, share.id)

    if share.owner_id:
        raise ShareAlreadyOwnedError

    if portfolio not in _session:
        portfolio = _session.get(Portfolio, portfolio.id)

    if portfolio.cash < instrument.price:
        raise CannotAffordError

    # TODO: Check ownership limits
    # TODO: Check and deduct cash

    with _session.begin_nested():
        if instrument.ipo > 0:
            instrument.ipo -= 1

        share.owner_id = portfolio.id
        portfolio.cash -= instrument.price

    _session.commit()


def sell_share(_session: Session, share: Share, portfolio: Portfolio) -> None:
    instrument_query = select(Instrument).where(Instrument.id == share.instrument_id)
    instrument = _session.execute(instrument_query).scalars().one()

    if share not in _session:
        share = _session.get(Share, share.id)

    if share.owner_id != portfolio.id:
        raise ShareNotOwnedError

    if portfolio not in _session:
        portfolio = _session.get(Portfolio, portfolio.id)

    with _session.begin_nested():
        share.owner_id = None
        portfolio.cash += instrument.price

    _session.commit()


def process_escrow(_session: Session) -> None:
    companies_query = select(Company)
    companies = _session.execute(companies_query).scalars().all()

    for company in companies:
        portfolios_query = select(
            Portfolio.board_vote.label("vote"), func.count(Portfolio.id).label("count")
        ).group_by(Portfolio.board_vote)
        votes = _session.execute(portfolios_query).all()

        results = {vote_type: 0 for vote_type in BoardVote}

        for vote in votes:
            (vote_type, count) = vote._tuple()
            results[vote_type] = count

        if results[BoardVote.PAYOUT] >= results[BoardVote.WITHOLD]:
            payout(_session)
        else:
            withold(_session)


def payout(_session: Session) -> None:
    LOGGER.info("Board voted to payout")
    pass


def withold(_session: Session) -> None:
    LOGGER.info("Board voted to withold")
    pass
