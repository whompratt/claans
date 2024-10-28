from datetime import datetime
from decimal import Decimal, FloatOperation, getcontext
from typing import Any, Dict, List

import streamlit as st
from sqlalchemy import func, select, update
from sqlalchemy.exc import NoResultFound
from sqlalchemy.orm import Session

from src.models.claan import Claan
from src.models.market.company import Company
from src.models.market.instrument import Instrument
from src.models.market.portfolio import BoardVote, Portfolio
from src.models.market.share import Share
from src.models.market.transaction import Operation, Transaction
from src.models.record import Record
from src.models.task import Task
from src.models.user import User
from src.utils.data.seasons import get_fortnight_start
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

    escrow_query = (
        select(func.sum(Record.score))
        .where(Record.claan == company.claan)
        .where(Record.escrow)
    )
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
def get_owned_shares(
    _session: Session, claan: Claan
) -> Dict[int, Dict[Claan, Dict[str, Any]]]:
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

    shares_query = (
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

    shares = _session.execute(shares_query).all()

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
        ) in [row.tuple() for row in shares]
    }

    instruments_query = (
        select(Instrument.id, Company.claan, Instrument.price, Instrument.ticker)
        .select_from(Instrument)
        .join(Company)
    )
    instruments = _session.execute(instruments_query).all()

    for _, data in result.items():
        for claan in data:
            data[claan]["price"] = [
                instrument.tuple()[2]
                for instrument in instruments
                if instrument.tuple()[1] == claan
            ][0]
            data[claan]["ticker"] = [
                instrument.tuple()[3]
                for instrument in instruments
                if instrument.tuple()[1] == claan
            ]

    return result


def issue_company_share(_session: Session, instrument: Instrument) -> None:
    amount_to_issue = st.session_state["issue_amount"]

    new_shares = []
    for _ in range(0, amount_to_issue):
        new_shares.append(Share(instrument=instrument.id, owner=None))

    _session.add_all(new_shares)

    if not _session.in_nested_transaction():
        _session.commit()
    else:
        _session.flush()


def delete_unowned_company_share(_session: Session, instrument: Instrument) -> None:
    """Delete a single, unowned share for a company.

    Will raise an exception if there are now owned shares.
    """
    share_query = (
        select(Share)
        .where(Share.instrument_id == instrument.id)
        .where(Share.owner.is_(None))
        .limit(1)
    )
    share = _session.execute(share_query).scalar_one()

    _session.delete(share)

    if not _session.in_nested_transaction():
        _session.commit()


def grant_share_to_user(_session: Session, portfolio: Portfolio) -> None:
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


def get_all_shares(_session: Session) -> List[Share]:
    shares_query = select(Share)
    shares = _session.execute(shares_query).scalars().all()

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


def buy_share(_session: Session, portfolio: Portfolio, instrument: Instrument) -> None:
    with _session.begin_nested() as nested:
        LOGGER.info("--- User Purchasing Share ---")
        LOGGER.info(f"\tUser: {portfolio.user.name}")
        LOGGER.info(f"\tCash: ${portfolio.cash}")
        LOGGER.info(f"\tShare: 1x {instrument.ticker} @ {instrument.price}")

        fortnight_start = get_fortnight_start(_session=_session)
        sold_already_query = (
            select(func.count(Transaction.id))
            .where(Transaction.timestamp >= fortnight_start)
            .where(Transaction.portfolio_id == portfolio.id)
            .where(Transaction.instrument_id == instrument.id)
            .where(Transaction.operation == Operation.SELL)
        )
        sold_already = _session.execute(sold_already_query).scalar_one() != 0

        if sold_already:
            LOGGER.warning(
                f"User {portfolio.user.name} attempted to buy shares having already sold them this fortnight."
            )
            st.error(
                "You've already sold shares in this company, so you can't buy more until next fortnight."
            )
            return

        owned_count = len(
            [share for share in portfolio.shares if share.instrument == instrument]
        )

        if owned_count >= 5:
            LOGGER.warning(
                f"User {portfolio.user.name} attempted to buy shares in a company when they already own 5."
            )
            st.error("Can't own more than 5 shares of a single Company")
            return

        if instrument.price > portfolio.cash:
            LOGGER.warning(
                f"User {portfolio.user.name} attempted to buy a share they can't afford (cash: ${portfolio.cash}, price: ${instrument.price})"
            )
            st.error("You don't have enough cash to buy that!")
            return

        share_ipo_query = (
            select(Share)
            .where(Share.instrument == instrument)
            .where(Share.ipo)
            .where(Share.owner_id.is_(None))
            .limit(1)
        )

        try:
            share = _session.execute(share_ipo_query).scalar_one()
        except NoResultFound:
            LOGGER.info("No shares found in IPO, will check non-IPO shares.")
            share_query = (
                select(Share)
                .where(Share.instrument == instrument)
                .where(Share.owner_id.is_(None))
            )
            try:
                share = _session.execute(share_query).scalar_one()
            except NoResultFound:
                LOGGER.warning(
                    f"User {portfolio.user.name} attempted to buy share but none left to buy."
                )
                st.error("No shares left to buy!")

        LOGGER.info(
            f"User {portfolio.user.name} buying {instrument.ticker}, successful. Saving..."
        )
        _session.add(
            Transaction(
                value=instrument.price,
                operation=Operation.BUY,
                instrument=instrument,
                portfolio=portfolio,
                company=None,
                timestamp=datetime.now(),
            )
        )
        share.owner_id = portfolio.id
        portfolio.cash -= instrument.price

        nested.commit()

    get_portfolio.clear(user_id=portfolio.user_id)
    if f"portfolios_{portfolio.company.claan.name}" in st.session_state:
        LOGGER.info(f"Refreshing portfolios for {portfolio.company.claan.value}")
        st.session_state[f"portfolios_{portfolio.company.claan.name}"][
            portfolio.user_id
        ] = get_portfolio(_session=_session, user_id=portfolio.user_id)

    get_owned_shares(claan=portfolio.user.claan)
    if f"owned_shares_{portfolio.user.claan.name}" in st.session_state:
        LOGGER.info(f"Refreshing owned shares for {portfolio.user.claan.value}")
        st.session_state[f"owned_shares_{portfolio.user.claan.name}"] = {
            portfolio_id: {
                claan: {key: value for key, value in data.items()}
                for claan, data in data.items()
            }
            for portfolio_id, data in get_owned_shares(
                _session=_session, claan=portfolio.user.claan
            ).items()
        }

    _session.commit()


def sell_share(_session: Session, portfolio: Portfolio, instrument: Instrument) -> None:
    """Sell 1 share of the given instrument from the given portfolio."""
    with _session.begin_nested() as nested:
        LOGGER.info("--- User Selling Share ---")
        LOGGER.info(f"\tUser: {portfolio.user.name}")
        LOGGER.info(f"\tShare: 1x {instrument.ticker} @ {instrument.price}")

        owned_share_query = (
            select(Share)
            .where(Share.instrument_id == instrument.id)
            .where(Share.owner_id == portfolio.id)
            .limit(1)
        )
        try:
            owned_share = _session.execute(owned_share_query).scalar_one()
        except NoResultFound:
            LOGGER.warning(
                f"User {portfolio.user.name} attempted to sell a share they don't own."
            )
            st.error("You don't any shares of this company to sell.")
            return

        owned_share.owner_id = None
        portfolio.cash += instrument.price
        instrument.price -= float(1)

        nested.commit()

    get_portfolio.clear(user_id=portfolio.user_id)
    if f"portfolios_{portfolio.company.claan.name}" in st.session_state:
        LOGGER.info(f"Refreshing portfolios for {portfolio.company.claan.value}")
        st.session_state[f"portfolios_{portfolio.company.claan.name}"][
            portfolio.user_id
        ] = get_portfolio(_session=_session, user_id=portfolio.user_id)

    get_owned_shares(claan=portfolio.user.claan)
    if f"owned_shares_{portfolio.user.claan.name}" in st.session_state:
        LOGGER.info(f"Refreshing owned shares for {portfolio.user.claan.value}")
        st.session_state[f"owned_shares_{portfolio.user.claan.name}"] = {
            portfolio_id: {
                claan: {key: value for key, value in data.items()}
                for claan, data in data.items()
            }
            for portfolio_id, data in get_owned_shares(
                _session=_session, claan=portfolio.user.claan
            ).items()
        }

    _session.commit()


def get_instruments(_session: Session) -> List[Instrument]:
    instruments_query = select(Instrument)
    instruments = _session.execute(instruments_query).scalars().all()

    return instruments


def process_escrow(_session: Session) -> None:
    from src.utils.data.scores import get_scores

    companies_query = select(Company)
    companies = _session.execute(companies_query).scalars().all()

    for company in companies:
        LOGGER.info(f"Processing escrow for {company.claan.value.title()}")
        votes_query = (
            select(
                Portfolio.board_vote.label("vote"),
                func.count(Portfolio.id).label("count"),
            )
            .where(Portfolio.company_id == company.id)
            .group_by(Portfolio.board_vote)
        )
        votes = _session.execute(votes_query).all()
        users_query = select(User).where(User.claan == company.claan)
        users = _session.execute(users_query).scalars().all()

        results = {vote_type: 0 for vote_type in BoardVote}

        for vote in votes:
            (vote_type, count) = vote._tuple()
            results[vote_type] = count

        LOGGER.info(
            f"{company.claan.name} votes:\n\tPayout: {results[BoardVote.PAYOUT]}\n\tWithhold: {results[BoardVote.WITHOLD]}"
        )
        if results[BoardVote.PAYOUT] >= results[BoardVote.WITHOLD]:
            payout(_session, company)
        else:
            withold(_session, company)

        LOGGER.info("Clearing relevant function caches and reloading data")

        get_scores.clear()
        if "scores" in st.session_state:
            st.session_state["scores"] = get_scores(_session=_session)

        get_corporate_data.clear(claan=company.claan)
        if f"data_{company.claan.name}" in st.session_state:
            st.session_state[f"data_{company.claan.name}"] = get_corporate_data(
                _session=_session, claan=company.claan
            )

        for user in users:
            get_portfolio.clear(user_id=user.id)
        if f"porfolios_{company.claan.name}" in st.session_state:
            st.session_state[f"portfolios_{company.claan.name}"] = {
                user.id: get_portfolio(_session=_session, user_id=user.id)
                for user in users
            }

        get_owned_shares.clear(claan=company.claan)
        if f"owned_shares_{company.claan.name}" in st.session_state:
            st.session_state[f"owned_shares_{company.claan.name}"] = {
                portfolio_id: {
                    claan: {key: value for key, value in data.items()}
                    for claan, data in data.items()
                }
                for portfolio_id, data in get_owned_shares(
                    _session=_session, claan=company.claan
                ).items()
            }

        _session.commit()


def payout(_session: Session, company: Company) -> None:
    decimal_context = getcontext()
    decimal_context.prec = 28  # if result of round would require higher precision than this to represent, then exception is raised, hence high value
    decimal_context.traps[FloatOperation] = True

    LOGGER.info(f"--- {company.claan.name}: PAYOUT ---")

    with _session.begin_nested() as nested:
        instrument_query = select(Instrument).where(Instrument.company_id == company.id)
        instrument = _session.execute(instrument_query).scalar_one()
        records_query = (
            select(Record).where(Record.claan == company.claan).where(Record.escrow)
        )
        records = _session.execute(records_query).scalars().all()

        amount_in_escrow = sum([Decimal(record.score) for record in records])

        shares_query = (
            select(Share)
            .join(Instrument)
            .join(Company)
            .where(Company.claan == company.claan)
        )
        shares = _session.execute(shares_query).scalars().all()

        total_share_count = Decimal(len(shares))
        ipo_share_count = Decimal(len([share for share in shares if share.ipo]))

        cash_per_share = round(amount_in_escrow / total_share_count, 2)
        cash_to_company = round(cash_per_share * ipo_share_count, 2)

        LOGGER.info(f"Total share count: {total_share_count}")
        LOGGER.info(f"Shares in IPO: {ipo_share_count}")
        LOGGER.info(f"Cash per share: ${cash_per_share}")
        LOGGER.info(f"Cash to company: ${cash_to_company}")

        owned_shares_query = (
            select(Portfolio, func.count(Share.owner_id))
            .select_from(Share)
            .join(Instrument, Instrument.id == Share.instrument_id)
            .join(Company, onclause=Company.id == Instrument.company_id)
            .join(Portfolio, onclause=Portfolio.id == Share.owner_id)
            .where(Instrument.company == company)
            .group_by(Portfolio)
        )
        owned_shares = _session.execute(owned_shares_query).all()

        ##-- Perform data updates --##
        new_transactions = []

        LOGGER.info("Adding shareholder dividend transactions...")
        for row in owned_shares:
            (portfolio, owned_count) = row.tuple()
            new_transactions.append(
                Transaction(
                    value=float(cash_per_share * owned_count),
                    operation=Operation.CREDIT,
                    instrument=None,
                    portfolio=portfolio,
                    company=None,
                    timestamp=None,
                )
            )
            portfolio.cash += float(cash_per_share * owned_count)
            _session.flush()

        LOGGER.info("Adding Claan vault transaction...")
        new_transactions.append(
            Transaction(
                value=float(cash_to_company),
                operation=Operation.CREDIT,
                instrument=None,
                timestamp=None,
                company=company,
                portfolio=None,
            )
        )
        company.cash += float(cash_to_company)
        _session.add_all(new_transactions)
        _session.flush()

        LOGGER.info("Emptying escrow...")
        update_records_query = (
            update(Record)
            .where(Record.claan == company.claan)
            .where(Record.escrow)
            .values(escrow=False)
        )
        _session.execute(update_records_query)
        _session.flush()

        if float(cash_per_share) >= instrument.price:
            LOGGER.info("Payout high enough, increasing share price...")
            instrument.price += 10
            _session.flush()

        print("")


def withold(_session: Session, company: Company) -> None:
    decimal_context = getcontext()
    decimal_context.prec = 28  # if result of round would require higher precision than this to represent, then exception is raised, hence high value
    decimal_context.traps[FloatOperation] = True

    LOGGER.info(f"--- {company.claan.name}: WITHHOLD ---")

    with _session.begin_nested() as nested:
        instrument_query = select(Instrument).where(Instrument.company_id == company.id)
        instrument = _session.execute(instrument_query).scalar_one()

        records_query = (
            select(Record).where(Record.claan == company.claan).where(Record.escrow)
        )
        records = _session.execute(records_query).scalars().all()
        amount_in_escrow = sum([Decimal(record.score) for record in records])
        LOGGER.info(f"Amount in escrow: {amount_in_escrow}")

        LOGGER.info("Adding Claan vault transaction")
        _session.add(
            Transaction(
                value=float(amount_in_escrow),
                operation=Operation.CREDIT,
                instrument=None,
                timestamp=None,
                company=company,
                portfolio=None,
            )
        )
        company.cash += float(amount_in_escrow)
        _session.flush()

        LOGGER.info("Decreasing share price...")
        instrument.price -= 10
        if instrument.price < 10:
            instrument.price = 10
        _session.flush()

        LOGGER.info("Emptying escrow...")
        update_records_query = (
            update(Record)
            .where(Record.claan == company.claan)
            .where(Record.escrow)
            .values(escrow=False)
        )
        _session.execute(update_records_query)
        _session.flush()

        print("")
