import streamlit as st
import pandas as pd
from storage import get_owners_by_department

st.markdown(
    """
    ### 🚨 안내
    **정지처리계획입니다.  
    2025-12-31일까지 등록하여 주시기 바랍니다.**
    """
)

df = pd.read_csv("storage/survey_targets.csv")

row = st.selectbox(
    "조사 대상 선택",
    df.index,
    format_func=lambda i: f"{df.loc[i,'계약번호']} | {df.loc[i,'상호']}"
)

selected = df.loc[row]

# 🔒 읽기 전용 표시
st.text_input("관리지사", selected["관리지사"], disabled=True)
st.text_input("계약번호", selected["계약번호"], disabled=True)
st.text_input("상호", selected["상호"], disabled=True)

# ✍️ 입력 영역
survey_text = st.text_area("조사내역 등록")
handler = st.text_input("처리자", selected.get("담당자", ""))
remark = st.text_area("비고")

if st.button("저장"):
    result = {
        "관리지사": selected["관리지사"],
        "계약번호": selected["계약번호"],
        "상호": selected["상호"],
        "조사내역": survey_text,
        "처리자": handler,
        "비고": remark
    }

    # CSV append
    results = pd.read_csv("storage/survey_results.csv") \
        if Path("storage/survey_results.csv").exists() else pd.DataFrame()

    results = pd.concat([results, pd.DataFrame([result])])
    results.to_csv("storage/survey_results.csv", index=False)

    st.success("조사 내역이 저장되었습니다.")
