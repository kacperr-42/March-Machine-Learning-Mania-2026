import streamlit as st
import pandas as pd
import plotly.express as px
from kaggle.api.kaggle_api_extended import KaggleApi
from datetime import datetime
from pathlib import Path
import tempfile, zipfile
from streamlit_autorefresh import st_autorefresh

st.set_page_config(page_title="March Madness Tracker", layout="wide")

@st.cache_resource
def get_api():
    api = KaggleApi()
    api.authenticate()
    return api

# --------------- CONFIG ---------------
COMPETITION = "march-machine-learning-mania-2026"
USERNAMES = [
    "Kacper Rzeźniczak",
    "Ryszard Czarnecki",
    "Stefan Gajda",
    "Norbert Gościcki",
]
HISTORY_FILE = Path(__file__).parent.parent/'score_history.csv'
api = get_api()

# --------------- FUNCTIONS ---------------
def fetch_leaderboard(api) -> pd.DataFrame:
    with tempfile.TemporaryDirectory() as tmp:
        api.competition_leaderboard_download(COMPETITION, tmp)
        with zipfile.ZipFile(f"{tmp}/{COMPETITION}.zip") as z:
            csv_name = z.namelist()[0]
            with z.open(csv_name) as f:
                df = pd.read_csv(f)
    df = df.loc[df["TeamName"].isin(USERNAMES), ['TeamName', 'Rank', 'Score']]
    df['FetchDate'] = datetime.now()
    return df

def load_history() -> pd.DataFrame:
    if HISTORY_FILE.exists():
        return pd.read_csv(HISTORY_FILE, parse_dates=["FetchDate"])
    return pd.DataFrame(columns=['TeamName', 'Rank', 'Score', 'FetchDate'])

def save_snapshot(current: pd.DataFrame, history: pd.DataFrame) -> pd.DataFrame:
    if not history.empty:
        current_comp = current.drop(columns="FetchDate").reset_index(drop=True)
        hist_comp = history.iloc[-len(current):].drop(columns="FetchDate").reset_index(drop=True)
        if current_comp.equals(hist_comp):
            return history
    updated = pd.concat([history, current], ignore_index=True)
    updated.to_csv(HISTORY_FILE, index=False)
    return updated

# --------------- DATA ---------------
st_autorefresh(interval=20 * 60 * 1000, key="refresh") #auto-feching without having to refesh

current = fetch_leaderboard(api)
history = load_history()
history = save_snapshot(current, history)



# --------------- UI ---------------
st.title("🏀 March Madness — Score Tracker")

# Przycisk + info
col_btn, col_info = st.columns([1, 3])
with col_btn:
    if st.button("🔄 Fetch new snapshot", type="primary"):
        st.rerun()
with col_info:
    if not history.empty:
        st.caption(f"Last snapshot: {history['FetchDate'].max().strftime('%Y-%m-%d %H:%M')}")

if history.empty:
    st.info("No data yet — click **Fetch new snapshot** to start tracking.")
else:
    # Metryki — każdy gracz w osobnej kolumnie
    st.subheader("Current Standings")
    latest_ts = history["FetchDate"].max()
    latest = (
        history[history["FetchDate"] == latest_ts]
        .sort_values("Rank")
        .reset_index(drop=True)
    )

    cols = st.columns(len(latest))
    for i, (_, row) in enumerate(latest.iterrows()):
        with cols[i]:
            # Delta z poprzedniego snapshotu
            delta_rank = None
            timestamps = sorted(history["FetchDate"].unique())
            if len(timestamps) >= 2:
                prev = history[history["FetchDate"] == timestamps[-2]]
                prev_row = prev[prev["TeamName"] == row["TeamName"]]
                if not prev_row.empty:
                    delta_rank = int(prev_row.iloc[0]["Rank"] - row["Rank"])

            st.metric(
                label=row["TeamName"],
                value=f"#{int(row['Rank'])}",
                delta=f"{delta_rank:+d} Ranks" if delta_rank else None,
                delta_color="normal",
            )
            st.caption(f"Score: {row['Score']:.4f}")

    # Wykresy w tabach
    tab1, tab2 = st.tabs(["📈 Score over time", "🏆 Rank over time"])

    with tab1:
        fig_score = px.line(
            history, x="FetchDate", y="Score", color="TeamName",
            markers=True,
            labels={"FetchDate": "Time", "Score": "Brier Score", "TeamName": "Participant"},
        )
        fig_score.update_layout(
            yaxis_title="Brier Score",
            hovermode="x unified",
        )
        st.plotly_chart(fig_score, use_container_width=True)

    with tab2:
        fig_rank = px.line(
            history, x="FetchDate", y="Rank", color="TeamName",
            markers=True,
            labels={"FetchDate": "Time", "Score": "Brier Score", "TeamName": "Participant"},
        )
        fig_rank.update_layout(
            yaxis_title="Rank",
            yaxis_autorange="reversed",
            hovermode="x unified",
        )
        st.plotly_chart(fig_rank, use_container_width=True)