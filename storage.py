import pandas as pd
from pathlib import Path

BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "storage"
DATA_DIR.mkdir(exist_ok=True)

TARGET_FILE = DATA_DIR / "survey_targets.csv"
RESULT_FILE = DATA_DIR / "survey_results.csv"
REASON_FILE = BASE_DIR / "reason_map.csv"

# =========================
# 담당자 컬럼 정규화
# =========================
def normalize_owner_column(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df

    rename_map = {}
    if "이름(담당자)" in df.columns:
        rename_map["이름(담당자)"] = "담당자"
    if "구역담당자" in df.columns:
        rename_map["구역담당자"] = "담당자"

    df = df.rename(columns=rename_map)
    df = df.loc[:, ~df.columns.duplicated()]
    return df

# =========================
# 🔥 결과 데이터 마이그레이션
# =========================
def migrate_results_schema(df: pd.DataFrame) -> pd.DataFrame:
    """
    - 세부내용 → 세부 해지사유 및 불만 내용
    - 구 컬럼 제거
    - 이후 표준 컬럼만 유지
    """
    if df.empty:
        return df

    df = df.copy()

    # 1️⃣ 기존 세부내용 → 신규 컬럼 이관
    if "세부내용" in df.columns:
        if "세부 해지사유 및 불만 내용" not in df.columns:
            df["세부 해지사유 및 불만 내용"] = df["세부내용"]
        else:
            # 둘 다 있으면 값이 있는 쪽 우선
            df["세부 해지사유 및 불만 내용"] = (
                df["세부 해지사유 및 불만 내용"]
                .fillna(df["세부내용"])
            )

    # 2️⃣ 구 컬럼 제거
    drop_cols = ["세부내용"]
    df = df.drop(columns=[c for c in drop_cols if c in df.columns])

    return df

# =========================
# 데이터 로드
# =========================
def load_targets():
    if TARGET_FILE.exists():
        df = pd.read_csv(TARGET_FILE)
        return normalize_owner_column(df)
    return pd.DataFrame()

def load_results():
    if RESULT_FILE.exists():
        df = pd.read_csv(RESULT_FILE)

        # 🔥 마이그레이션 적용
        df = migrate_results_schema(df)
        df = normalize_owner_column(df)

        # 👉 정리된 스키마로 다시 저장 (1회)
        df.to_csv(RESULT_FILE, index=False)

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
