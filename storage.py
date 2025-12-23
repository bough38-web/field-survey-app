import pandas as pd
from pathlib import Path

BASE = Path("storage")
EVENTS = BASE / "events.csv"
ACTIONS = BASE / "actions.csv"

def load_events():
    if EVENTS.exists():
        return pd.read_csv(EVENTS)
    return pd.DataFrame(columns=["event_id","title","type","due_date","description","reference"])

def load_actions():
    if ACTIONS.exists():
        return pd.read_csv(ACTIONS)
    return pd.DataFrame()

def save_action(row: dict):
    df = load_actions()
    df = pd.concat([df, pd.DataFrame([row])], ignore_index=True)
    df.to_csv(ACTIONS, index=False)