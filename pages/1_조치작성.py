import streamlit as st
from datetime import date

from storage import (
    load_targets,
    save_result,
    get_teams,
    get_owners_by_team
)

# =========================
# 안내 문구 (상단 고정)
# =========================
st.markdown(
    """
    ### 🚨 안내
    **정지처리계획입니다.  
    2025-12-31일까지 등록하여 주시기 바랍니다.**
    """
)

# =========================
# 조사 대상 로드
# =========================
df = load_targets()

if df.empty:
    st.warning("조사 대상 데이터가 아직 업로드되지 않았습니다.")
    st.stop()

# =========================
# 조사 대상 선택
# =========================
row = st.selectbox(
    "조사 대상 선택",
    df.index,
    format_func=lambda i: f"{df.loc[i,'계약번호']} | {df.loc[i,'상호']}"
)

selected = df.loc[row]

# =========================
# 🔒 읽기 전용 표시 영역
# =========================
st.text_input("관리지사", selected["관리지사"], disabled=True)
st.text_input("계약번호", selected["계약번호"], disabled=True)
st.text_input("상호", selected["상호"], disabled=True)

st.divider()

# =========================
# 👤 담당지사 / 담당자 (드롭다운)
# =========================
team = st.selectbox(
    "담당지사 / 팀",
    get_teams()
)

owner = st.selectbox(
    "담당자",
    get_owners_by_team(team)
)

# =========================
# ✍️ 조사 입력 영역
# =========================
survey_text = st.text_area("조사내역 등록")

# 🔥 해지_해지일자 (엑셀 I열 대응)
cancel_date = st.date_input(
    "해지_해지일자",
    value=date.today()
)

remark = st.text_area("비고")

# =========================
# 저장 처리
# =========================
if st.button("저장"):
    if not survey_text.strip():
        st.error("조사내역 등록은 필수입니다.")
        st.stop()

    save_result({
        "관리지사": selected["관리지사"],
        "계약번호": selected["계약번호"],
        "상호": selected["상호"],
        "담당지사/팀": team,
        "담당자": owner,
        "조사내역": survey_text,
        "해지_해지일자": cancel_date.strftime("%Y-%m-%d"),
        "비고": remark
    })

    st.success("조사 내역이 저장되었습니다.")
