import streamlit as st
import pandas as pd
from storage import load_targets, load_results, check_admin_password

# 🔒 관리자 인증 실행
check_admin_password()

# =========================
# 관리자 대시보드 내용
# =========================
st.title("📌 현장조사 관리 허브 (Admin)")
st.markdown("---")

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

st.subheader("📢 관리자 공지")
st.info("현재 관리자 권한으로 접속 중입니다. 좌측 메뉴에서 데이터 업로드 및 모니터링을 수행할 수 있습니다.")

if not results.empty:
    with st.expander("📊 최근 조치 내역 (최신 5건)"):
        st.dataframe(results.tail(5), use_container_width=True)