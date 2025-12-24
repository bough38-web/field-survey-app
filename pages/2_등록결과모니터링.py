import streamlit as st
import pandas as pd
import altair as alt
from storage import load_results, check_admin_password

# ==========================================
# 1. 보안 및 설정
# ==========================================
# [중요] 관리자 인증 실행
check_admin_password()

# 스타일 적용 (High-End UI)
st.markdown("""
<style>
    @import url("https://cdn.jsdelivr.net/gh/orioncactus/pretendard@v1.3.8/dist/web/static/pretendard.css");
    .stApp { background-color: #f8fafc; font-family: 'Pretendard', sans-serif; }
    div[data-testid="stMetricValue"] { font-size: 1.8rem; font-weight: 700; color: #2563eb; }
    div[data-testid="stMetricLabel"] { font-size: 0.9rem; color: #64748b; }
    .stContainer { background-color: #ffffff; border-radius: 12px; padding: 20px; box-shadow: 0 4px 6px rgba(0,0,0,0.05); border: 1px solid #e2e8f0; }
</style>
""", unsafe_allow_html=True)

st.title("📊 등록 결과 모니터링 (Admin)")
st.markdown("현장 조사 후 등록된 **조치 결과 데이터**를 실시간으로 조회하고 분석합니다.")

# ==========================================
# 2. 데이터 로드 및 전처리
# ==========================================
results = load_results()

if results.empty:
    st.info("📭 아직 등록된 조치 결과가 없습니다.")
    st.stop()

# [개선] 전처리 로직 통합 (중복 제거 및 최신순 정렬)
if "계약번호" in results.columns:
    results["계약번호"] = results["계약번호"].astype(str).str.replace(r'\.0$', '', regex=True)

# 날짜 형식 변환 및 정렬 (최신순)
if "처리일시" in results.columns:
    results["처리일시"] = pd.to_datetime(results["처리일시"], errors='coerce')
    results = results.sort_values(by="처리일시", ascending=False) # 최신 데이터가 위로

# ==========================================
# 3. 현황 요약 (Metrics)
# ==========================================
with st.container():
    col1, col2, col3, col4 = st.columns(4)
    
    total_count = len(results)
    
    # 최다 등록 지사
    if "관리지사" in results.columns and not results["관리지사"].empty:
        top_branch = results["관리지사"].value_counts().idxmax()
    else:
        top_branch = "-"

    # 금일 등록 건수 (처리일시 기준)
    today = pd.Timestamp.now().strftime("%Y-%m-%d")
    today_count = len(results[results["처리일시"].dt.strftime("%Y-%m-%d") == today])

    # 최근 업데이트
    if not results["처리일시"].isna().all():
        last_update = results["처리일시"].max().strftime("%Y-%m-%d %H:%M")
    else:
        last_update = "-"

    with col1: st.metric("총 등록 건수", f"{total_count:,}건")
    with col2: st.metric("오늘 신규 등록", f"{today_count:,}건", delta="Today")
    with col3: st.metric("최다 등록 지사", top_branch)
    with col4: st.metric("최근 업데이트", last_update)

st.markdown("---")

# ==========================================
# 4. 시각화 (Charts) - 관리자용 분석
# ==========================================
st.subheader("📈 데이터 시각화 분석")

chart_col1, chart_col2 = st.columns(2)

# [차트 1] 지사별 등록 건수 (Bar Chart)
with chart_col1:
    if "관리지사" in results.columns:
        branch_counts = results["관리지사"].value_counts().reset_index()
        branch_counts.columns = ["지사", "건수"]
        
        chart_branch = alt.Chart(branch_counts).mark_bar(cornerRadius=5).encode(
            x=alt.X("건수:Q", title=None),
            y=alt.Y("지사:N", sort="-x", title=None),
            color=alt.value("#3b82f6"),
            tooltip=["지사", "건수"]
        ).properties(title="🏢 지사별 등록 현황", height=250)
        st.altair_chart(chart_branch, use_container_width=True)

# [차트 2] 해지 사유 분포 (Donut Chart)
with chart_col2:
    if "해지사유" in results.columns:
        reason_counts = results["해지사유"].value_counts().reset_index()
        reason_counts.columns = ["사유", "건수"]
        
        chart_reason = alt.Chart(reason_counts).mark_arc(innerRadius=50).encode(
            theta=alt.Theta("건수", stack=True),
            color=alt.Color("사유", legend=alt.Legend(title="사유 목록")),
            tooltip=["사유", "건수"],
            order=alt.Order("건수", sort="descending")
        ).properties(title="🧩 해지 사유 분포", height=250)
        st.altair_chart(chart_reason, use_container_width=True)

# ==========================================
# 5. 상세 데이터 필터링 및 테이블
# ==========================================
st.markdown("---")
st.subheader("📋 등록 내역 상세 조회")

# 검색 및 필터
f_col1, f_col2 = st.columns([2, 1])
with f_col1:
    search_query = st.text_input("🔍 통합 검색", placeholder="계약번호, 상호, 담당자명으로 검색...")
with f_col2:
    if "관리지사" in results.columns:
        branch_filter = st.selectbox("지사 필터", ["전체"] + sorted(results["관리지사"].unique().tolist()))
    else:
        branch_filter = "전체"

# 필터링 로직
filtered_df = results.copy()

# 1. 지사 필터
if branch_filter != "전체":
    filtered_df = filtered_df[filtered_df["관리지사"] == branch_filter]

# 2. 검색어 필터 (대소문자 무시)
if search_query:
    query = search_query.lower()
    mask = (
        filtered_df["계약번호"].astype(str).str.lower().str.contains(query) | 
        filtered_df["상호"].astype(str).str.lower().str.contains(query) |
        filtered_df["담당자"].astype(str).str.lower().str.contains(query)
    )
    filtered_df = filtered_df[mask]

# 결과 정보 표시
st.caption(f"검색 결과: 총 **{len(filtered_df)}**건")

# 데이터 테이블 표시
st.dataframe(
    filtered_df,
    use_container_width=True,
    hide_index=True,
    column_config={
        "처리일시": st.column_config.DatetimeColumn("처리일시", format="YYYY-MM-DD HH:mm"),
        "계약번호": st.column_config.TextColumn("계약번호"),
    }
)

# ==========================================
# 6. 다운로드 기능
# ==========================================
csv = filtered_df.to_csv(index=False).encode('utf-8-sig')

st.download_button(
    label="📥 조회 결과 다운로드 (CSV)",
    data=csv,
    file_name=f"survey_results_{pd.Timestamp.now().strftime('%Y%m%d')}.csv",
    mime="text/csv",
    type="primary",
    use_container_width=True
)
