import streamlit as st
import pandas as pd
from datetime import date
from storage import load_targets, load_results

# =========================
# 기본 설정
# =========================
st.set_page_config(page_title="등록결과 모니터링", layout="wide")
st.title("📊 등록결과 모니터링 (업로드 대비 등록 현황)")

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

targets["관리지사표시"] = (
    targets["관리지사"].astype(str)
    .str.replace("지사", "", regex=False)
    .str.strip()
)

results["관리지사표시"] = (
    results["관리지사"].astype(str)
    .str.replace("지사", "", regex=False)
    .str.strip()
)

targets["계약번호"] = targets["계약번호"].astype(str)
results["계약번호"] = results["계약번호"].astype(str)

# =========================
# 등록 기준: 해지사유 입력된 건만
# =========================
if "해지사유" in results.columns:
    registered_results = results[results["해지사유"].notna()]
else:
    registered_results = results.iloc[0:0]

processed_contracts = registered_results["계약번호"].unique()

# =========================
# 사이드바 필터
# =========================
st.sidebar.header("🔎 필터")

available_branches = [
    b for b in BRANCH_ORDER
    if b in targets["관리지사표시"].unique()
]

selected_branch = st.sidebar.radio(
    "관리지사",
    ["전체"] + available_branches
)

if selected_branch != "전체":
    targets_f = targets[targets["관리지사표시"] == selected_branch]
    results_f = registered_results[registered_results["관리지사표시"] == selected_branch]
else:
    targets_f = targets.copy()
    results_f = registered_results.copy()

# =========================
# KPI 계산
# =========================
total_targets = targets_f["계약번호"].nunique()
processed_count = results_f["계약번호"].nunique()
unprocessed_count = total_targets - processed_count
progress_rate = round((processed_count / total_targets) * 100, 1) if total_targets else 0

def rate_icon(rate):
    if rate >= 70:
        return "🔴"
    elif rate >= 40:
        return "🟡"
    return "🟢"

rate_status = rate_icon(progress_rate)

# 오늘 등록 건수 (완전 방어)
today = date.today().strftime("%Y-%m-%d")
if "해지_해지일자" in registered_results.columns:
    today_count = registered_results[
        registered_results["해지_해지일자"] == today
    ].shape[0]
else:
    today_count = 0

# =========================
# KPI 카드
# =========================
st.markdown("## 📌 진행 현황 요약")

c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("업로드 대상", total_targets)
c2.metric("등록 건수", processed_count)
c3.metric("미등록 건수", unprocessed_count)
c4.metric("등록율", f"{progress_rate}% {rate_status}")
c5.metric("오늘 등록", today_count)

st.divider()

# =========================
# 지사별 요약 (전체 선택 시)
# =========================
if selected_branch == "전체":
    st.markdown("## 🏢 관리지사별 처리 현황")

    branch_target = (
        targets.groupby("관리지사표시")["계약번호"]
        .nunique()
        .reindex(BRANCH_ORDER)
    )

    branch_done = (
        registered_results.groupby("관리지사표시")["계약번호"]
        .nunique()
        .reindex(BRANCH_ORDER)
    )

    summary = pd.DataFrame({
        "대상건수": branch_target,
        "등록건수": branch_done
    }).fillna(0)

    summary["미등록건수"] = summary["대상건수"] - summary["등록건수"]
    summary["미등록율(%)"] = (
        summary["미등록건수"] / summary["대상건수"] * 100
    ).round(1)

    summary["상태"] = summary["미등록율(%)"].apply(rate_icon)

    # 📊 대상 vs 등록
    st.subheader("📊 지사별 대상건수 vs 등록건수")
    st.bar_chart(summary[["대상건수", "등록건수"]])

    # 📉 미등록율
    st.subheader("📉 지사별 미등록율 (%)")
    st.bar_chart(summary[["미등록율(%)"]])

    st.subheader("📋 지사별 상세 현황")
    st.dataframe(summary.reset_index(), use_container_width=True)

st.divider()

# =========================
# Drill-down: 미등록 대상
# =========================
st.markdown("## 🔍 미등록 대상 상세")

unprocessed = targets_f[
    ~targets_f["계약번호"].isin(processed_contracts)
]

st.dataframe(unprocessed, use_container_width=True)

# =========================
# 관리자 영역
# =========================
st.divider()
st.markdown("## 🔐 관리자 전용")

pw = st.text_input("관리자 비밀번호 입력", type="password")

if pw != "3867":
    st.info("관리자 인증 시 다운로드 기능이 활성화됩니다.")
    st.stop()

st.success("관리자 인증 완료")

# 등록 완료 대상
st.markdown("### 🟢 등록 완료 대상 목록")
registered_list = targets_f[
    targets_f["계약번호"].isin(processed_contracts)
]
st.dataframe(registered_list, use_container_width=True)

# 다운로드
csv = unprocessed.to_csv(index=False).encode("utf-8-sig")
st.download_button(
    label="📥 미등록 대상 다운로드",
    data=csv,
    file_name="미등록_대상_목록.csv",
    mime="text/csv"
)
