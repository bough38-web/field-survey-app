import pandas as pd
from pathlib import Path

BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "storage"
DATA_DIR.mkdir(exist_ok=True)

TARGET_FILE = DATA_DIR / "survey_targets.csv"
RESULT_FILE = DATA_DIR / "survey_results.csv"
REASON_FILE = BASE_DIR / "reason_map.csv"

# =========================
# 🔑 담당자 컬럼 정규화 (핵심)
# =========================
def normalize_owner_column(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df

    df = df.copy()
    df.columns = (
        df.columns.astype(str)
        .str.replace(" ", "")
        .str.replace("\n", "")
        .str.strip()
    )

    rename_map = {}
    if "이름(담당자)" in df.columns:
        rename_map["이름(담당자)"] = "담당자"
    if "구역담당자" in df.columns:
        rename_map["구역담당자"] = "담당자"

    df = df.rename(columns=rename_map)
    df = df.loc[:, ~df.columns.duplicated()]
    return df

# =========================
# 데이터 로드 / 저장
# =========================
def load_targets():
    if TARGET_FILE.exists():
        df = pd.read_csv(TARGET_FILE)
        return normalize_owner_column(df)
    return pd.DataFrame()

def save_targets(df):
    df = normalize_owner_column(df)
    df.to_csv(TARGET_FILE, index=False)

def load_results():
    if RESULT_FILE.exists():
        df = pd.read_csv(RESULT_FILE)
        return normalize_owner_column(df)
    return pd.DataFrame()

def save_result(row: dict):
    df = load_results()
    df = pd.concat([df, pd.DataFrame([row])], ignore_index=True)
    df.to_csv(RESULT_FILE, index=False)

# =========================
# 해지사유 / 불만유형
# =========================
def load_reason_map():
    if REASON_FILE.exists():
        return pd.read_csv(REASON_FILE)
    return pd.DataFrame(columns=["해지사유", "불만유형"])
