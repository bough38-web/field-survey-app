import pandas as pd
from pathlib import Path

BASE_DIR = Path(__file__).parent
STORAGE_DIR = BASE_DIR / "storage"
STORAGE_DIR.mkdir(exist_ok=True)

TARGET_FILE = STORAGE_DIR / "survey_targets.csv"
RESULT_FILE = STORAGE_DIR / "survey_results.csv"
REASON_FILE = BASE_DIR / "reason_map.csv"

# =========================
# 해지사유 / 불만유형 맵
# =========================
def load_reason_map():
    if REASON_FILE.exists():
        df = pd.read_csv(REASON_FILE)
        df.columns = df.columns.str.strip()
        return df
    return pd.DataFrame(columns=["해지사유", "불만유형"])

# =========================
# 조사 대상
# =========================
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
