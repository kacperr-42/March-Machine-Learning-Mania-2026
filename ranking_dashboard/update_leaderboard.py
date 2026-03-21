import pandas as pd
from kaggle.api.kaggle_api_extended import KaggleApi
from datetime import datetime
from pathlib import Path
import tempfile, zipfile

def get_api():
    api = KaggleApi()
    api.authenticate()
    return api
#--------------- config ---------------
COMPETITION = "march-machine-learning-mania-2026"
USERNAMES = [
    "Kacper Rzeźniczak",
    "Ryszard Czarnecki",
    "Stefan Gajda",
    "Norbert Gościcki",
]
HISTORY_FILE = Path("score_history.csv")

api = get_api()

#--------------- function ---------------

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
            return 
    updated = pd.concat([history, current], ignore_index=True)
    updated.to_csv(HISTORY_FILE, index=False)
    return updated

#--------------- script ---------------

current=fetch_leaderboard(api)
history = load_history()
if save_snapshot(current,history) is not None:
    print(f"new {len(current)} rows added")
else:
    print("no changes")