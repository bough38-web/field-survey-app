import streamlit as st
import pandas as pd
from storage import match_branch_owner, save_targets

st.title("📋 조사 대상 업로드")

uploaded_file = st.file_uploader(
    "엑셀 또는 CSV 업로드",
    type=["xlsx", "csv"]
)

if uploaded_file:
    # 1️⃣ 파일 형식 자동 판별
    if uploaded_file.name.endswith(".csv"):
        df = pd.read_csv(uploaded_file)
    else:
        df = pd.read_excel(uploaded_file)

    # 2️⃣ (선택) 컬럼명 공백/줄바꿈 정리
    df.columns = df.columns.str.strip()

    # 3️⃣ 지사/담당자 자동 매칭
    df = match_branch_owner(df)

    # 4️⃣ 앱 내부 CSV로 저장
    save_targets(df)

    st.success("조사 대상이 앱에 반영되었습니다.")
    st.dataframe(df.head())
