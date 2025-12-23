import pandas as pd
from pathlib import Path

# =========================
# 경로 설정
# =========================

BASE_DIR = Path(__file__).parent

STORAGE_DIR = BASE_DIR / "storage"
STORAGE_DIR.mkdir(exist_ok=True)

EVENTS_FILE = STORAGE_DIR / "events.csv"
ACTIONS_FILE = STORAGE_DIR / "actions.csv"

CONTACT_FILE = BASE_DIR / "contact_map.xlsx"

# =========================
# 이벤트(Event) 관련
# =========================

def load_events() -> pd.DataFrame:
    """
    이벤트(조사/공지) 목록 로드
    """
    if EVENTS_FILE.exists():
        return pd.read_csv(EVENTS_FILE)
    return pd.DataFrame(
        columns=[
            "event_id",
            "title",
            "type",
            "due_date",
            "description",
            "reference"
        ]
    )


# =========================
# 조치(Action) 관련
# =========================

def load_actions() -> pd.DataFrame:
    """
    현업 조치 내역 로드
    """
    if ACTIONS_FILE.exists():
        return pd.read_csv(ACTIONS_FILE)
    return pd.DataFrame(
        columns=[
            "event_id",
            "department",
            "owner",
            "status",
            "comment",
            "created_at"
        ]
    )


def save_action(action: dict) -> None:
    """
    조치 내역 1건 저장
    """
    df = load_actions()
    df = pd.concat(
        [df, pd.DataFrame([action])],
        ignore_index=True
    )
    df.to_csv(ACTIONS_FILE, index=False)


# =========================
# 담당자(Contact) 관련
# =========================

def load_contacts() -> pd.DataFrame:
    """
    담당자 매핑 정보 로드
    (contact_map.xlsx)
    """
    if CONTACT_FILE.exists():
        df = pd.read_excel(CONTACT_FILE)

        # 컬럼 표준화 (혹시 모를 오타 대비)
        df.columns = [c.strip().lower() for c in df.columns]

        required_cols = {"department", "name"}
        if not required_cols.issubset(set(df.columns)):
            raise ValueError(
                "contact_map.xlsx에 'department', 'name' 컬럼이 필요합니다."
            )

        return df

    return pd.DataFrame(columns=["department", "name"])


# =========================
# 운영 편의용 헬퍼
# =========================

def get_departments():
    """
    부서 목록
    """
    contacts = load_contacts()
    if contacts.empty:
        return []
    return sorted(contacts["department"].dropna().unique())


def get_owners_by_department(department: str):
    """
    부서별 담당자 목록
    """
    contacts = load_contacts()
    if contacts.empty:
        return []
    return (
        contacts[contacts["department"] == department]["name"]
        .dropna()
        .unique()
        .tolist()
    )
