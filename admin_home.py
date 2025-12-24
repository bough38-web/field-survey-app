import streamlit as st
import pandas as pd
from storage import load_targets, load_results, check_admin_password

# 🔒 관리자 인증
check_admin_password()

st.title("📌 관리자 홈 (Admin Hub)")
st.markdown("현장조사 데이터 관리 및 모니터링 허브입니다.")
st.markdown("---")

# 대시보드 요약
targets = load_targets()
results = load_results()

col1, col2, col3 = st.columns(3)
total_target = len(targets)
total_done = len(results)
progress = (total_done / total_target * 100) if total_target > 0 else 0

with col1: st.metric("총 조사 대상", f"{total_target}건")
with col2: st.metric("조치 완료", f"{total_done}건")
with col3: st.metric("진행률", f"{progress:.1f}%")

st.progress(progress / 100)

st.info("좌측 메뉴에서 [조사 대상 업로드] 또는 [결과 모니터링]을 이용하세요.")

if not results.empty:
    with st.expander("📊 최근 조치 내역 (최신 5건)"):
        st.dataframe(results.tail(5), use_container_width=True)
