from sqlalchemy import text
from db import engine


def fetch_df(query: str):
    with engine.connect() as conn:
        return conn.execute(text(query)).fetchall()


def get_precinct_summary():
    query = """
        SELECT issuer_precinct AS precinct,
               COUNT(*) AS tickets
        FROM parking_violations
        WHERE issuer_precinct IS NOT NULL
        GROUP BY issuer_precinct
        ORDER BY tickets DESC
        LIMIT 50;
    """
    return fetch_df(query)


def get_monthly_trends():
    query = """
        SELECT DATE_FORMAT(issue_date, '%Y-%m') AS month,
               COUNT(*) AS tickets
        FROM parking_violations
        WHERE issue_date IS NOT NULL
        GROUP BY month
        ORDER BY month;
    """
    return fetch_df(query)


def get_top_violations():
    query = """
        SELECT violation_description,
               COUNT(*) AS count
        FROM parking_violations
        WHERE violation_description IS NOT NULL
        GROUP BY violation_description
        ORDER BY count DESC
        LIMIT 15;
    """
    return fetch_df(query)


def get_revenue_by_precinct():
    query = """
        SELECT issuer_precinct,
               COUNT(*) * 65 AS estimated_revenue
        FROM parking_violations
        WHERE issuer_precinct IS NOT NULL
        GROUP BY issuer_precinct
        ORDER BY estimated_revenue DESC
        LIMIT 50;
    """
    return fetch_df(query)