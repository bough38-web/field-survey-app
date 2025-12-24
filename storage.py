import pandas as pd
from pathlib import Path

BASE_DIR = Path(__file__).parent
STORAGE_DIR = BASE_DIR / "storage"
STORAGE_DIR.mkdir(exist_ok=True)

TARGET_FILE = STORAGE_DIR / "survey_targets.csv"
RESULT_FILE = STORAGE_DIR / "survey_results.csv"
CONTACT_FILE = BASE_DIR / "contact_map.xlsx"

# =========================
# 담당지사 / 담당자 로드
# =========================
def load_contacts():
    if not CONTACT_FILE.exists():
        return pd.DataFrame(columns=["branch", "owner"])

    df = pd.read_excel(CONTACT_FILE)

    # 🔥 컬럼명 강제 표준화 (핵심)
    df.columns = (
        df.columns
        .str.replace("\n", "")
        .str.replace(" ", "")
        .str.replace("/", "")
        .str.strip()
    )

    # 가능한 컬럼명 케이스 흡수
    rename_map = {
        "담당지사팀": "branch",
        "담당지사": "branch",
        "지사": "branch",
        "팀": "branch",
        "이름": "owner",
        "담당자": "owner",
        "성명": "owner"
    }

    df = df.rename(columns=rename_map)

    # 필수 컬럼 체크
    if not {"branch", "owner"}.issubset(df.columns):
        raise ValueError(
            "contact_map.xlsx에 담당지사/팀 및 이름(담당자) 컬럼이 필요합니다."
        )

    return df[["branch", "owner"]]

# =========================
# 조사 대상에 담당자 매칭
# =========================
def match_branch_owner(df):
    contacts = load_contacts()

    # 조사 대상 컬럼도 동일하게 표준화
    df = df.copy()
    df.columns = (
        df.columns
        .str.replace("\n", "")
        .str.replace(" ", "")
        .str.replace("/", "")
        .str.strip()
    )

    if "관리지사" not in df.columns:
        raise ValueError("조사 대상 데이터에 '관리지사' 컬럼이 없습니다.")

    merged = df.merge(
        contacts,
        left_on="관리지사",
        right_on="branch",
        how="left"
    )

    merged = merged.rename(columns={"owner": "담당자"})
    merged = merged.drop(columns=["branch"], errors="ignore")

    return merged

# =========================
# 조사 대상 / 결과
# =========================
def load_targets():
    if TARGET_FILE.exists():
        return pd.read_csv(TARGET_FILE)
    return pd.DataFrame()

def save_targets(df):
    df.to_csv(TARGET_FILE, index=False)

def load_results():
    if RESULT_FILE.exists():
        return pd.read_csv(RESULT_FILE)
    return pd.DataFrame()

def save_result(row: dict):
    df = load_results()
    df = pd.concat([df, pd.DataFrame([row])], ignore_index=True)
    df.to_csv(RESULT_FILE, index=False)
