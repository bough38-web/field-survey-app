import streamlit as st
import pandas as pd
from storage import load_targets, load_results

st.set_page_config(page_title="현장조사 관리 허브", layout="wide")

st.title("📌 현장조사 관리 허브")
st.markdown("---")

# 데이터 로드
targets = load_targets()
results = load_results()

col1, col2, col3 = st.columns(3)

total_target = len(targets)
total_done = len(results)
progress = (total_done / total_target * 100) if total_target > 0 else 0

with col1:
    st.metric("총 조사 대상", f"{total_target}건")
with col2:
    st.metric("조치 완료", f"{total_done}건")
with col3:
    st.metric("진행률", f"{progress:.1f}%")

st.progress(progress / 100)

st.subheader("📢 공지사항")
st.info("좌측 메뉴에서 [조사 대상 업로드] 또는 [사유 등록 대상]을 선택하여 업무를 진행해주세요.")

if not results.empty:
    with st.expander("📊 최근 조치 내역 (최신 5건)"):
        st.dataframe(results.tail(5)[["관리지사", "계약번호", "상호", "해지사유", "담당자"]])
