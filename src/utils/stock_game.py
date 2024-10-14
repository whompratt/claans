from sqlalchemy import func, select

from src.models.base import Base
from src.models.claan import Claan
from src.models.user import User
from src.utils.data.stocks import issue_share
from src.utils.database import Database
from src.utils.logger import LOGGER


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

            companies_query = select(Company)
            companies = session.execute(companies_query).scalars().all()

            instruments_query = select(Instrument.company_id)
            instruments = session.execute(instruments_query).scalars().all()

            new_instruments = [
                Instrument(company.id, company.claan.name.split("_")[0].upper())
                for company in companies
                if company.id not in instruments
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

                for _ in range(0, 50 - shares_count):
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

        ## Issue shares to board members
        with session.begin_nested() as transaction:
            LOGGER.info("Issuing starting shares")
            query = (
                select(Portfolio, User, func.count(Share.id).label("count"))
                .select_from(Portfolio)
                .join(User)
                .join(Share, isouter=True)
                .group_by(Portfolio, User)
            )
            result = session.execute(query).scalars().all()

            for portfolio in result:
                if len(portfolio.shares) < 2:
                    for _ in range(0, 2 - len(portfolio.shares)):
                        LOGGER.info(f"Issuing share to user {portfolio.user.name}")
                        with session.begin_nested():
                            issue_share(_session=session, portfolio=portfolio)

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
