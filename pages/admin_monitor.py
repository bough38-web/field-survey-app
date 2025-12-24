import streamlit as st
import pandas as pd
import altair as alt
from storage import load_results, check_admin_password

# 🔒 인증 실행
check_admin_password()

st.title("📊 등록 결과 모니터링")
results = load_results()

if results.empty:
    st.info("데이터가 없습니다.")
    st.stop()

# 처리일시 기준 정렬
if "처리일시" in results.columns:
    results["처리일시"] = pd.to_datetime(results["처리일시"], errors='coerce')
    results = results.sort_values("처리일시", ascending=False)

c1, c2, c3 = st.columns(3)
with c1: st.metric("총 건수", len(results))
with c2: st.metric("최다 지사", results["관리지사"].mode()[0] if "관리지사" in results.columns else "-")
with c3: st.metric("최근 업데이트", results["처리일시"].max().strftime("%m-%d %H:%M") if "처리일시" in results.columns else "-")

st.markdown("---")

col1, col2 = st.columns(2)
with col1:
    if "관리지사" in results.columns:
        cnt = results["관리지사"].value_counts().reset_index()
        cnt.columns = ["지사", "건수"]
        st.altair_chart(alt.Chart(cnt).mark_bar().encode(x="건수", y=alt.Y("지사", sort="-x")), use_container_width=True)
with col2:
    if "해지사유" in results.columns:
        cnt = results["해지사유"].value_counts().reset_index()
        cnt.columns = ["사유", "건수"]
        st.altair_chart(alt.Chart(cnt).mark_arc().encode(theta="건수", color="사유"), use_container_width=True)

st.markdown("### 📋 상세 내역")
st.dataframe(results, use_container_width=True)
st.download_button("CSV 다운로드", results.to_csv(index=False).encode('utf-8-sig'), "results.csv")
