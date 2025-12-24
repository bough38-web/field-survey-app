import streamlit as st
import pandas as pd
import altair as alt
from storage import load_targets, load_results

# ==========================================
# 1. 페이지 설정 및 스타일링 (High-End CSS)
# ==========================================

st.title("💧 종합 현황 대시보드")

st.markdown("""
<style>
    /* 전체 배경 및 폰트 */
    .stApp {
        background-color: #f8fafc;
    }
    h1, h2, h3 {
        font-family: 'Pretendard', sans-serif;
        color: #1e293b;
    }
    
    /* KPI 카드 스타일 */
    [data-testid="stMetricValue"] {
        font-size: 2.2rem;
        font-weight: 800;
        color: #2563eb;
    }
    [data-testid="stMetricLabel"] {
        font-size: 1rem;
        color: #64748b;
        font-weight: 600;
    }
    
    /* 컨테이너(카드) 스타일 */
    .stContainer {
        background-color: #ffffff;
        border-radius: 12px;
        padding: 20px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);
        border: 1px solid #e2e8f0;
    }
    
    /* 사이드바 스타일 개선 */
    [data-testid="stSidebar"] {
        background-color: #f1f5f9;
        border-right: 1px solid #e2e8f0;
    }

    /* 🌟 [Advanced Table Styling] 테이블 디자인 */
    .styled-table {
        width: 100%;
        border-collapse: collapse;
        margin: 25px 0;
        font-size: 0.95em;
        font-family: 'Pretendard', sans-serif;
        box-shadow: 0 0 20px rgba(0, 0, 0, 0.05);
        border-radius: 10px;
        overflow: hidden; 
    }
    .styled-table thead tr {
        background-color: #2563eb; 
        color: #ffffff;
        text-align: center;
    }
    .styled-table th {
        padding: 15px;
        font-weight: 600;
        letter-spacing: 0.5px;
        text-align: center !important;
        white-space: nowrap;
    }
    .styled-table td {
        padding: 12px 15px;
        border-bottom: 1px solid #dddddd;
        text-align: center !important;
        vertical-align: middle;
        color: #334155;
        white-space: normal;
        word-wrap: break-word;
    }
    .styled-table tbody tr {
        background-color: #ffffff;
        transition: all 0.2s ease-in-out;
    }
    .styled-table tbody tr:nth-of-type(even) {
        background-color: #f8fafc;
    }
    .styled-table tbody tr:hover {
        background-color: #eff6ff;
        transform: scale(1.002);
        font-weight: 600;
        color: #2563eb;
    }
    /* 커스텀 진행바 */
    .progress-bg {
        background-color: #e2e8f0;
        border-radius: 10px;
        width: 100px;
        height: 8px;
        margin: 0 auto;
        overflow: hidden;
    }
    .progress-fill {
        height: 100%;
        border-radius: 10px;
        background: linear-gradient(90deg, #60a5fa 0%, #2563eb 100%);
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
        targets["계약번호"] = targets["계약번호"].astype(str).str.replace(r'\.0$', '', regex=True)
    
    if not results.empty:
        if "관리지사" in results.columns:
            results["관리지사표시"] = results["관리지사"].str.replace("지사", "").str.strip()
        else:
            results["관리지사표시"] = "미지정"
        results["계약번호"] = results["계약번호"].astype(str).str.replace(r'\.0$', '', regex=True)

    return targets, results

targets, results = preprocess_data(targets, results)

if targets.empty:
    st.warning("⚠️ 분석할 데이터가 없습니다. 먼저 '조사 대상 업로드'를 진행해주세요.")
    st.stop()

# ==========================================
# 3. 사이드바 필터
# ==========================================
with st.sidebar:
    st.header("🔍 필터 설정")
    st.markdown("보고 싶은 데이터를 선택하세요.")
    
    with st.expander("🏢 지사 선택", expanded=True):
        available_branches = [b for b in BRANCH_ORDER if b in targets["관리지사표시"].unique()]
        other_branches = [b for b in targets["관리지사표시"].unique() if b not in BRANCH_ORDER]
        final_branch_order = available_branches + other_branches
        
        selected_branches = st.multiselect(
            "지사를 선택해주세요",
            options=final_branch_order,
            default=[], 
            placeholder="지사 선택 (비워두면 전체)"
        )

    with st.expander("👤 담당자 선택", expanded=True):
        if selected_branches:
            filtered_by_branch = targets[targets["관리지사표시"].isin(selected_branches)]
        else:
            filtered_by_branch = targets
        
        if "담당자" in filtered_by_branch.columns:
            available_owners = sorted(filtered_by_branch["담당자"].dropna().unique().tolist())
        else:
            available_owners = []
            
        selected_owners = st.multiselect(
            "담당자를 선택해주세요",
            options=available_owners,
            default=[],
            placeholder="담당자 선택 (비워두면 전체)"
        )

    st.markdown("---")
    
    if st.button("🔄 필터 초기화", use_container_width=True):
        st.rerun()

# 필터 적용
if selected_branches:
    filtered_targets = targets[targets["관리지사표시"].isin(selected_branches)]
else:
    filtered_targets = targets

if selected_owners:
    filtered_targets = filtered_targets[filtered_targets["담당자"].isin(selected_owners)]

target_ids = filtered_targets["계약번호"].unique()
filtered_results = results[results["계약번호"].isin(target_ids)] if not results.empty else pd.DataFrame()

st.sidebar.info(f"📊 표시 대상: **{len(filtered_targets):,}건**")

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
# 5. 시각화 (Altair)
# ==========================================
branch_stats = filtered_targets.groupby("관리지사표시").size().reset_index(name="대상건수")

if not filtered_results.empty:
    done_stats = filtered_results.groupby("관리지사표시").size().reset_index(name="완료건수")
    branch_stats = pd.merge(branch_stats, done_stats, on="관리지사표시", how="left")
else:
    branch_stats["완료건수"] = 0

branch_stats = branch_stats.fillna(0)
branch_stats["대상건수"] = branch_stats["대상건수"].astype(int)
branch_stats["완료건수"] = branch_stats["완료건수"].astype(int)
branch_stats["진행률"] = (branch_stats["완료건수"] / branch_stats["대상건수"] * 100).fillna(0)

bar_props = {"cornerRadiusTopLeft": 10, "cornerRadiusTopRight": 10, "size": 30}
base = alt.Chart(branch_stats).encode(
    x=alt.X("관리지사표시:N", sort=BRANCH_ORDER, title=None, axis=alt.Axis(labelAngle=0))
)
bar_bg = base.mark_bar(color="#f1f5f9", **bar_props).encode(
    y=alt.Y("대상건수:Q", title="건수"),
    tooltip=[alt.Tooltip("관리지사표시:N", title="지사"), alt.Tooltip("대상건수:Q", title="대상")]
)
bar_fg = base.mark_bar(color="#3b82f6", **bar_props).encode(
    y=alt.Y("완료건수:Q"),
    tooltip=[alt.Tooltip("관리지사표시:N", title="지사"), alt.Tooltip("완료건수:Q", title="완료")]
)
text = base.mark_text(dy=-10, color="#1e293b", fontWeight="bold").encode(
    y="대상건수:Q",
    text=alt.Text("진행률:Q", format=".1f")
)
chart1 = (bar_bg + bar_fg + text).properties(title="🏢 지사별 진행 현황", height=320)

if not filtered_results.empty and "해지사유" in filtered_results.columns:
    reason_counts = filtered_results["해지사유"].value_counts().reset_index()
    reason_counts.columns = ["해지사유", "건수"]
    reason_counts["건수"] = reason_counts["건수"].astype(int)
    
    base_bubble = alt.Chart(reason_counts).encode(
        x=alt.X("해지사유:N", title=None, axis=alt.Axis(labels=True, ticks=False, domain=False)),
        y=alt.Y("건수:Q", title=None, axis=None),
        tooltip=[alt.Tooltip("해지사유:N"), alt.Tooltip("건수:Q")]
    )
    bubbles = base_bubble.mark_circle().encode(
        size=alt.Size("건수:Q", scale=alt.Scale(range=[300, 2000]), legend=None),
        color=alt.Color("해지사유:N", legend=None, scale=alt.Scale(scheme="blues"))
    )
    text_bubble = base_bubble.mark_text(color="white", fontWeight="bold").encode(text="건수:Q")
    chart2 = (bubbles + text_bubble).properties(title="💧 해지 사유 분포", height=320).configure_view(strokeWidth=0)
else:
    chart2 = alt.Chart(pd.DataFrame({"text": ["데이터 없음"]})).mark_text().encode(text="text").properties(title="데이터 없음", height=320)

if not filtered_results.empty and "담당자" in filtered_results.columns:
    owner_counts = filtered_results["담당자"].value_counts().reset_index()
    owner_counts.columns = ["담당자", "처리건수"]
    owner_counts["처리건수"] = owner_counts["처리건수"].astype(int)
    owner_counts = owner_counts.head(10)
    chart3 = alt.Chart(owner_counts).mark_bar(cornerRadiusEnd=5, height=15, color="#10b981").encode(
        x=alt.X("처리건수:Q", title="건수"),
        y=alt.Y("담당자:N", sort="-x", title=None),
        tooltip=[alt.Tooltip("담당자:N"), alt.Tooltip("처리건수:Q")]
    ).properties(title="🏆 담당자별 실적 (Top 10)", height=320)
else:
    chart3 = alt.Chart(pd.DataFrame()).mark_text().properties(height=320)

if not filtered_results.empty and "처리일시" in filtered_results.columns:
    filtered_results["처리날짜"] = pd.to_datetime(filtered_results["처리일시"], errors='coerce').dt.date
    daily_counts = filtered_results.groupby("처리날짜").size().reset_index(name="건수")
    daily_counts["건수"] = daily_counts["건수"].astype(int)
    chart4 = alt.Chart(daily_counts).mark_area(interpolate='monotone', fillOpacity=0.6, line={'color':'#6366f1'}).encode(
        x=alt.X("처리날짜:T", title=None),
        y=alt.Y("건수:Q", title="등록 건수"),
        color=alt.value("#818cf8"),
        tooltip=[alt.Tooltip("처리날짜:T", title="날짜"), alt.Tooltip("건수:Q", title="건수")]
    ).properties(title="📅 일별 처리 흐름", height=320)
else:
    chart4 = alt.Chart(pd.DataFrame()).mark_text().properties(height=320)

row1_col1, row1_col2 = st.columns(2)
row2_col1, row2_col2 = st.columns(2)

with row1_col1: st.altair_chart(chart1, use_container_width=True)
with row1_col2: st.altair_chart(chart2, use_container_width=True)
with row2_col1: st.altair_chart(chart3, use_container_width=True)
with row2_col2: st.altair_chart(chart4, use_container_width=True)

# ==========================================
# 6. 상세 데이터 테이블 (HTML 공백 제거)
# ==========================================
def render_custom_table(df):
    """Pandas DataFrame을 예쁜 HTML 테이블로 변환 (공백 제거)"""
    html = '<table class="styled-table">'
    html += '<thead><tr><th>지사명</th><th>대상 건수</th><th>완료 건수</th><th>진행률</th><th>상태(Progress)</th></tr></thead>'
    html += '<tbody>'
    
    try:
        df['sort_key'] = df['관리지사표시'].apply(lambda x: BRANCH_ORDER.index(x) if x in BRANCH_ORDER else 99)
        df = df.sort_values('sort_key').drop(columns=['sort_key'])
    except:
        pass

    for _, row in df.iterrows():
        rate = row['진행률']
        # f-string 앞에 공백을 없애서 마크다운이 코드로 인식하지 않게 함
        html += f"""<tr>
<td><strong>{row['관리지사표시']}</strong></td>
<td>{row['대상건수']:,}건</td>
<td>{row['완료건수']:,}건</td>
<td style="color:#2563eb; font-weight:bold;">{rate:.1f}%</td>
<td>
<div class="progress-bg">
<div class="progress-fill" style="width: {rate}%;"></div>
</div>
</td>
</tr>"""
    
    html += '</tbody></table>'
    return html

st.markdown("### 📄 지사별 상세 데이터 (Detailed View)")
if not branch_stats.empty:
    st.markdown(render_custom_table(branch_stats), unsafe_allow_html=True)
else:
    st.info("표시할 데이터가 없습니다.")
