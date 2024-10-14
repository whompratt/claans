from typing import Dict, List

import streamlit as st
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from src.models.base import Base
from src.models.claan import Claan
from src.models.market.company import Company
from src.models.market.instrument import Instrument
from src.models.market.portfolio import BoardVote, Portfolio
from src.models.market.share import Share
from src.models.market.transaction import Transaction
from src.models.record import Record
from src.models.task import Task
from src.models.user import User
from src.utils.database import Database
from src.utils.logger import LOGGER


class ShareAlreadyOwnedError(Exception):
    pass


class ShareNotOwnedError(Exception):
    pass


class CannotAffordError(Exception):
    pass


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


@st.cache_data(ttl=600)
def get_corporate_data(_session: Session, claan: Claan) -> Dict[str, float]:
    company_query = select(Company).where(Company.claan == claan)
    company = _session.execute(company_query).scalar_one()

    funds_query = (
        select(func.sum(Transaction.value))
        .select_from(Transaction)
        .where(Transaction.company_id == company.id)
    )
    funds = _session.execute(funds_query).scalar_one()

    escrow_query = select(func.sum(Record.score)).where(Record.claan == company.claan)
    escrow = _session.execute(escrow_query).scalar_one()

    quests_query = select(func.count()).select_from(Record).join(Task)
    quests = _session.execute(quests_query).scalar_one()

    return {
        "funds": funds,
        "escrow": escrow,
        "task_count": quests,
    }


def get_shares_for_sale(_session: Session, instrument: Instrument) -> List[Share]:
    share_query = select(Share).where(not Share.owner_id)
    shares = _session.execute(share_query).scalars().all()

    return shares


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


def main():
    LOGGER.info("Initializing stock game...")

    ## Build tables
    from src.models.market import Company, Instrument, Portfolio, Share, Transaction

    _tables = [Company, Instrument, Portfolio, Share, Transaction]
    Base.metadata.create_all(bind=Database.get_engine())

    with Database.get_session() as session:
        ## Populate companies table
        with session.begin_nested() as transaction:
            LOGGER.info("Populating companies")

            companies_query = select(Company)
            companies = session.execute(companies_query).scalars().all()

            new_companies = []
            for claan in Claan:
                if claan not in [company.claan for company in companies]:
                    new_companies.append(Company(claan))
            session.add_all(new_companies)
            transaction.commit()

        ## Populate instruments table
        with session.begin_nested() as transaction:
            LOGGER.info("Populating instruments")

            companies_query = select(Company.id)
            companies = session.execute(companies_query).scalars().all()

            instruments_query = select(Instrument.company_id)
            instruments = session.execute(instruments_query).scalars().all()

            new_instruments = [
                Instrument(company)
                for company in companies
                if company not in instruments
            ]
            session.add_all(new_instruments)
            transaction.commit()

        ## Populate shares table
        with session.begin_nested() as transaction:
            LOGGER.info("Populating shares")

            instruments_query = select(Instrument)
            instruments = session.execute(instruments_query).scalars().all()

            new_shares = []
            for instrument in instruments:
                shares_query = (
                    select(func.count())
                    .select_from(Share)
                    .where(Share.instrument == instrument)
                )
                shares_count = session.execute(shares_query).scalar_one()

                for _ in range(0, 100 - shares_count):
                    new_shares.append(Share(instrument=instrument, owner=None))

            session.add_all(new_shares)
            transaction.commit()

        ## Populate portfolios table
        with session.begin_nested() as transaction:
            LOGGER.info("Populating portfolios")

            users_query = select(User)
            users = session.execute(users_query).scalars().all()

            new_portfolios = []
            for user in users:
                portfolio_query = select(Portfolio).where(Portfolio.user_id == user.id)
                portfolio = session.execute(portfolio_query).scalar_one_or_none()

                if not portfolio and user.claan:
                    company_query = select(Company).where(Company.claan == user.claan)
                    company = session.execute(company_query).scalar_one()

                    new_portfolios.append(Portfolio(user, company))

            session.add_all(new_portfolios)
            transaction.commit()

        ## Test Escrow Processing
        with session.begin_nested():
            LOGGER.info("Testing processing of escrow")
            process_escrow(_session=session)

        # ### Disabled currently as users will start with 0 dollars ###
        # ## Grant starting funds to users with no transactions
        # with session.begin_nested() as transaction:
        #     transaction_count_subquery = (
        #         select(
        #             Transaction.portfolio_id,
        #             func.count(Transaction.id).label("transactions"),
        #         )
        #         .group_by(Transaction.portfolio_id)
        #         .subquery()
        #     )
        #     transaction_count = aliased(
        #         Transaction, transaction_count_subquery, "transaction_count"
        #     )

        #     user_transactions_query = (
        #         select(Portfolio)
        #         .join(
        #             transaction_count,
        #             onclause=Portfolio.id == transaction_count.portfolio_id,
        #             isouter=True,
        #         )
        #         .where(transaction_count.transactions == 0)
        #     )
        #     user_transactions = session.execute(user_transactions_query).scalars().all()

        #     new_transactions = []
        #     for user in user_transactions:
        #         new_transactions.append(
        #             Transaction(
        #                 instrument=None,
        #                 operation=Operation.CREDIT,
        #                 value=50.0,
        #             )
        #         )
        #     session.add_all(new_transactions)
        #     transaction.commit()

        # ## Ensures all users that have no trades and no instrument are given two shares of their own claan
        # with session.begin_nested():
        #     LOGGER.info("Granting starting shares to new users")
        #     session.expire_on_commit = False

        #     trade_count_subquery = (
        #         select(
        #             MarketData.portfolio_id,
        #             func.count(MarketData.id).label("trade_count"),
        #         )
        #         .group_by(MarketData.portfolio_id)
        #         .order_by(MarketData.portfolio_id)
        #         .subquery()
        #     )
        #     trade_count_alias = aliased(MarketData, trade_count_subquery)

        #     query = (
        #         select()
        #         .select_from(trade_count_alias)
        #         .join(
        #             Portfolio, onclause=(Portfolio.id == trade_count_alias.portfolio_id)
        #         )
        #     )
        #     rows = session.execute(query).all()

        #     for row in rows:
        #         (portfolio, user, instrument, trade_count) = row.tuple()

        #         if trade_count == 0:
        #             LOGGER.info(
        #                 f"No trades defined for user {user}, adding starting shares"
        #             )
        #             MarketData.create(
        #                 instrument=instrument,
        #                 portfolio=portfolio,
        #                 price=10.0,
        #                 quantity=2,
        #                 timestamp=datetime.now(),
        #             )

        session.commit()


if __name__ == "__main__":
    main()
