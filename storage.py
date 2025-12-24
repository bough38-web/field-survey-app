import pandas as pd
from pathlib import Path
from filelock import FileLock
import shutil
from datetime import datetime
import os

# =========================
# 기본 경로 및 설정
# =========================
BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "storage"
BACKUP_DIR = DATA_DIR / "backups"  # 백업 폴더
LOG_FILE = DATA_DIR / "activity_log.csv" # 로그 파일

# 폴더가 없으면 생성
DATA_DIR.mkdir(exist_ok=True)
BACKUP_DIR.mkdir(exist_ok=True)

TARGET_FILE = DATA_DIR / "survey_targets.csv"
RESULT_FILE = DATA_DIR / "survey_results.csv"
REASON_FILE = BASE_DIR / "reason_map.csv"
LOCK_FILE = DATA_DIR / "data.lock"

# =========================
# 1. 로그(Log) 기록 함수
# =========================
def log_activity(action, details, user="System"):
    """작업 이력을 CSV에 기록합니다."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    new_log = pd.DataFrame([{
        "일시": timestamp,
        "작업자": user,
        "작업유형": action,
        "상세내용": details
    }])
    
    with FileLock(str(LOCK_FILE)):
        if LOG_FILE.exists():
            new_log.to_csv(LOG_FILE, mode='a', header=False, index=False)
        else:
            new_log.to_csv(LOG_FILE, index=False)

def load_logs():
    """로그 내역을 불러옵니다."""
    if LOG_FILE.exists():
        return pd.read_csv(LOG_FILE).sort_values("일시", ascending=False)
    return pd.DataFrame(columns=["일시", "작업자", "작업유형", "상세내용"])

# =========================
# 2. 컬럼 정규화 (공통 유틸리티)
# =========================
def normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty: return df
    df = df.copy()
    
    # 1. 컬럼명 공백/특수문자 제거
    df.columns = (df.columns.astype(str).str.replace("\n", "").str.replace(" ", "").str.replace("_", "").str.strip())

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
            df["상호"] = ""

    # 중복 컬럼 제거
    df = df.loc[:, ~df.columns.duplicated()]
    return df

# =========================
# 3. 데이터 로드 / 저장 (백업 기능 포함)
# =========================
def load_targets():
    if TARGET_FILE.exists():
        # 계약번호는 문자열로 읽기
        df = pd.read_csv(TARGET_FILE, dtype={"계약번호": str})
        return normalize_columns(df)
    return pd.DataFrame()

def save_targets(df: pd.DataFrame, action_type="Upload"):
    """
    데이터 저장 시:
    1. 기존 파일 백업
    2. 데이터 저장
    3. 로그 기록
    """
    df = normalize_columns(df)
    
    # 계약번호 .0 제거 로직
    if "계약번호" in df.columns:
        df["계약번호"] = df["계약번호"].astype(str).str.replace(r'\.0$', '', regex=True)
    
    with FileLock(str(LOCK_FILE)):
        # 1. 기존 파일이 있다면 백업 생성
        if TARGET_FILE.exists():
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_path = BACKUP_DIR / f"targets_backup_{timestamp}.csv"
            shutil.copy(TARGET_FILE, backup_path)
        
        # 2. 파일 저장
        df.to_csv(TARGET_FILE, index=False)
        
        # 3. 로그 기록
        log_activity(action_type, f"총 {len(df)}건 저장 완료 (백업 생성됨)")

def load_results():
    if RESULT_FILE.exists():
        df = pd.read_csv(RESULT_FILE, dtype={"계약번호": str})
        return normalize_columns(df)
    return pd.DataFrame()

def save_result(row: dict):
    with FileLock(str(LOCK_FILE)):
        df = load_results()
        
        # 계약번호 처리
        contract_id = str(row["계약번호"]).replace(".0", "")
        row["계약번호"] = contract_id
        
        if not df.empty and "계약번호" in df.columns:
            idx = df[df["계약번호"] == contract_id].index
            if not idx.empty:
                # Update
                for key, value in row.items():
                    df.loc[idx[0], key] = value
            else:
                # Insert
                df = pd.concat([df, pd.DataFrame([row])], ignore_index=True)
        else:
            df = pd.DataFrame([row])

        df.to_csv(RESULT_FILE, index=False)

def load_reason_map():
    if REASON_FILE.exists():
        return pd.read_csv(REASON_FILE)
    return pd.DataFrame(columns=["해지사유", "불만유형"])
