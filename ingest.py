import os
import pandas as pd
import psycopg2
from pybaseball import statcast, playerid_reverse_lookup
from dotenv import load_dotenv
from psycopg2.extras import execute_values
import numpy as np

load_dotenv()

def pull_data(start_time, end_time, refresh=False):
    os.makedirs("data/raw", exist_ok=True) #create folder for data

    file_path = f"data/raw/statcast_{start_time}_{end_time}.parquet" #create parquet file using years as name
    if os.path.exists(file_path) and not refresh: #check if the filepath has already been created. Refresh attribute checks if need for cache
        print(f"Loading cached data for {start_time} to {end_time}")
        return pd.read_parquet(file_path) #reads parquet file which is like a compressed csv file
    print(f"Pulling statcast data from {start_time} to {end_time}")
    df = statcast(start_dt=start_time, end_dt=end_time)
    print(f"Got {len(df)} rows")
    df = df.replace({np.nan: None})
    df.to_parquet(file_path)
    return df

def get_connection():
    required_vars = ["DB_NAME", "DB_USER", "DB_PASSWORD", "DB_HOST", "DB_PORT"] #list of required variables
    missing = [x for x in required_vars if not os.getenv(x)] #os.getenv returns None if not exist
    if missing:
        raise ValueError(f"Missing enviroment variables: {missing}") #if missing is not empty then throw error
    return psycopg2.connect( #start by opening TCP connection to postgres
        dbname = os.getenv("DB_NAME"),
        user = os.getenv("DB_USER"),
        password = os.getenv("DB_PASSWORD"), #connect to specific server
        host = os.getenv("DB_HOST"),
        port = os.getenv("DB_PORT")
    )

def create_table(conn):
    with conn.cursor() as cur: #cursor = "talking" to sql database "with" closes call after
        cur.execute("""
            CREATE TABLE IF NOT EXISTS raw_statcast (
                id SERIAL PRIMARY KEY,
                game_date DATE,
                batter INTEGER,
                pitcher INTEGER,
                events VARCHAR(50),
                estimated_ba_using_speedangle FLOAT,
                estimated_woba_using_speedangle FLOAT,
                launch_speed FLOAT,
                launch_angle FLOAT,
                player_name VARCHAR(100),
                at_bat_number INTEGER,
                pitch_number INTEGER
            );
        """)
        conn.commit()

#loading data, takes conn database connection, and loads the df onto postgres
def load_data(conn, df):
    cols = [
        'game_date', 'batter', 'pitcher', 'events', 'estimated_ba_using_speedangle', 'estimated_woba_using_speedangle', 'launch_speed',
        'launch_angle', 'player_name', 'at_bat_number', 'pitch_number'
    ]
    df = df[cols].dropna(subset=['events'])
    df = df.copy()
    df = df.where(pd.notnull(df), None) #creates a boolean mask where(condition met, otherwise none postgres understands NONE better than NaN)
    for col in df.select_dtypes(include=[np.number]).columns: #finds columns with type of number such as int or float
        df[col] = df[col].apply(lambda x : x.item() if hasattr(x, "item") else x) #.item takes raw python value from np number lambda creates a fuctions, hasattr checks if x.item() exists
    values = [
    tuple(
        None if pd.isna(x) else x
        for x in row
    )
    for row in df.itertuples(index=False, name=None)
    ]
    query = """
        INSERT INTO raw_statcast (
            game_date,
            batter,
            pitcher,
            events,
            estimated_ba_using_speedangle,
            estimated_woba_using_speedangle,
            launch_speed,
            launch_angle,
            player_name,
            at_bat_number,
            pitch_number
        )
        VALUES %s
        ON CONFLICT (game_date, batter, pitcher, at_bat_number, pitch_number)
        DO NOTHING
    """
    try:
        with conn.cursor() as cur:
            execute_values(cur, query, values, page_size=10000)
            conn.commit()
            print(f"Loaded {len(df):,} rows into raw_statcast")
    except Exception as e:
        conn.rollback() #undos everything before fail
        print(f"Load failed: {e}")
        raise


if __name__ == "__main__":
    """df = pull_data("2026-03-25", "2026-06-10")
    conn = get_connection()
    with conn.cursor() as cur:
        cur.execute("SELECT current_user;")
        print(cur.fetchone())
    create_table(conn)
    load_data(conn, df)
    conn.close()
    print("Done")
    print(playerid_reverse_lookup([592663]))"""