import streamlit as st
from storage import load_results

st.title("📊 조사 현황")

df = load_results()
if df.empty:
    st.info("등록된 조사 결과가 없습니다.")
else:
    st.metric("총 등록 건수", len(df))
    st.dataframe(df)
