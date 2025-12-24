import streamlit as st
import pandas as pd
from storage import load_results

st.title("📊 현황 모니터링")

df = load_results()

# =========================
# 데이터 없음 처리
# =========================
if df.empty:
    st.info("등록된 데이터가 없습니다.")
    st.stop()

# 🔥 nan 제거 (시각화 안정화)
df = df.dropna(subset=["관리지사", "해지사유", "불만유형"])

# =========================
# 🔓 공통 현황 (모든 사용자)
# =========================
st.subheader("📌 전체 현황 요약")

col1, col2, col3 = st.columns(3)
col1.metric("총 등록 건수", len(df))
col2.metric("관리지사 수", df["관리지사"].nunique())
col3.metric("불만유형 수", df["불만유형"].nunique())

st.divider()

st.subheader("📊 관리지사별 현황")
st.bar_chart(df["관리지사"].value_counts())

st.subheader("📊 해지사유별 현황")
st.bar_chart(df["해지사유"].value_counts())

st.subheader("📊 불만유형별 현황")
st.bar_chart(df["불만유형"].value_counts())

# =========================
# 🔐 관리자 영역
# =========================
st.divider()
st.subheader("🔐 관리자 전용")

pw = st.text_input("관리자 비밀번호 입력", type="password")

if pw != "3867":
    st.info("관리자는 상세 데이터 및 다운로드 기능이 활성화됩니다.")
    st.stop()

st.success("관리자 인증 완료")

# =========================
# 관리자 필터
# =========================
st.subheader("🔎 관리자 필터")

col_f1, col_f2, col_f3 = st.columns(3)

with col_f1:
    f_branch = st.selectbox(
        "관리지사",
        ["전체"] + sorted(df["관리지사"].unique().tolist())
    )

with col_f2:
    f_reason = st.selectbox(
        "해지사유",
        ["전체"] + sorted(df["해지사유"].unique().tolist())
    )

with col_f3:
    f_complaint = st.selectbox(
        "불만유형",
        ["전체"] + sorted(df["불만유형"].unique().tolist())
    )

filtered = df.copy()

if f_branch != "전체":
    filtered = filtered[filtered["관리지사"] == f_branch]

if f_reason != "전체":
    filtered = filtered[filtered["해지사유"] == f_reason]

if f_complaint != "전체":
    filtered = filtered[filtered["불만유형"] == f_complaint]

st.caption(f"조회 결과: {len(filtered)}건")

# =========================
# 상세 데이터
# =========================
st.subheader("📋 상세 데이터")
st.dataframe(filtered)

# =========================
# 다운로드
# =========================
csv = filtered.to_csv(index=False).encode("utf-8-sig")
st.download_button(
    label="📥 엑셀(CSV) 다운로드",
    data=csv,
    file_name="survey_results_filtered.csv",
    mime="text/csv"
)
