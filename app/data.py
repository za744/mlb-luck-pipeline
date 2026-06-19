import streamlit as st
import pandas as pd
import psycopg2
import os
from dotenv import load_dotenv

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

@st.cache_data
def load_data():
    return pd.read_sql_query(
        "select * from player_luck_names",
        get_connection()
    )