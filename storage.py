import pandas as pd
from pathlib import Path

BASE_DIR = Path(__file__).parent
STORAGE_DIR = BASE_DIR / "storage"
STORAGE_DIR.mkdir(exist_ok=True)

TARGET_FILE = STORAGE_DIR / "survey_targets.csv"
RESULT_FILE = STORAGE_DIR / "survey_results.csv"
CONTACT_FILE = BASE_DIR / "contact_map.xlsx"

# =========================
# 담당자 매핑 파일 로드
# =========================
def load_contacts():
    if not CONTACT_FILE.exists():
        return pd.DataFrame(columns=["branch", "owner"])

    df = pd.read_excel(CONTACT_FILE)

    # 컬럼명 강제 표준화
    df.columns = (
        df.columns.astype(str)
        .str.replace("\n", "")
        .str.replace(" ", "")
        .str.replace("/", "")
        .str.strip()
    )

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

    if not {"branch", "owner"}.issubset(df.columns):
        return pd.DataFrame(columns=["branch", "owner"])

    return df[["branch", "owner"]]

# =========================
# 조사 대상 + 담당자 처리
# =========================
def match_branch_owner(df):
    df = df.copy()

    # 컬럼명 표준화
    df.columns = (
        df.columns.astype(str)
        .str.replace("\n", "")
        .str.replace(" ", "")
        .str.replace("/", "")
        .str.strip()
    )

    # 이름(담당자) → 담당자 통합
    if "이름담당자" in df.columns:
        if "담당자" not in df.columns:
            df = df.rename(columns={"이름담당자": "담당자"})
        else:
            df = df.drop(columns=["이름담당자"])

    # 중복 컬럼 제거 (🔥 핵심)
    df = df.loc[:, ~df.columns.duplicated()]

    # 이미 담당자가 있으면 그대로 사용
    if "담당자" in df.columns:
        return df

    # 담당자 없을 때만 contact_map 매칭
    contacts = load_contacts()
    if contacts.empty:
        df["담당자"] = ""
        return df

    if "관리지사" not in df.columns:
        df["담당자"] = ""
        return df

    merged = df.merge(
        contacts,
        left_on="관리지사",
        right_on="branch",
        how="left"
    )

    merged = merged.rename(columns={"owner": "담당자"})
    merged = merged.drop(columns=["branch"], errors="ignore")
    merged = merged.loc[:, ~merged.columns.duplicated()]

    return merged

# =========================
# 저장 / 로드
# =========================
def save_targets(df):
    df.to_csv(TARGET_FILE, index=False)

def load_targets():
    if TARGET_FILE.exists():
        return pd.read_csv(TARGET_FILE)
    return pd.DataFrame()

def save_result(row: dict):
    if RESULT_FILE.exists():
        df = pd.read_csv(RESULT_FILE)
    else:
        df = pd.DataFrame()

    df = pd.concat([df, pd.DataFrame([row])], ignore_index=True)
    df.to_csv(RESULT_FILE, index=False)

def load_results():
    if RESULT_FILE.exists():
        return pd.read_csv(RESULT_FILE)
    return pd.DataFrame()
