import streamlit as st
import pandas as pd
from storage import load_targets, load_results

st.set_page_config(page_title="현황 모니터링", layout="wide")
st.title("📊 현황 모니터링 (업로드 대비 등록 현황)")

# =========================
# 데이터 로드
# =========================
targets = load_targets()
results = load_results()

if targets.empty:
    st.info("업로드된 조사 대상이 없습니다.")
    st.stop()

# nan 제거
targets = targets.dropna(subset=["관리지사", "계약번호"])
results = results.dropna(subset=["관리지사", "계약번호"])

# 계약번호 문자열 통일
targets["계약번호"] = targets["계약번호"].astype(str)
results["계약번호"] = results["계약번호"].astype(str)

# =========================
# 전체 KPI 계산
# =========================
total_targets = len(targets)
processed_contracts = results["계약번호"].unique()
processed_count = len(processed_contracts)

unprocessed_count = total_targets - processed_count
progress_rate = round((processed_count / total_targets) * 100, 1)

# =========================
# 🔹 KPI 카드
# =========================
st.markdown("## 📌 전체 진행 현황")

col1, col2, col3, col4 = st.columns(4)
col1.metric("업로드 대상 건수", total_targets)
col2.metric("등록(처리) 건수", processed_count)
col3.metric("미등록 건수", unprocessed_count)
col4.metric("등록율", f"{progress_rate}%")

st.divider()

# =========================
# 🔹 관리지사별 등록율
# =========================
st.markdown("## 🏢 관리지사별 등록 현황")

branch_target = (
    targets.groupby("관리지사")["계약번호"]
    .nunique()
    .rename("업로드건수")
)

branch_result = (
    results.groupby("관리지사")["계약번호"]
    .nunique()
    .rename("등록건수")
)

branch_status = pd.concat(
    [branch_target, branch_result], axis=1
).fillna(0)

branch_status["미등록건수"] = (
    branch_status["업로드건수"] - branch_status["등록건수"]
)

branch_status["등록율(%)"] = (
    branch_status["등록건수"] / branch_status["업로드건수"] * 100
).round(1)

# =========================
# 시각화
# =========================
st.markdown("### 등록율(%) 비교")
st.bar_chart(branch_status["등록율(%)"])

st.markdown("### 업로드 vs 등록 건수")
st.bar_chart(branch_status[["업로드건수", "등록건수"]])

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
# 상세 테이블
# =========================
st.markdown("### 📋 관리지사별 상세 현황")
st.dataframe(
    branch_status.reset_index(),
    use_container_width=True
)

# =========================
# 미등록 대상 리스트
# =========================
st.markdown("### 🚨 미등록 대상 목록")

unprocessed = targets[
    ~targets["계약번호"].isin(processed_contracts)
]

st.dataframe(
    unprocessed,
    use_container_width=True
)

# =========================
# 다운로드
# =========================
csv = branch_status.reset_index().to_csv(
    index=False
).encode("utf-8-sig")

st.download_button(
    label="📥 관리지사별 등록 현황 다운로드",
    data=csv,
    file_name="branch_registration_status.csv",
    mime="text/csv"
)
