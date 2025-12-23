import streamlit as st
from storage import load_actions

st.title("📊 조치 현황 모니터링")

actions = load_actions()

if actions.empty:
    st.info("아직 등록된 조치 내역이 없습니다.")
else:
    st.metric("총 조치 건수", len(actions))
    st.dataframe(actions)