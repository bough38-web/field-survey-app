import pandas as pd
from pathlib import Path

BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "storage"
DATA_DIR.mkdir(exist_ok=True)

TARGET_FILE = DATA_DIR / "survey_targets.csv"
RESULT_FILE = DATA_DIR / "survey_results.csv"
REASON_FILE = BASE_DIR / "reason_map.csv"

# =========================
# 컬럼 정규화 (담당자 / 상호)
# =========================
def normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df

    df = df.copy()

    # 🔹 담당자 통일
    for col in ["이름(담당자)", "구역담당자"]:
        if col in df.columns and "담당자" not in df.columns:
            df["담당자"] = df[col]

    # 🔹 상호 통일
    if "상호" not in df.columns:
        for alt in ["상호명", "업체명", "고객명"]:
            if alt in df.columns:
                df["상호"] = df[alt]
                break
        else:
            df["상호"] = ""

    df = df.loc[:, ~df.columns.duplicated()]
    return df

# =========================
# 🔥 결과 데이터 마이그레이션
# =========================
def migrate_results_schema(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df

    df = df.copy()

    # 세부내용 → 신규 컬럼
    if "세부내용" in df.columns:
        if "세부 해지사유 및 불만 내용" not in df.columns:
            df["세부 해지사유 및 불만 내용"] = df["세부내용"]
        else:
            df["세부 해지사유 및 불만 내용"] = (
                df["세부 해지사유 및 불만 내용"]
                .fillna(df["세부내용"])
            )
        df = df.drop(columns=["세부내용"])

    return df

# =========================
# 데이터 로드
# =========================
def load_targets():
    if TARGET_FILE.exists():
        df = pd.read_csv(TARGET_FILE)
        return normalize_columns(df)
    return pd.DataFrame()

def load_results():
    if RESULT_FILE.exists():
        df = pd.read_csv(RESULT_FILE)
        df = migrate_results_schema(df)
        df = normalize_columns(df)
        df.to_csv(RESULT_FILE, index=False)  # 1회 정리
        return df
    return pd.DataFrame()

def save_result(row: dict):
    df = load_results()
    df = pd.concat([df, pd.DataFrame([row])], ignore_index=True)
    df.to_csv(RESULT_FILE, index=False)

def load_reason_map():
    if REASON_FILE.exists():
        return pd.read_csv(REASON_FILE)
    return pd.DataFrame(columns=["해지사유", "불만유형"])
