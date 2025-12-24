import streamlit as st
import pandas as pd
import altair as alt
from storage import load_targets, load_results

# ==========================================
# 1. 페이지 설정 및 스타일링
# ==========================================
st.set_page_config(page_title="종합 현황 대시보드", layout="wide", page_icon="💧")

st.markdown("""
<style>
    [data-testid="stMetricValue"] {
        font-size: 2.2rem;
        font-weight: 800;
        color: #2563eb;
    }
    [data-testid="stMetricLabel"] {
        font-size: 1rem;
        color: #64748b;
    }
    .stContainer {
        background-color: #ffffff;
        border-radius: 15px;
        padding: 15px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
    }
    h1, h2, h3 {
        font-family: 'Pretendard', sans-serif;
    }
</style>
""", unsafe_allow_html=True)

st.title("💧 종합 현황 대시보드")
st.markdown("실시간 **조치 진척률** 및 **해지 사유** 시각화 리포트")

# ==========================================
# 2. 데이터 로드 및 전처리
# ==========================================
targets = load_targets()
results = load_results()

BRANCH_ORDER = ["중앙", "강북", "서대문", "고양", "의정부", "남양주", "강릉", "원주"]

def preprocess_data(targets, results):
    if not targets.empty:
        if "관리지사" in targets.columns:
            targets["관리지사표시"] = targets["관리지사"].str.replace("지사", "").str.strip()
        else:
            targets["관리지사표시"] = "미지정"
        targets["계약번호"] = targets["계약번호"].astype(str)
    
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
# 3. 사이드바 필터
# ==========================================
st.sidebar.header("🔍 필터 설정")

available_branches = [b for b in BRANCH_ORDER if b in targets["관리지사표시"].unique()]
other_branches = [b for b in targets["관리지사표시"].unique() if b not in BRANCH_ORDER]
final_branch_order = available_branches + other_branches

selected_branches = st.sidebar.multiselect(
    "지사 선택",
    final_branch_order,
    default=final_branch_order
)

available_owners = sorted(targets["담당자"].dropna().unique().tolist()) if "담당자" in targets.columns else []
selected_owners = st.sidebar.multiselect(
    "담당자 선택",
    available_owners,
    default=[]
)

filtered_targets = targets[targets["관리지사표시"].isin(selected_branches)]
if selected_owners:
    filtered_targets = filtered_targets[filtered_targets["담당자"].isin(selected_owners)]

target_ids = filtered_targets["계약번호"].unique()
filtered_results = results[results["계약번호"].isin(target_ids)] if not results.empty else pd.DataFrame()

# ==========================================
# 4. KPI Scorecard
# ==========================================
st.markdown("### 🚀 핵심 성과 지표 (KPI)")
col1, col2, col3, col4 = st.columns(4)

total_tgt = len(filtered_targets)
total_res = len(filtered_results)
progress_rate = (total_res / total_tgt * 100) if total_tgt > 0 else 0
remain_cnt = total_tgt - total_res

with col1:
    st.metric("총 대상", f"{total_tgt:,.0f}건")
with col2:
    st.metric("조치 완료", f"{total_res:,.0f}건", delta=f"{progress_rate:.1f}%")
with col3:
    st.metric("잔여 대상", f"{remain_cnt:,.0f}건", delta_color="inverse")
with col4:
    if not filtered_results.empty and "해지사유" in filtered_results.columns:
        top_reason = filtered_results["해지사유"].mode()[0]
    else:
        top_reason = "-"
    st.metric("최다 해지사유", top_reason)

st.markdown("---")

# ==========================================
# 5. 시각화 (안전한 타입 변환 및 둥근 디자인)
# ==========================================

# ------------------------------------------
# [데이터 집계 & 타입 강제 변환] SchemaError 방지 핵심
# ------------------------------------------
branch_stats = filtered_targets.groupby("관리지사표시").size().reset_index(name="대상건수")

if not filtered_results.empty:
    done_stats = filtered_results.groupby("관리지사표시").size().reset_index(name="완료건수")
    branch_stats = pd.merge(branch_stats, done_stats, on="관리지사표시", how="left")
else:
    branch_stats["완료건수"] = 0

branch_stats = branch_stats.fillna(0)
# [중요] Python 기본 int/float로 변환 (Numpy int64 오류 방지)
branch_stats["대상건수"] = branch_stats["대상건수"].apply(lambda x: int(x))
branch_stats["완료건수"] = branch_stats["완료건수"].apply(lambda x: int(x))
branch_stats["진행률"] = (branch_stats["완료건수"] / branch_stats["대상건수"] * 100).round(1).apply(lambda x: float(x))

# ------------------------------------------
# [Chart 1] 지사별 진척도 (Rounded Bar - 호환성 개선)
# ------------------------------------------
# cornerRadius 대신 cornerRadiusTopLeft/Right 사용으로 호환성 확보
bar_props = {"cornerRadiusTopLeft": 10, "cornerRadiusTopRight": 10, "size": 30}

base = alt.Chart(branch_stats).encode(
    x=alt.X("관리지사표시:N", sort=BRANCH_ORDER, title=None, axis=alt.Axis(labelAngle=0))
)

# 배경 막대
bar_bg = base.mark_bar(color="#f1f5f9", **bar_props).encode(
    y=alt.Y("대상건수:Q", title="건수"),
    tooltip=[alt.Tooltip("관리지사표시:N", title="지사"), alt.Tooltip("대상건수:Q", title="대상")]
)

# 진행 막대
bar_fg = base.mark_bar(color="#3b82f6", **bar_props).encode(
    y=alt.Y("완료건수:Q"),
    tooltip=[
        alt.Tooltip("관리지사표시:N", title="지사"),
        alt.Tooltip("완료건수:Q", title="완료"),
        alt.Tooltip("진행률:Q", title="진행률(%)")
    ]
)

# 텍스트
text = base.mark_text(dy=-10, color="#1e293b", fontWeight="bold").encode(
    y="대상건수:Q",
    text=alt.Text("진행률:Q", format=".1f")
)

chart1 = (bar_bg + bar_fg + text).properties(
    title="🏢 지사별 진행 현황",
    height=320
)

# ------------------------------------------
# [Chart 2] 해지 사유 (Bubble Chart)
# ------------------------------------------
if not filtered_results.empty and "해지사유" in filtered_results.columns:
    reason_counts = filtered_results["해지사유"].value_counts().reset_index()
    reason_counts.columns = ["해지사유", "건수"]
    # 타입 안전 변환
    reason_counts["건수"] = reason_counts["건수"].apply(lambda x: int(x))
    
    base_bubble = alt.Chart(reason_counts).encode(
        x=alt.X("해지사유:N", title=None, axis=alt.Axis(labels=True, ticks=False, domain=False)),
        y=alt.Y("건수:Q", title=None, axis=None),
        tooltip=[alt.Tooltip("해지사유:N"), alt.Tooltip("건수:Q")]
    )
    
    bubbles = base_bubble.mark_circle().encode(
        size=alt.Size("건수:Q", scale=alt.Scale(range=[300, 2000]), legend=None),
        color=alt.Color("해지사유:N", legend=None, scale=alt.Scale(scheme="blues"))
    )
    
    text_bubble = base_bubble.mark_text(color="white", fontWeight="bold").encode(
        text="건수:Q"
    )
    
    # Layering 후 properties 적용
    chart2 = (bubbles + text_bubble).properties(
        title="💧 해지 사유 분포",
        height=320
    ).configure_view(strokeWidth=0)

else:
    chart2 = alt.Chart(pd.DataFrame({"text": ["데이터 없음"]})).mark_text().encode(text="text").properties(title="데이터 없음", height=320)

# ------------------------------------------
# [Chart 3] 담당자별 실적
# ------------------------------------------
if not filtered_results.empty and "담당자" in filtered_results.columns:
    owner_counts = filtered_results["담당자"].value_counts().reset_index()
    owner_counts.columns = ["담당자", "처리건수"]
    owner_counts["처리건수"] = owner_counts["처리건수"].apply(lambda x: int(x))
    owner_counts = owner_counts.head(10)
    
    chart3 = alt.Chart(owner_counts).mark_bar(cornerRadiusEnd=5, height=15, color="#10b981").encode(
        x=alt.X("처리건수:Q", title="건수"),
        y=alt.Y("담당자:N", sort="-x", title=None),
        tooltip=[alt.Tooltip("담당자:N"), alt.Tooltip("처리건수:Q")]
    ).properties(
        title="🏆 담당자별 실적 (Top 10)",
        height=320
    )
else:
    chart3 = alt.Chart(pd.DataFrame()).mark_text().properties(height=320)

# ------------------------------------------
# [Chart 4] 일자별 추이
# ------------------------------------------
if not filtered_results.empty and "처리일시" in filtered_results.columns:
    filtered_results["처리날짜"] = pd.to_datetime(filtered_results["처리일시"], errors='coerce').dt.date
    daily_counts = filtered_results.groupby("처리날짜").size().reset_index(name="건수")
    daily_counts["건수"] = daily_counts["건수"].apply(lambda x: int(x))

    chart4 = alt.Chart(daily_counts).mark_area(
        interpolate='monotone', 
        fillOpacity=0.6,
        line={'color':'#6366f1'}
    ).encode(
        x=alt.X("처리날짜:T", title=None),
        y=alt.Y("건수:Q", title="등록 건수"),
        color=alt.value("#818cf8"),
        tooltip=[alt.Tooltip("처리날짜:T", title="날짜"), alt.Tooltip("건수:Q", title="건수")]
    ).properties(
        title="📅 일별 처리 흐름",
        height=320
    )
else:
    chart4 = alt.Chart(pd.DataFrame()).mark_text().properties(height=320)


# ==========================================
# 6. 레이아웃 배치
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

with st.expander("📄 상세 데이터 테이블 열기"):
    st.dataframe(
        branch_stats.style.background_gradient(subset=["진행률"], cmap="Blues"),
        use_container_width=True,
        hide_index=True
    )
