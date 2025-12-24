import streamlit as st
import pandas as pd
import altair as alt
from storage import load_results, check_admin_password

# 🔒 관리자 인증
check_admin_password()

st.markdown("""
<style>
    @import url("https://cdn.jsdelivr.net/gh/orioncactus/pretendard@v1.3.8/dist/web/static/pretendard.css");
    .stApp { background-color: #f8fafc; font-family: 'Pretendard', sans-serif; }
    .stContainer { background-color: #ffffff; border-radius: 12px; padding: 20px; box-shadow: 0 4px 6px rgba(0,0,0,0.05); border: 1px solid #e2e8f0; }
</style>
""", unsafe_allow_html=True)

st.title("📊 등록 결과 모니터링 (Admin)")

results = load_results()
if results.empty:
    st.info("📭 아직 등록된 조치 결과가 없습니다.")
    st.stop()

if "계약번호" in results.columns:
    results["계약번호"] = results["계약번호"].astype(str).str.replace(r'\.0$', '', regex=True)

if "처리일시" in results.columns:
    results["처리일시"] = pd.to_datetime(results["처리일시"], errors='coerce')
    results = results.sort_values(by="처리일시", ascending=False)

with st.container():
    col1, col2, col3, col4 = st.columns(4)
    total_count = len(results)
    top_branch = results["관리지사"].value_counts().idxmax() if "관리지사" in results.columns and not results["관리지사"].empty else "-"
    today = pd.Timestamp.now().strftime("%Y-%m-%d")
    today_count = len(results[results["처리일시"].dt.strftime("%Y-%m-%d") == today]) if "처리일시" in results.columns else 0
    
    with col1: st.metric("총 등록 건수", f"{total_count}건")
    with col2: st.metric("오늘 신규", f"{today_count}건")
    with col3: st.metric("최다 지사", top_branch)
    with col4: st.metric("업데이트", results["처리일시"].max().strftime("%m-%d %H:%M") if "처리일시" in results.columns else "-")

st.markdown("---")
st.subheader("📈 데이터 분석")
cc1, cc2 = st.columns(2)
with cc1:
    if "관리지사" in results.columns:
        bc = results["관리지사"].value_counts().reset_index()
        bc.columns=["지사","건수"]
        st.altair_chart(alt.Chart(bc).mark_bar().encode(x="건수", y=alt.Y("지사", sort="-x")).properties(title="지사별 등록"), use_container_width=True)
with cc2:
    if "해지사유" in results.columns:
        rc = results["해지사유"].value_counts().reset_index()
        rc.columns=["사유","건수"]
        st.altair_chart(alt.Chart(rc).mark_arc().encode(theta="건수", color="사유").properties(title="사유 분포"), use_container_width=True)

st.markdown("---")
st.subheader("📋 상세 내역")
sq = st.text_input("🔍 검색 (상호/계약번호/담당자)", placeholder="검색어 입력")
filt_df = results.copy()
if sq:
    q = sq.lower()
    mask = filt_df.astype(str).apply(lambda x: x.str.lower().str.contains(q)).any(axis=1)
    filt_df = filt_df[mask]

st.dataframe(filt_df, use_container_width=True, hide_index=True)
st.download_button("📥 CSV 다운로드", filt_df.to_csv(index=False).encode('utf-8-sig'), "results.csv", "text/csv")
