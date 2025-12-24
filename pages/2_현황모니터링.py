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
st.metric("총 조사 등록 건수", len(df))

# =========================
# 📈 시각화
# =========================
st.subheader("지사별 처리 건수")
branch_count = df["관리지사"].value_counts()
st.bar_chart(branch_count)

st.subheader("담당자별 처리 건수")
owner_count = df["담당자"].value_counts()
st.bar_chart(owner_count)

# =========================
# 상세 데이터
# =========================
st.subheader("전체 조사 데이터")
st.dataframe(df)
