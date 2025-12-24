import pandas as pd
from pathlib import Path

BASE_DIR = Path(__file__).parent
STORAGE_DIR = BASE_DIR / "storage"
STORAGE_DIR.mkdir(exist_ok=True)

TARGET_FILE = STORAGE_DIR / "survey_targets.csv"
RESULT_FILE = STORAGE_DIR / "survey_results.csv"
CONTACT_FILE = BASE_DIR / "contact_map.xlsx"

# =========================
# 담당지사/담당자
# =========================
def load_contacts():
    if CONTACT_FILE.exists():
        df = pd.read_excel(CONTACT_FILE)
        df.columns = df.columns.str.strip()
        return df
    return pd.DataFrame(columns=["담당지사/팀", "이름"])

def get_teams():
    df = load_contacts()
    return sorted(df["담당지사/팀"].dropna().unique().tolist())

def get_owners_by_team(team: str):
    df = load_contacts()
    return (
        df[df["담당지사/팀"] == team]["이름"]
        .dropna()
        .unique()
        .tolist()
    )

# =========================
# 조사 대상
# =========================
def match_branch_owner(df):
    contacts = load_contacts()
    if contacts.empty:
        return df

    merged = df.merge(
        contacts,
        left_on="관리지사",
        right_on="담당지사/팀",
        how="left"
    )
    merged.rename(columns={"이름": "담당자"}, inplace=True)
    merged.drop(columns=["담당지사/팀"], inplace=True, errors="ignore")
    return merged

def load_targets():
    if TARGET_FILE.exists():
        return pd.read_csv(TARGET_FILE)
    return pd.DataFrame()

def save_targets(df):
    df.to_csv(TARGET_FILE, index=False)

# =========================
# 조사 결과
# =========================
def load_results():
    if RESULT_FILE.exists():
        return pd.read_csv(RESULT_FILE)
    return pd.DataFrame()

def save_result(row: dict):
    df = load_results()
    df = pd.concat([df, pd.DataFrame([row])], ignore_index=True)
    df.to_csv(RESULT_FILE, index=False)
