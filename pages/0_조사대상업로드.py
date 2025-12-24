import streamlit as st
import pandas as pd
from io import StringIO
import os
import time
# check_admin_password 추가 Import
from storage import save_targets, load_targets, load_logs, normalize_columns, BACKUP_DIR, check_admin_password

# Page Config
st.set_page_config(page_title="데이터 관리 센터", layout="wide", page_icon="💾")

# 🔒 관리자 인증 실행
check_admin_password()

st.set_page_config(page_title="조사 대상 업로드", layout="wide")
st.title("📋 조사 대상 업로드")

method = st.radio("데이터 반영 방법", ["파일 업로드", "엑셀 복사 붙여넣기"])

def clean_headers(df):
    df = df.copy()
    df.columns = (
        df.columns.astype(str)
        .str.replace("\n", "")
        .str.replace(" ", "")
        .str.replace("_", "")
        .str.strip()
    )
    return df

if method == "파일 업로드":
    file = st.file_uploader("엑셀 또는 CSV", type=["xlsx", "csv"])
    if file:
        df = pd.read_excel(file) if file.name.endswith(".xlsx") else pd.read_csv(file)
        df = clean_headers(df)
        df = normalize_columns(df)

        if "계약번호" in df.columns:
            df["계약번호"] = df["계약번호"].astype(str)

        save_targets(df)
        st.success("✅ 업로드 완료")
        st.dataframe(df.head(), use_container_width=True)

else:
    pasted = st.text_area("엑셀 붙여넣기", height=300)
    if pasted.strip():
        df = pd.read_csv(StringIO(pasted), sep="\t")
        df = clean_headers(df)
        df = normalize_columns(df)

        if "계약번호" in df.columns:
            df["계약번호"] = df["계약번호"].astype(str)

        save_targets(df)
        st.success("✅ 붙여넣기 완료")
        st.dataframe(df.head(), use_container_width=True)
