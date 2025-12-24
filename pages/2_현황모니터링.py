import streamlit as st
import pandas as pd
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
# 전처리 (nan 제거 + 지사명 정규화)
# =========================
targets = targets.dropna(subset=["관리지사", "계약번호"])
results = results.dropna(subset=["관리지사", "계약번호"])

targets["관리지사표시"] = targets["관리지사"].astype(str).str.replace("지사", "", regex=False).str.strip()
results["관리지사표시"] = results["관리지사"].astype(str).str.replace("지사", "", regex=False).str.strip()

targets["계약번호"] = targets["계약번호"].astype(str)
results["계약번호"] = results["계약번호"].astype(str)

# =========================
# 🔹 사이드바 필터 (버튼식)
# =========================
st.sidebar.header("🔎 필터")

# 관리지사 버튼 (고정 순서)
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
    results_f = results[results["관리지사표시"] == selected_branch]
else:
    targets_f = targets.copy()
    results_f = results.copy()

# 담당자 버튼 (지사 선택에 따라 동적)
if "담당자" in targets_f.columns:
    owners = sorted(
        targets_f["담당자"]
        .dropna()
        .unique()
        .tolist()
    )

    selected_owner = st.sidebar.radio(
        "담당자",
        ["전체"] + owners
    )

    if selected_owner != "전체":
        targets_f = targets_f[targets_f["담당자"] == selected_owner]
        results_f = results_f[results_f["담당자"] == selected_owner]
else:
    selected_owner = "전체"

# =========================
# KPI 계산
# =========================
total_targets = len(targets_f)
processed_contracts = results_f["계약번호"].unique()
processed_count = len(processed_contracts)
unprocessed_count = total_targets - processed_count
progress_rate = round((processed_count / total_targets) * 100, 1) if total_targets else 0

# =========================
# 🔹 KPI 카드
# =========================
st.markdown("## 📌 진행 현황 요약")

c1, c2, c3, c4 = st.columns(4)
c1.metric("업로드 대상", total_targets)
c2.metric("등록 건수", processed_count)
c3.metric("미등록 건수", unprocessed_count)
c4.metric("등록율", f"{progress_rate}%")

st.divider()

# =========================
# 관리지사별 등록율 (선택 안 했을 때만)
# =========================
if selected_branch == "전체":
    st.markdown("## 🏢 관리지사별 등록율")

    branch_target = (
        targets.groupby("관리지사표시")["계약번호"]
        .nunique()
        .reindex(available_branches)
    )

    branch_result = (
        results.groupby("관리지사표시")["계약번호"]
        .nunique()
        .reindex(available_branches)
    )

    branch_status = pd.concat(
        [branch_target, branch_result],
        axis=1
    ).fillna(0)

    branch_status.columns = ["업로드건수", "등록건수"]
    branch_status["미등록건수"] = branch_status["업로드건수"] - branch_status["등록건수"]
    branch_status["등록율(%)"] = (
        branch_status["등록건수"] / branch_status["업로드건수"] * 100
    ).round(1)

    st.bar_chart(branch_status["등록율(%)"])
    st.dataframe(branch_status.reset_index(), use_container_width=True)

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

# 미등록 대상
st.markdown("### 🚨 미등록 대상 목록")

unprocessed = targets_f[
    ~targets_f["계약번호"].isin(processed_contracts)
]

st.dataframe(unprocessed, use_container_width=True)

# 다운로드
csv = unprocessed.to_csv(index=False).encode("utf-8-sig")
st.download_button(
    label="📥 미등록 대상 다운로드",
    data=csv,
    file_name="unprocessed_targets.csv",
    mime="text/csv"
)
