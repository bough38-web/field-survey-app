import pandas as pd
from pathlib import Path
from filelock import FileLock
import shutil
from datetime import datetime
import os
import streamlit as st
import time

# --- 경로 설정 ---
BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "storage"
BACKUP_DIR = DATA_DIR / "backups"
LOG_FILE = DATA_DIR / "activity_log.csv"

DATA_DIR.mkdir(exist_ok=True)
BACKUP_DIR.mkdir(exist_ok=True)

TARGET_FILE = DATA_DIR / "survey_targets.csv"
RESULT_FILE = DATA_DIR / "survey_results.csv"
REASON_FILE = BASE_DIR / "reason_map.csv"
LOCK_FILE = DATA_DIR / "data.lock"

# --- 🔐 관리자 인증 함수 ---
def check_admin_password():
    """관리자 비밀번호(3867) 확인 및 로그인 UI"""
    if "is_admin" not in st.session_state:
        st.session_state["is_admin"] = False

    # 이미 로그인 된 경우
    if st.session_state["is_admin"]:
        # 사이드바에 로그아웃 버튼 배치
        with st.sidebar:
            if st.button("🔒 관리자 로그아웃", type="secondary", use_container_width=True):
                st.session_state["is_admin"] = False
                st.rerun()
        return

    # 로그인 안 된 경우: 화면 전체를 로그인 창으로 막음
    st.markdown("""
    <style>
        .login-container {
            max-width: 350px; margin: 100px auto; padding: 30px;
            background: white; border-radius: 12px;
            box-shadow: 0 4px 20px rgba(0,0,0,0.1); text-align: center;
            border: 1px solid #e2e8f0;
        }
    </style>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        st.markdown('<div class="login-container"><h3>🔒 관리자 접속</h3><p style="color:#64748b; font-size:0.8rem;">관리자 코드를 입력하세요.</p></div>', unsafe_allow_html=True)
        password = st.text_input("Password", type="password", placeholder="Code: 3867", label_visibility="collapsed")
        
        if st.button("로그인", type="primary", use_container_width=True):
            if password == "3867":
                st.session_state["is_admin"] = True
                st.toast("✅ 로그인 성공!", icon="🔓")
                time.sleep(0.5)
                st.rerun()
            else:
                st.error("⛔ 비밀번호가 틀렸습니다.")
    
    st.stop() # 코드가 여기 밑으로 진행되지 않도록 차단

# --- 데이터 처리 함수들 ---
def normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty: return df
    df = df.copy()
    df.columns = (df.columns.astype(str).str.replace("\n", "").str.replace(" ", "").str.replace("_", "").str.strip())
    # 컬럼명 표준화
    for col in ["이름(담당자)", "구역담당자"]:
        if col in df.columns and "담당자" not in df.columns: df["담당자"] = df[col]
    if "상호" not in df.columns:
        for alt in ["상호명", "업체명", "고객명"]:
            if alt in df.columns: df["상호"] = df[alt]; break
        else: df["상호"] = ""
    # 해지일자 표준화
    if "해지_해지일자" in df.columns:
        df.rename(columns={"해지_해지일자": "해지일자"}, inplace=True)
    return df.loc[:, ~df.columns.duplicated()]

def clean_contract_id(df):
    if "계약번호" in df.columns:
        df["계약번호"] = df["계약번호"].astype(str).str.replace(r'\.0$', '', regex=True)
    return df

def load_targets():
    if TARGET_FILE.exists():
        df = pd.read_csv(TARGET_FILE, dtype={"계약번호": str})
        df = normalize_columns(df)
        return clean_contract_id(df)
    return pd.DataFrame()

def save_targets(df: pd.DataFrame, action_type="Upload"):
    df = normalize_columns(df)
    df = clean_contract_id(df)
    with FileLock(str(LOCK_FILE)):
        if TARGET_FILE.exists():
            shutil.copy(TARGET_FILE, BACKUP_DIR / f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv")
        df.to_csv(TARGET_FILE, index=False)
        log_activity(action_type, f"{len(df)}건 저장")

def load_results():
    if RESULT_FILE.exists():
        df = pd.read_csv(RESULT_FILE, dtype={"계약번호": str})
        df = normalize_columns(df)
        return clean_contract_id(df)
    return pd.DataFrame()

def save_result(row: dict):
    with FileLock(str(LOCK_FILE)):
        df = load_results()
        row["계약번호"] = str(row["계약번호"]).replace(".0", "")
        
        if not df.empty and "계약번호" in df.columns:
            # 업데이트
            idx = df[df["계약번호"] == row["계약번호"]].index
            if not idx.empty:
                for k, v in row.items(): df.loc[idx[0], k] = v
            else:
                df = pd.concat([df, pd.DataFrame([row])], ignore_index=True)
        else:
            # 신규 추가
            df = pd.DataFrame([row])
            
        df.to_csv(RESULT_FILE, index=False)

def log_activity(action, details, user="System"):
    log_entry = pd.DataFrame([{"일시": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "작업자": user, "작업유형": action, "상세내용": details}])
    with FileLock(str(LOCK_FILE)):
        mode = 'a' if LOG_FILE.exists() else 'w'
        log_entry.to_csv(LOG_FILE, mode=mode, header=(not LOG_FILE.exists()), index=False)

def load_logs():
    if LOG_FILE.exists(): return pd.read_csv(LOG_FILE).sort_values("일시", ascending=False)
    return pd.DataFrame()

def load_reason_map():
    if REASON_FILE.exists(): return pd.read_csv(REASON_FILE)
    return pd.DataFrame(columns=["해지사유", "불만유형"])
