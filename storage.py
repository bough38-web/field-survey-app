import pandas as pd
from pathlib import Path
from filelock import FileLock
import shutil
from datetime import datetime
import os
import streamlit as st
import time

# =========================
# 기본 경로 및 설정
# =========================
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

# =========================
# 🔐 관리자 인증 (Admin Auth)
# =========================
def check_admin_password():
    """관리자 비밀번호(3867) 확인 함수"""
    if "is_admin" not in st.session_state:
        st.session_state["is_admin"] = False

    if st.session_state["is_admin"]:
        if st.sidebar.button("🔒 관리자 로그아웃", key="logout_btn"):
            st.session_state["is_admin"] = False
            st.rerun()
        return

    # --- 로그인 UI ---
    st.markdown("""
    <style>
        .login-box {
            max-width: 350px; margin: 50px auto; padding: 30px;
            background: white; border-radius: 12px;
            box-shadow: 0 4px 15px rgba(0,0,0,0.1); text-align: center;
            border: 1px solid #e2e8f0;
        }
        .login-btn button { width: 100%; background-color: #2563eb; color: white; }
    </style>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("""
        <div class="login-box">
            <h3>🔒 관리자 접속</h3>
            <p style="color:#64748b; font-size:0.9em;">보안을 위해 비밀번호를 입력하세요.</p>
        </div>
        """, unsafe_allow_html=True)
        
        password = st.text_input("Password", type="password", placeholder="Access Code", label_visibility="collapsed")
        
        st.markdown('<div class="login-btn">', unsafe_allow_html=True)
        if st.button("로그인", type="primary", use_container_width=True):
            if password == "3867":
                st.session_state["is_admin"] = True
                st.toast("✅ 관리자 권한 승인", icon="🔓")
                time.sleep(0.5)
                st.rerun()
            else:
                st.error("❌ 비밀번호가 틀렸습니다.")
        st.markdown('</div>', unsafe_allow_html=True)
    
    st.stop() # 인증 안 되면 여기서 멈춤

# =========================
# 로그 및 데이터 관리 함수들
# =========================
def log_activity(action, details, user="System"):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    new_log = pd.DataFrame([{"일시": timestamp, "작업자": user, "작업유형": action, "상세내용": details}])
    with FileLock(str(LOCK_FILE)):
        if LOG_FILE.exists():
            new_log.to_csv(LOG_FILE, mode='a', header=False, index=False)
        else:
            new_log.to_csv(LOG_FILE, index=False)

def load_logs():
    if LOG_FILE.exists():
        return pd.read_csv(LOG_FILE).sort_values("일시", ascending=False)
    return pd.DataFrame(columns=["일시", "작업자", "작업유형", "상세내용"])

def normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty: return df
    df = df.copy()
    df.columns = (df.columns.astype(str).str.replace("\n", "").str.replace(" ", "").str.replace("_", "").str.strip())
    for col in ["이름(담당자)", "구역담당자"]:
        if col in df.columns and "담당자" not in df.columns:
            df["담당자"] = df[col]
    if "상호" not in df.columns:
        for alt in ["상호명", "업체명", "고객명"]:
            if alt in df.columns:
                df["상호"] = df[alt]
                break
        else:
            df["상호"] = ""
    return df.loc[:, ~df.columns.duplicated()]

def load_targets():
    if TARGET_FILE.exists():
        df = pd.read_csv(TARGET_FILE, dtype={"계약번호": str})
        return normalize_columns(df)
    return pd.DataFrame()

def save_targets(df: pd.DataFrame, action_type="Upload"):
    df = normalize_columns(df)
    if "계약번호" in df.columns:
        df["계약번호"] = df["계약번호"].astype(str).str.replace(r'\.0$', '', regex=True)
    
    with FileLock(str(LOCK_FILE)):
        if TARGET_FILE.exists():
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            shutil.copy(TARGET_FILE, BACKUP_DIR / f"targets_backup_{timestamp}.csv")
        df.to_csv(TARGET_FILE, index=False)
        log_activity(action_type, f"총 {len(df)}건 저장 (백업 완료)")

def load_results():
    if RESULT_FILE.exists():
        df = pd.read_csv(RESULT_FILE, dtype={"계약번호": str})
        return normalize_columns(df)
    return pd.DataFrame()

def save_result(row: dict):
    with FileLock(str(LOCK_FILE)):
        df = load_results()
        contract_id = str(row["계약번호"]).replace(".0", "")
        row["계약번호"] = contract_id
        
        if not df.empty and "계약번호" in df.columns:
            idx = df[df["계약번호"] == contract_id].index
            if not idx.empty:
                for key, value in row.items():
                    df.loc[idx[0], key] = value
            else:
                df = pd.concat([df, pd.DataFrame([row])], ignore_index=True)
        else:
            df = pd.DataFrame([row])
        df.to_csv(RESULT_FILE, index=False)

def load_reason_map():
    if REASON_FILE.exists(): return pd.read_csv(REASON_FILE)
    return pd.DataFrame(columns=["해지사유", "불만유형"])
