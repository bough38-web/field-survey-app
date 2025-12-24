import streamlit as st
import pandas as pd
import altair as alt
from storage import load_targets, load_results

# ==========================================
# 1. 페이지 설정 및 스타일링
# ==========================================
st.set_page_config(page_title="종합 현황 대시보드", layout="wide", page_icon="📈")

# 커스텀 CSS로 여백 조정 및 카드 스타일링
st.markdown("""
<style>
    [data-testid="stMetricValue"] {
        font-size: 2.5rem;
        font-weight: 700;
        color: #0f172a;
    }
    .stContainer {
        border: 1px solid #e2e8f0;
        border-radius: 0.5rem;
        padding: 1rem;
        box-shadow: 0 1px 2px 0 rgba(0, 0, 0, 0.05);
    }
</style>
""", unsafe_allow_html=True)

st.title("📈 종합 현황 대시보드")
st.markdown("데이터 기반의 **실시간 진척률** 및 **해지 사유 분석** 리포트입니다.")

# ==========================================
# 2. 데이터 로드 및 전처리
# ==========================================
targets = load_targets()
results = load_results()

# 지사 정렬 순서 (User Request)
BRANCH_ORDER = ["중앙", "강북", "서대문", "고양", "의정부", "남양주", "강릉", "원주"]

# 데이터 전처리 함수
def preprocess_data(targets, results):
    # 1. 대상 데이터 정리
    if not targets.empty:
        if "관리지사" in targets.columns:
            targets["관리지사표시"] = targets["관리지사"].str.replace("지사", "").str.strip()
        else:
            targets["관리지사표시"] = "미지정"
        targets["계약번호"] = targets["계약번호"].astype(str)
    
    # 2. 결과 데이터 정리
    if not results.empty:
        if "관리지사" in results.columns:
            results["관리지사표시"] = results["관리지사"].str.replace("지사", "").str.strip()
        else:
            results["관리지사표시"] = "미지정"
        results["계약번호"] = results["계약번호"].astype(str)

    return targets, results

targets, results = preprocess_data(targets, results)

if targets.empty:
    st.warning("⚠️ 분석할 데이터가 없습니다. 먼저 '조사 대상 업로드'를 진행해주세요.")
    st.stop()

# ==========================================
# 3. 사이드바 필터 (UX 고려)
# ==========================================
st.sidebar.header("🔍 상세 필터")

# 지사 필터
available_branches = [b for b in BRANCH_ORDER if b in targets["관리지사표시"].unique()]
other_branches = [b for b in targets["관리지사표시"].unique() if b not in BRANCH_ORDER]
final_branch_order = available_branches + other_branches

selected_branches = st.sidebar.multiselect(
    "지사 선택",
    final_branch_order,
    default=final_branch_order,
    placeholder="지사를 선택하세요"
)

# 담당자 필터
available_owners = sorted(targets["담당자"].dropna().unique().tolist()) if "담당자" in targets.columns else []
selected_owners = st.sidebar.multiselect(
    "담당자 선택",
    available_owners,
    default=[],
    placeholder="전체 담당자 (선택 시 필터링)"
)

# 필터링 적용
filtered_targets = targets[targets["관리지사표시"].isin(selected_branches)]
if selected_owners:
    filtered_targets = filtered_targets[filtered_targets["담당자"].isin(selected_owners)]

# 결과 데이터도 동일한 계약번호 기준으로 필터링
target_ids = filtered_targets["계약번호"].unique()
filtered_results = results[results["계약번호"].isin(target_ids)] if not results.empty else pd.DataFrame()

# ==========================================
# 4. KPI Scorecard (핵심 지표)
# ==========================================
st.markdown("### 🚀 핵심 지표 (KPI)")

col1, col2, col3, col4 = st.columns(4)

total_tgt = len(filtered_targets)
total_res = len(filtered_results)
progress_rate = (total_res / total_tgt * 100) if total_tgt > 0 else 0
remain_cnt = total_tgt - total_res

with col1:
    st.metric("총 대상", f"{total_tgt:,.0f}건")
with col2:
    st.metric("조치 완료", f"{total_res:,.0f}건", delta=f"{progress_rate:.1f}% 달성")
with col3:
    st.metric("잔여 대상", f"{remain_cnt:,.0f}건", delta_color="inverse")
with col4:
    # 가장 많이 발생한 해지사유
    if not filtered_results.empty and "해지사유" in filtered_results.columns:
        top_reason = filtered_results["해지사유"].mode()[0]
    else:
        top_reason = "-"
    st.metric("최다 해지사유", top_reason)

st.markdown("---")

# ==========================================
# 5. 시각화 (Altair 고급 차트)
# ==========================================

# ------------------------------------------
# [데이터 집계] 지사별 진척률
# ------------------------------------------
branch_stats = filtered_targets.groupby("관리지사표시").size().reset_index(name="대상건수")
if not filtered_results.empty:
    done_stats = filtered_results.groupby("관리지사표시").size().reset_index(name="완료건수")
    branch_stats = pd.merge(branch_stats, done_stats, on="관리지사표시", how="left").fillna(0)
else:
    branch_stats["완료건수"] = 0

branch_stats["진행률"] = (branch_stats["완료건수"] / branch_stats["대상건수"] * 100).round(1)

# ------------------------------------------
# [차트 1] 지사별 진척 현황 (이중 막대 그래프)
# ------------------------------------------
chart_base = alt.Chart(branch_stats).encode(
    x=alt.X("관리지사표시", sort=BRANCH_ORDER, title=None, axis=alt.Axis(labelAngle=0))
)

# 배경(전체 대상) - 회색
bar_bg = chart_base.mark_bar(color="#e2e8f0", size=30).encode(
    y=alt.Y("대상건수", title="건수"),
    tooltip=["관리지사표시", "대상건수"]
)

# 전경(완료) - 파란색
bar_fg = chart_base.mark_bar(color="#3b82f6", size=20).encode(
    y=alt.Y("완료건수"),
    tooltip=["관리지사표시", "완료건수", "진행률"]
)

# 텍스트 라벨 (진행률)
text_rate = chart_base.mark_text(dy=-10, color="black").encode(
    y="완료건수",
    text=alt.Text("진행률", format=".1f", suffix="%")
)

chart1 = (bar_bg + bar_fg + text_rate).properties(
    title="🏢 지사별 진행 현황 (대상 vs 완료)",
    height=350
)

# ------------------------------------------
# [차트 2] 해지 사유 분석 (도넛 차트)
# ------------------------------------------
if not filtered_results.empty and "해지사유" in filtered_results.columns:
    reason_counts = filtered_results["해지사유"].value_counts().reset_index()
    reason_counts.columns = ["해지사유", "건수"]
    
    base_pie = alt.Chart(reason_counts).encode(
        theta=alt.Theta("건수", stack=True),
        color=alt.Color("해지사유", legend=alt.Legend(title="사유 목록", orient="bottom"))
    )
    
    pie = base_pie.mark_arc(outerRadius=120, innerRadius=80).encode(
        tooltip=["해지사유", "건수"]
    )
    
    text_pie = base_pie.mark_text(radius=140).encode(
        text=alt.Text("건수"),
        order=alt.Order("건수", sort="descending"),
        color=alt.value("black")  
    )
    
    chart2 = (pie + text_pie).properties(
        title="📉 해지 사유 분포",
        height=350
    )
else:
    chart2 = alt.Chart(pd.DataFrame({"text": ["데이터 없음"]})).mark_text().encode(text="text").properties(title="📉 해지 사유 분포", height=350)

# ------------------------------------------
# [차트 3] 담당자별 실적 Top 10
# ------------------------------------------
if not filtered_results.empty and "담당자" in filtered_results.columns:
    owner_counts = filtered_results["담당자"].value_counts().reset_index()
    owner_counts.columns = ["담당자", "처리건수"]
    owner_counts = owner_counts.head(10)
    
    chart3 = alt.Chart(owner_counts).mark_bar().encode(
        x=alt.X("처리건수", title="처리 건수"),
        y=alt.Y("담당자", sort="-x", title=None),
        color=alt.value("#10b981"), # Green
        tooltip=["담당자", "처리건수"]
    ).properties(
        title="🏆 담당자별 처리 실적 (Top 10)",
        height=350
    )
else:
    chart3 = alt.Chart(pd.DataFrame()).mark_text().properties(title="🏆 담당자별 실적", height=350)

# ------------------------------------------
# [차트 4] 일자별 등록 추이 (시계열)
# ------------------------------------------
if not filtered_results.empty and "처리일시" in filtered_results.columns:
    # 처리일시를 날짜로 변환 (오류 방지)
    filtered_results["처리날짜"] = pd.to_datetime(filtered_results["처리일시"], errors='coerce').dt.date
    daily_counts = filtered_results.groupby("처리날짜").size().reset_index(name="건수")
    
    chart4 = alt.Chart(daily_counts).mark_area(
        line={'color':'darkblue'},
        color=alt.Gradient(
            gradient='linear',
            stops=[alt.GradientStop(color='darkblue', offset=0),
                   alt.GradientStop(color='white', offset=1)],
            x1=1, x2=1, y1=1, y2=0
        )
    ).encode(
        x=alt.X("처리날짜:T", title="날짜"),
        y=alt.Y("건수:Q", title="등록 건수"),
        tooltip=["처리날짜", "건수"]
    ).properties(
        title="📅 일별 처리 추이",
        height=350
    )
else:
    chart4 = alt.Chart(pd.DataFrame()).mark_text().properties(title="📅 일별 처리 추이", height=350)


# ==========================================
# 6. 레이아웃 배치 (2열 그리드)
# ==========================================
row1_col1, row1_col2 = st.columns(2)
row2_col1, row2_col2 = st.columns(2)

with row1_col1:
    st.altair_chart(chart1, use_container_width=True)

with row1_col2:
    st.altair_chart(chart2, use_container_width=True)

with row2_col1:
    st.altair_chart(chart3, use_container_width=True)

with row2_col2:
    st.altair_chart(chart4, use_container_width=True)

# ==========================================
# 7. 상세 데이터 (Expander)
# ==========================================
with st.expander("📄 지사별 상세 데이터 테이블 보기"):
    # 가독성을 위해 데이터프레임 스타일링 (Gradient)
    st.dataframe(
        branch_stats.style.background_gradient(subset=["진행률"], cmap="Blues"),
        use_container_width=True,
        hide_index=True
    )