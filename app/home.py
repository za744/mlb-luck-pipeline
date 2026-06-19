import streamlit as st
import requests
from data import load_data

st.set_page_config(layout="wide")
st.title("MLB Batted Ball Luck Tracker")
st.markdown("""
Luck Score = BA - xBA

Positive = overperforming contact quality

Negative = underperforming contact quality
""")

st.header("Top 5 Unluckiest Hitters (Min ABs >= 100)")

df = load_data()

eligible = df[df["abs"] >= 100]
unlucky = eligible.nsmallest(5, "luck_score")
luckiest = eligible.nlargest(5, "luck_score")
    
cols = st.columns(5)


for col, (_, player) in zip(cols, unlucky.iterrows()):
    with col:
        with st.container(border=True, horizontal_alignment="center"):
            st.image(f"https://img.mlbstatic.com/mlb-photos/image/upload/w_213,h_213,c_fill,f_auto,q_auto:best/v1/people/{player['batter']}/headshot/67/current", width=150)

            st.markdown(
                f"""
                <div style="text-align: left; min-height: 65px; display: flex; align-items: flex-end; padding-bottom: 5px;">
                    <h3 style="margin: 0; font-size: 1.25rem; font-weight: bold; line-height: 1.2;">
                        {player['batter_name']}
                    </h3>
                </div>
                """,
                unsafe_allow_html=True
            )

            luck_val = player['luck_score']

            if luck_val < 0:
                st.metric(
                    label="Luck Score", 
                    value=f"{luck_val:.3f}", 
                    delta="- Unlucky",       
                    delta_color="normal"     
                )
            else:
                st.metric(
                    label="Luck Score", 
                    value=f"{luck_val:.3f}", 
                    delta="Lucky",           
                    delta_color="normal"     
                )

st.divider()
st.header("Top 5 Luckiest Hitters (Min ABs >= 100)")
cols1 = st.columns(5)
for col, (_, player) in zip(cols1, luckiest.iterrows()):
    with col:
        with st.container(border=True, horizontal_alignment="center"):
            st.image(f"https://img.mlbstatic.com/mlb-photos/image/upload/w_213,h_213,c_fill,f_auto,q_auto:best/v1/people/{player['batter']}/headshot/67/current", width=150)

            st.markdown(
                f"""
                <div style="text-align: left; min-height: 65px; display: flex; align-items: flex-end; padding-bottom: 5px;">
                    <h3 style="margin: 0; font-size: 1.25rem; font-weight: bold; line-height: 1.2;">
                        {player['batter_name']}
                    </h3>
                </div>
                """,
                unsafe_allow_html=True
            )

            luck_val = player['luck_score']

            if luck_val < 0:
                st.metric(
                    label="Luck Score", 
                    value=f"{luck_val:.3f}", 
                    delta="- Unlucky",       
                    delta_color="normal"     
                )
            else:
                st.metric(
                    label="Luck Score", 
                    value=f"{luck_val:.3f}", 
                    delta="Lucky",           
                    delta_color="normal"     
                )
st.divider()

st.header("League Overview")

col1, col2, col3 = st.columns(3)

with col1:
    st.metric(
        "Players",
        len(df)
    )

with col2:
    st.metric(
        "Luckiest",
        luckiest.iloc[0]["batter_name"]
    )

with col3:
    st.metric(
        "Unluckiest",
        unlucky.iloc[0]["batter_name"]
    )