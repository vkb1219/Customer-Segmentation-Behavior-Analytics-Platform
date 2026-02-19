from sqlalchemy import create_engine, text
from python.config import DATABASE_URL

def get_engine():
    return create_engine(DATABASE_URL, pool_pre_ping=True)

def execute_sql(sql: str):
    eng = get_engine()
    with eng.begin() as conn:
        conn.execute(text(sql))

def fetch_df(query: str):
    import pandas as pd
    eng = get_engine()
    return pd.read_sql_query(query, eng)
