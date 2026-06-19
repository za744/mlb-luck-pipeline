import streamlit as st
from data import load_data

st.title("Player Explorer")
st.subheader("Find any player and their luck score")

df = load_data()

def render_sidebar():
    min_ab = int(df["abs"].min())
    max_ab = int(df["abs"].max())

    with st.sidebar:
        st.header("Filters")

        ab_threshold = st.slider(
            "Minimum ABs",
            min_value=min_ab,
            max_value=max_ab,
            value=100
        )

    return ab_threshold

ab_threshold = render_sidebar()

filtered = df[df["abs"] >= ab_threshold]

player_search = st.text_input(
    "Search Player",
    placeholder="Aaron Judge"
)

if player_search:
    filtered = filtered[
        filtered["batter_name"].str.contains(
            player_search,
            case=False,
            na=False
        )
    ]

if filtered.empty:
    st.warning("No players match your filters.")
    st.stop()

# Player selector
selected_player = st.selectbox(
    "Select a Player",
    filtered["batter_name"]
        .sort_values()
        .unique()
)

player = filtered[
    filtered["batter_name"] == selected_player
].iloc[0]

st.divider()

st.header(selected_player)

col1, col2, col3, col4 = st.columns(4)

col1.metric(
    "Luck Score",
    round(player["luck_score"], 3)
)

col2.metric(
    "BA",
    round(player["true_ba"], 3)
)

col3.metric(
    "xBA",
    round(player["xba"], 3)
)

col4.metric(
    "ABs",
    int(player["abs"])
)

st.divider()

display_cols = [
    "batter_name",
    "abs",
    "true_ba",
    "xba",
    "luck_score"
]

st.dataframe(
    filtered[display_cols].sort_values(
        "luck_score",
        ascending=False
    ),
    use_container_width=True,
    hide_index=True
)