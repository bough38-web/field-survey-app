import streamlit as st
import pandas as pd
from storage import load_results

st.title("📊 관리자 현황 모니터링")

# =========================
# 🔐 관리자 인증
# =========================
pw = st.text_input("관리자 비밀번호 입력", type="password")

if pw != "3867":
    st.warning("관리자만 접근 가능합니다.")
    st.stop()

# =========================
# 데이터 로드
# =========================
df = load_results()

if df.empty:
    st.info("등록된 조사 결과가 없습니다.")
    st.stop()

st.success("관리자 인증 완료")

# =========================
# 요약 지표
# =========================
st.subheader("📌 요약 지표")

col1, col2, col3 = st.columns(3)
col1.metric("총 조사 등록 건수", len(df))
col2.metric("해지사유 종류", df["해지사유"].nunique())
col3.metric("불만유형 종류", df["불만유형"].nunique())

st.divider()

# =========================
# 📈 시각화 영역
# =========================
st.subheader("📊 지사별 처리 건수")
branch_count = df["관리지사"].value_counts()
st.bar_chart(branch_count)

st.subheader("📊 담당자별 처리 건수")
owner_count = df["담당자"].value_counts()
st.bar_chart(owner_count)

st.subheader("📊 해지사유별 분포")
reason_count = df["해지사유"].value_counts()
st.bar_chart(reason_count)

st.subheader("📊 불만유형별 분포")
complaint_count = df["불만유형"].value_counts()
st.bar_chart(complaint_count)

st.divider()

# =========================
# 🔍 필터링 (관리자 분석용)
# =========================
st.subheader("🔍 조건별 데이터 조회")

col_f1, col_f2 = st.columns(2)

with col_f1:
    selected_reason = st.selectbox(
        "해지사유 선택",
        ["전체"] + sorted(df["해지사유"].dropna().unique().tolist())
    )

with col_f2:
    selected_complaint = st.selectbox(
        "불만유형 선택",
        ["전체"] + sorted(df["불만유형"].dropna().unique().tolist())
    )

filtered = df.copy()

if selected_reason != "전체":
    filtered = filtered[filtered["해지사유"] == selected_reason]

if selected_complaint != "전체":
    filtered = filtered[filtered["불만유형"] == selected_complaint]

st.caption(f"조회 결과: {len(filtered)}건")

# =========================
# 상세 데이터
# =========================
st.subheader("📋 전체 조사 데이터")
st.dataframe(filtered)
