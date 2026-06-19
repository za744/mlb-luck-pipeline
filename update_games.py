import os
import pandas as pd
import psycopg2
from pybaseball import statcast, playerid_reverse_lookup
from dotenv import load_dotenv
from psycopg2.extras import execute_values
import numpy as np
from datetime import datetime, timedelta, date
from ingest import load_data, pull_data
from load_players import build_name_table

load_dotenv()

def get_connection():
    required_vars = ["DB_NAME", "DB_USER", "DB_PASSWORD", "DB_HOST", "DB_PORT"] 
    missing = [x for x in required_vars if not os.getenv(x)] 
    if missing:
        raise ValueError(f"Missing enviroment variables: {missing}") 
    return psycopg2.connect( 
        dbname = os.getenv("DB_NAME"),
        user = os.getenv("DB_USER"),
        password = os.getenv("DB_PASSWORD"), 
        host = os.getenv("DB_HOST"),
        port = os.getenv("DB_PORT")
    )

def get_last_loaded(conn):
    query = "SELECT MAX(game_date) FROM raw_statcast"
    result = pd.read_sql(query, conn)
    return result.iloc[0,0]

def update_games():
    connection = get_connection()
    last_loaded = get_last_loaded(connection)
    today = date.today()
    start_date = last_loaded + timedelta(days=1)
    end_date = today - timedelta(days=1)
    if(start_date < end_date):
        print("No new games to load")
        exit()
    df = pull_data(datetime.strftime(start_date, "%Y-%m-%d"), datetime.strftime(end_date, "%Y-%m-%d"))
    load_data(connection, df)
    build_name_table(connection)

if __name__ == "__main__":
    update_games()
    