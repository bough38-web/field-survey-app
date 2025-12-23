import streamlit as st
import pandas as pd
from storage import match_branch_owner

st.title("📋 조사 대상 업로드")

uploaded = st.file_uploader(
    "조사 대상 파일 업로드 (Excel / CSV)",
    type=["xlsx", "csv"]
)

if uploaded:
    if uploaded.name.endswith("csv"):
        df = pd.read_csv(uploaded)
    else:
        df = pd.read_excel(uploaded)

    df = match_branch_owner(df)

    st.success("자동 매칭 완료")
    st.dataframe(df)

    df.to_csv("storage/survey_targets.csv", index=False)
