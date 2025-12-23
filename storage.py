import pandas as pd
from pathlib import Path

# =========================
# 경로 설정
# =========================
BASE_DIR = Path(__file__).parent
STORAGE_DIR = BASE_DIR / "storage"
STORAGE_DIR.mkdir(exist_ok=True)

TARGET_FILE = STORAGE_DIR / "survey_targets.csv"
RESULT_FILE = STORAGE_DIR / "survey_results.csv"
CONTACT_FILE = BASE_DIR / "contact_map.xlsx"

# =========================
# 담당자 로드
# =========================
def load_contacts() -> pd.DataFrame:
    if CONTACT_FILE.exists():
        df = pd.read_excel(CONTACT_FILE)
        df.columns = [c.strip() for c in df.columns]
        return df
    return pd.DataFrame(columns=["department", "name"])

# =========================
# 조사 대상 자동 매칭
# =========================
def match_branch_owner(df_targets: pd.DataFrame) -> pd.DataFrame:
    contacts = load_contacts()

    if contacts.empty:
        df_targets["담당자"] = ""
        return df_targets

    merged = df_targets.merge(
        contacts,
        left_on="관리지사",
        right_on="department",
        how="left"
    )

    merged.rename(columns={"name": "담당자"}, inplace=True)
    merged.drop(columns=["department"], inplace=True, errors="ignore")

    return merged

# =========================
# 조사 대상(Targets)
# =========================
def load_targets() -> pd.DataFrame:
    if TARGET_FILE.exists():
        return pd.read_csv(TARGET_FILE)
    return pd.DataFrame()

def save_targets(df: pd.DataFrame):
    df.to_csv(TARGET_FILE, index=False)

# =========================
# 조사 결과(Results)
# =========================
def load_results() -> pd.DataFrame:
    if RESULT_FILE.exists():
        return pd.read_csv(RESULT_FILE)
    return pd.DataFrame()

def save_result(row: dict):
    df = load_results()
    df = pd.concat([df, pd.DataFrame([row])], ignore_index=True)
    df.to_csv(RESULT_FILE, index=False)
