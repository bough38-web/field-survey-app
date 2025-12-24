import streamlit as st
import pandas as pd
from datetime import date
from storage import load_targets, load_results

st.set_page_config(page_title="현황 모니터링", layout="wide")
st.title("📊 현황 모니터링 (업로드 대비 등록 현황)")

BRANCH_ORDER = ["중앙", "강북", "서대문", "고양", "의정부", "남양주", "강릉", "원주"]

# =========================
# 데이터 로드
# =========================
targets = load_targets()
results = load_results()

if targets.empty:
    st.info("업로드된 조사 대상이 없습니다.")
    st.stop()

# =========================
# 전처리
# =========================
targets = targets.dropna(subset=["관리지사", "계약번호"])
results = results.dropna(subset=["관리지사", "계약번호"])

targets["관리지사표시"] = targets["관리지사"].astype(str).str.replace("지사", "", regex=False).str.strip()
results["관리지사표시"] = results["관리지사"].astype(str).str.replace("지사", "", regex=False).str.strip()

targets["계약번호"] = targets["계약번호"].astype(str)
results["계약번호"] = results["계약번호"].astype(str)

# 🔥 등록 완료 기준: 해지사유가 있는 건만
registered_results = results.dropna(subset=["해지사유"])

# =========================
# 🔹 사이드바 필터
# =========================
st.sidebar.header("🔎 필터")

available_branches = [
    b for b in BRANCH_ORDER
    if b in targets["관리지사표시"].unique()
]

selected_branch = st.sidebar.radio("관리지사", ["전체"] + available_branches)

targets_f = targets if selected_branch == "전체" else targets[targets["관리지사표시"] == selected_branch]
results_f = registered_results if selected_branch == "전체" else registered_results[registered_results["관리지사표시"] == selected_branch]

if "담당자" in targets_f.columns:
    owners = sorted(targets_f["담당자"].dropna().unique().tolist())
else:
    owners = []

selected_owner = st.sidebar.radio("담당자", ["전체"] + owners)

if selected_owner != "전체":
    targets_f = targets_f[targets_f["담당자"] == selected_owner]
    results_f = results_f[results_f["담당자"] == selected_owner]

# =========================
# KPI 계산 (등록 기준 반영)
# =========================
total_targets = len(targets_f)

registered_contracts = results_f["계약번호"].unique()
registered_count = len(registered_contracts)

unregistered_count = max(total_targets - registered_count, 0)
progress_rate = round((registered_count / total_targets) * 100, 1) if total_targets else 0

# 상태 아이콘
def rate_icon(rate):
    if rate >= 70:
        return "🟢"
    elif rate >= 40:
        return "🟡"
    return "🔴"

rate_status = rate_icon(progress_rate)

# 오늘 등록 건수 (해지사유 기준)
today = date.today().strftime("%Y-%m-%d")
today_count = (
    registered_results[
        registered_results.get("해지_해지일자", registered_results.get("해지일자", "")) == today
    ].shape[0]
    if not registered_results.empty else 0
)

# =========================
# KPI 카드
# =========================
st.markdown("## 📌 진행 현황 요약")

c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("업로드 대상", total_targets)
c2.metric("등록 건수", registered_count)
c3.metric("미등록 건수", unregistered_count)
c4.metric("등록율", f"{progress_rate}% {rate_status}")
c5.metric("오늘 등록 건수", today_count)

st.divider()

# =========================
# 지사별 시각화 (정렬 적용)
# =========================
if selected_branch == "전체":
    st.markdown("## 🏢 관리지사별 처리 현황")

    branch_target = (
        targets.groupby("관리지사표시")["계약번호"]
        .nunique()
        .reindex(available_branches)
    )

    branch_done = (
        registered_results.groupby("관리지사표시")["계약번호"]
        .nunique()
        .reindex(available_branches)
    )

    summary = pd.concat([branch_target, branch_done], axis=1).fillna(0)
    summary.columns = ["대상건수", "등록건수"]
    summary["미등록건수"] = summary["대상건수"] - summary["등록건수"]
    summary["미등록율(%)"] = (summary["미등록건수"] / summary["대상건수"] * 100).round(1)
    summary["상태"] = summary["미등록율(%)"].apply(rate_icon)

    # 막대그래프 (건수)
    st.subheader("📊 지사별 대상 / 등록 / 미등록 건수")
    st.bar_chart(summary[["대상건수", "등록건수", "미등록건수"]])

    # 미등록율
    st.subheader("📉 지사별 미등록율(%)")
    st.bar_chart(summary["미등록율(%)"])

    # 상세 테이블
    st.subheader("📋 지사별 상세 현황")
    st.dataframe(summary.reset_index(), use_container_width=True)

st.divider()

# =========================
# 🔐 관리자 영역
# =========================
st.markdown("## 🔐 관리자 전용")

pw = st.text_input("관리자 비밀번호 입력", type="password")

if pw != "3867":
    st.info("관리자는 상세 데이터 및 다운로드 기능이 활성화됩니다.")
    st.stop()

st.success("관리자 인증 완료")

# =========================
# 🟢 등록 완료 대상
# =========================
st.markdown("### 🟢 등록 완료 대상 목록")

registered_list = targets_f[
    targets_f["계약번호"].isin(registered_contracts)
]

st.dataframe(registered_list, use_container_width=True)

# =========================
# 🔴 미등록 대상
# =========================
st.markdown("### 🔴 미등록 대상 목록")

unregistered = targets_f[
    ~targets_f["계약번호"].isin(registered_contracts)
]

st.dataframe(unregistered, use_container_width=True)

# 다운로드 (미등록 대상)
csv = unregistered.to_csv(index=False).encode("utf-8-sig")
st.download_button(
    label="📥 미등록 대상 다운로드",
    data=csv,
    file_name="unregistered_targets.csv",
    mime="text/csv"
)
