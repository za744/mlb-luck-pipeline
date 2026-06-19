import os
import pandas as pd
import psycopg2
from pybaseball import statcast, playerid_reverse_lookup
from dotenv import load_dotenv
from psycopg2.extras import execute_values
import numpy as np
import requests

load_dotenv()

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

def build_name_table(conn):
    query = """ SELECT DISTINCT batter FROM raw_statcast WHERE batter IS NOT NULL """

    id_list = pd.read_sql(query, conn)["batter"].to_list()
    players = playerid_reverse_lookup(id_list, key_type="mlbam")
    returned_ids = set(players["key_mlbam"].astype(int))
    missing_ids = set(id_list) - returned_ids
    for id in missing_ids:
        response = requests.get(f"https://statsapi.mlb.com/api/v1/people/{id}")
        if response.status_code == 200:
            response.encoding = "utf-8"
            info = response.json()
            fullName = (info['people'][0]['fullName']).split()
            name_row = pd.DataFrame({
                "key_mlbam" : [id],
                "name_first" : fullName[0],
                "name_last" : fullName[1]

            })
            players = pd.concat([players, name_row], ignore_index=True)
 
        else:
            raise Exception(f"Unknown ID {id}")
        players
    players = players[["key_mlbam", "name_first", "name_last"]].copy()
    players["fullname"] = (
        players["name_first"].fillna("").str.title()
        + " "
        + players["name_last"].fillna("").str.title()
    ).str.strip()    
    values = list(players[["key_mlbam", "fullname"]].itertuples(index=False, name=None))
    with conn.cursor() as cur:
        cur.execute('''
            CREATE TABLE IF NOT EXISTS player_names (
                player_id INTEGER PRIMARY KEY,
                player_name VARCHAR(50)
            )
        ''')
        execute_values(
            cur,
            """
            INSERT INTO player_names
            (player_id, player_name)
            VALUES %s
            ON CONFLICT (player_id)
            DO UPDATE SET
                player_name = EXCLUDED.player_name;
            """,
            values
        )

        conn.commit()

    print(f"Loaded {len(players):,} players")
    print(f"Loaded {len(missing_ids):,} new players")
    
    
