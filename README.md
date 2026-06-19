# MLB Batted Ball Luck Pipeline

Baseball data pipeline that compares hitters' actual vs expected batting average to reveal who's getting lucky or unlucky.

## Why

Batting average is noisy. A hitter can scorch the ball and still get robbed by a great defensive play, or hit a weak dribbler that happens to find a gap. Statcast's expected batting average (xBA) measures contact quality using exit velocity and launch angle, independent of outcome. Comparing actual BA to xBA surfaces which hitters are over or underperforming their underlying skill, which is useful for spotting regression and breakout candidates before the stats catch up.

## Architecture

```
Statcast API (pybaseball)
        ↓
  Python ingestion script (incremental, cached locally as parquet)
        ↓
  PostgreSQL (raw_statcast table)
        ↓
  SQL transformation layer (player_luck_scores, player_names, player_luck_names views)
        ↓
  Streamlit dashboard
        ↓
  Cron job — runs update_games.py daily, pulls only new game dates
```

## Tech stack

- **Python** — pybaseball, pandas, psycopg2
- **PostgreSQL** — storage and SQL transformations
- **Streamlit** — dashboard
- **Cron** — daily scheduled automation

## How it works

1. `ingest.py` checks the most recent game date already loaded in PostgreSQL, pulls only the missing dates from Statcast via pybaseball, and caches the raw pull locally as parquet to avoid redundant API calls.
2. Data loads into a `raw_statcast` table using `execute_values` for fast bulk inserts, with a unique constraint on game date, batter, pitcher, at-bat number, and pitch number to prevent duplicate pitches on reruns.
3. `load_players.py` maintains a `player_names` lookup table, mapping Statcast's numeric player IDs to readable names.
4. SQL views aggregate raw pitch-level data into one row per player: hits, at-bats, actual batting average, average expected batting average (on balls in play only — walks, strikeouts, and hit by pitches are excluded since they have no xBA), and the luck score (actual BA minus xBA).
5. `update_games.py` runs daily via cron, automatically picking up new games with no manual date entry required.
6. The Streamlit dashboard reads from the final view and lets you filter by minimum at-bats and sort by luck score.

## Project structure

```
mlb-luck-pipeline/
├── ingest.py          # pulls and loads statcast data
├── load_players.py    # builds player ID to name lookup table
├── update_games.py    # daily incremental update, run via cron
├── dashboard.py        # streamlit app
├── .env                # database credentials (not committed)
├── .gitignore
├── requirements.txt
└── data/
    └── raw/            # cached parquet files
```

## Running it locally

```bash
git clone [your repo url]
cd mlb-luck-pipeline
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

Create a `.env` file:
```
DB_NAME=baseball
DB_USER=pipeline_user
DB_PASSWORD=yourpassword
DB_HOST=localhost
DB_PORT=5432
```

Set up PostgreSQL, then run:
```bash
python3 ingest.py
python3 load_players.py
streamlit run dashboard.py
```

To automate daily updates, schedule `update_games.py` with cron:
```bash
crontab -e
# add a line like:
0 6 * * * /path/to/venv/bin/python3 /path/to/update_games.py
```

## What I'd improve with more time

- Migrate from cron to Airflow for better observability and retry logic
- Deploy PostgreSQL to a cloud instance instead of running locally
- Add player headshots and team logos to the dashboard
- Expand the luck score model to account for park factors and defensive positioning
