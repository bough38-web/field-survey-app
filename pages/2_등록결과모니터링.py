import streamlit as st
import pandas as pd
from datetime import date
from storage import load_targets, load_results

# =========================
# 기본 설정
# =========================
st.set_page_config(page_title="등록결과 모니터링", layout="wide")
st.title("📊 등록결과 모니터링")

BRANCH_ORDER = ["중앙", "강북", "서대문", "고양", "의정부", "강릉", "원주"]

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
# 등록 기준: 해지사유가 있는 건만
# =========================
if "해지사유" in results.columns:
    registered_results = results[results["해지사유"].notna()]
else:
    registered_results = results.iloc[0:0]

# =========================
# 사이드바 필터 (관리지사 + 담당자)
# =========================
st.sidebar.header("🔎 필터")

available_branches = [
    b for b in BRANCH_ORDER
    if b in targets["관리지사표시"].unique()
]

selected_branch = st.sidebar.radio("관리지사", ["전체"] + available_branches)

if selected_branch == "전체":
    targets_f = targets.copy()
    results_f = registered_results.copy()
else:
    targets_f = targets[targets["관리지사표시"] == selected_branch]
    results_f = registered_results[registered_results["관리지사표시"] == selected_branch]

owners = sorted(targets_f["담당자"].dropna().unique().tolist())
selected_owner = st.sidebar.radio("담당자", ["전체"] + owners)

if selected_owner != "전체":
    targets_f = targets_f[targets_f["담당자"] == selected_owner]
    results_f = results_f[results_f["담당자"] == selected_owner]

# =========================
# KPI 계산
# =========================
total_targets = targets_f["계약번호"].nunique()
registered_count = results_f["계약번호"].nunique()
unregistered_count = total_targets - registered_count
register_rate = round((registered_count / total_targets) * 100, 1) if total_targets else 0

today = date.today().strftime("%Y-%m-%d")
today_count = (
    results_f["해지_해지일자"].eq(today).sum()
    if "해지_해지일자" in results_f.columns else 0
)

# =========================
# KPI 카드
# =========================
st.markdown("## 📌 진행 현황 요약")

c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("대상 건수", total_targets)
c2.metric("등록 건수", registered_count)
c3.metric("미등록 건수", unregistered_count)
c4.metric("등록율", f"{register_rate}%")
c5.metric("오늘 등록", today_count)

st.divider()

# =========================
# 지사별 대상 vs 등록 (정렬 고정)
# =========================
st.markdown("## 🏢 지사별 대상건수 vs 등록건수")

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

branch_summary = pd.DataFrame({
    "대상건수": branch_target,
    "등록건수": branch_done
}).fillna(0)

branch_summary["등록율(%)"] = (
    branch_summary["등록건수"] / branch_summary["대상건수"] * 100
).round(1)

st.bar_chart(branch_summary[["대상건수", "등록건수"]])
st.dataframe(branch_summary.reset_index(), use_container_width=True)

st.divider()

# =========================
# 담당자별 미등록 건수 (내림차순)
# =========================
st.markdown("## 👤 담당자별 미등록 건수")

unregistered_by_owner = (
    targets_f[~targets_f["계약번호"].isin(results_f["계약번호"])]
    .groupby("담당자")["계약번호"]
    .count()
    .sort_values(ascending=False)
)

if not unregistered_by_owner.empty:
    st.bar_chart(unregistered_by_owner)
else:
    st.info("미등록 대상이 없습니다.")

st.divider()

# =========================
# 미등록 대상 상세
# =========================
st.markdown("## 🔴 미등록 대상 상세")

unregistered = (
    targets_f[~targets_f["계약번호"].isin(results_f["계약번호"])]
    .fillna("")
    .drop(columns=["관리지사표시"], errors="ignore")
)

st.dataframe(unregistered, use_container_width=True)

st.divider()

# =========================
# 🔐 관리자 영역
# =========================
st.markdown("## 🔐 관리자 전용")

pw = st.text_input("관리자 비밀번호 입력", type="password")

if pw != "3867":
    st.info("관리자 인증 시 등록 완료 데이터 수정이 가능합니다.")
    st.stop()

st.success("관리자 인증 완료")

# =========================
# 등록 완료 대상 (관리자 수정 가능)
# =========================
st.markdown("### 🟢 등록 완료 대상 목록 (수정 가능)")

editable = (
    results_f
    .fillna("")
    .drop(columns=["관리지사표시"], errors="ignore")
)

edited = st.data_editor(
    editable,
    use_container_width=True,
    num_rows="dynamic"
)

if st.button("💾 수정 저장"):
    edited.to_csv("storage/survey_results.csv", index=False)
    st.success("수정 내용이 저장되었습니다.")
