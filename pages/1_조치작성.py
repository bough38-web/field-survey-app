import streamlit as st
from datetime import date
from storage import load_targets, save_result

st.markdown(
    """
    ### 🚨 안내
    **정지처리계획입니다.  
    2025-12-31일까지 등록하여 주시기 바랍니다.**
    """
)

df = load_targets()
if df.empty:
    st.warning("조사 대상 데이터가 없습니다.")
    st.stop()

row = st.selectbox(
    "조사 대상 선택",
    df.index,
    format_func=lambda i: f"{df.loc[i,'계약번호']} | {df.loc[i,'상호']}"
)

selected = df.loc[row]

st.text_input("관리지사", selected["관리지사"], disabled=True)
st.text_input("계약번호", selected["계약번호"], disabled=True)
st.text_input("상호", selected["상호"], disabled=True)
st.text_input("담당자", selected.get("담당자", ""), disabled=True)

survey = st.text_area("조사내역 등록")
cancel_date = st.date_input("해지_해지일자", value=date.today())
remark = st.text_area("비고")

if st.button("저장"):
    if not survey.strip():
        st.error("조사내역은 필수입니다.")
        st.stop()

    save_result({
        "관리지사": selected["관리지사"],
        "계약번호": selected["계약번호"],
        "상호": selected["상호"],
        "담당자": selected.get("담당자", ""),
        "조사내역": survey,
        "해지_해지일자": cancel_date.strftime("%Y-%m-%d"),
        "비고": remark
    })

    st.success("조사 내역이 저장되었습니다.")
