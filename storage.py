import pandas as pd
from pathlib import Path
from filelock import FileLock # 동시성 제어

BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "storage"
DATA_DIR.mkdir(exist_ok=True)

TARGET_FILE = DATA_DIR / "survey_targets.csv"
RESULT_FILE = DATA_DIR / "survey_results.csv"
REASON_FILE = BASE_DIR / "reason_map.csv"

# 파일 동시 접근 방지를 위한 Lock 파일
LOCK_FILE = DATA_DIR / "data.lock"

# =========================
# 컬럼 정규화
# =========================
def normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df
    
    df = df.copy()
    
    # 1. 컬럼명 공백/특수문자 제거
    df.columns = (
        df.columns.astype(str)
        .str.replace("\n", "")
        .str.replace(" ", "")
        .str.replace("_", "")
        .str.strip()
    )

    # 2. 담당자 컬럼 통일
    for col in ["이름(담당자)", "구역담당자"]:
        if col in df.columns and "담당자" not in df.columns:
            df["담당자"] = df[col]

    # 3. 상호 컬럼 통일
    if "상호" not in df.columns:
        for alt in ["상호명", "업체명", "고객명"]:
            if alt in df.columns:
                df["상호"] = df[alt]
                break
        else:
            df["상호"] = "" # 없으면 빈 값

    # 중복 컬럼 제거
    df = df.loc[:, ~df.columns.duplicated()]
    return df

# =========================
# 데이터 로드 / 저장 (Lock 적용)
# =========================
def load_targets():
    if TARGET_FILE.exists():
        df = pd.read_csv(TARGET_FILE, dtype={"계약번호": str}) # 읽을 때 문자열로 강제
        return normalize_columns(df)
    return pd.DataFrame()

def save_targets(df: pd.DataFrame):
    df = normalize_columns(df)
    if "계약번호" in df.columns:
        df["계약번호"] = df["계약번호"].astype(str)
    
    with FileLock(str(LOCK_FILE)):
        df.to_csv(TARGET_FILE, index=False)

def load_results():
    if RESULT_FILE.exists():
        # 읽을 때 계약번호는 무조건 문자열 처리
        df = pd.read_csv(RESULT_FILE, dtype={"계약번호": str})
        return normalize_columns(df)
    return pd.DataFrame()

def save_result(row: dict):
    """
    데이터 저장 시 '계약번호'를 기준으로
    이미 존재하면 수정(Update), 없으면 추가(Append)합니다.
    """
    with FileLock(str(LOCK_FILE)):
        df = load_results()
        
        # 계약번호 문자열 변환
        contract_id = str(row["계약번호"])
        row["계약번호"] = contract_id
        
        if not df.empty and "계약번호" in df.columns:
            # 기존 데이터 확인
            idx = df[df["계약번호"] == contract_id].index
            
            if not idx.empty:
                # Update: 기존 행 업데이트
                for key, value in row.items():
                    df.loc[idx[0], key] = value
            else:
                # Insert: 신규 행 추가
                df = pd.concat([df, pd.DataFrame([row])], ignore_index=True)
        else:
            # 데이터가 아예 없을 때
            df = pd.DataFrame([row])

        df.to_csv(RESULT_FILE, index=False)

def load_reason_map():
    if REASON_FILE.exists():
        return pd.read_csv(REASON_FILE)
    return pd.DataFrame(columns=["해지사유", "불만유형"])
