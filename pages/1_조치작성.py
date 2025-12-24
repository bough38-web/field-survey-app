import streamlit as st
from datetime import date
from storage import load_targets, save_result, load_reason_map

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

# =========================
# 기본 정보 (읽기 전용)
# =========================
st.text_input("관리지사", selected.get("관리지사",""), disabled=True)
st.text_input("계약번호", selected["계약번호"], disabled=True)
st.text_input("상호", selected["상호"], disabled=True)

# =========================
# 해지사유 / 불만유형
# =========================
reason_map = load_reason_map()

default_reason = selected.get("해지사유", "")
default_complaint = selected.get("불만유형", "")
default_detail = selected.get("세부내용", "")

reasons = sorted(reason_map["해지사유"].dropna().unique())
cancel_reason = st.selectbox(
    "해지사유",
    reasons,
    index=reasons.index(default_reason) if default_reason in reasons else 0
)

complaints = (
    reason_map[reason_map["해지사유"] == cancel_reason]["불만유형"]
    .dropna().unique().tolist()
)

complaint_type = st.selectbox(
    "불만유형",
    complaints,
    index=complaints.index(default_complaint)
    if default_complaint in complaints else 0
)

detail = st.text_area(
    "세부 해지사유 및 불만 내용",
    value=default_detail,
    disabled=(complaint_type == "불만없음")
)

# =========================
# 기타 입력
# =========================
cancel_date = st.date_input("해지_해지일자", value=date.today())
remark = st.text_area("비고")

# =========================
# 저장
# =========================
if st.button("저장"):
    save_result({
        "관리지사": selected.get("관리지사",""),
        "계약번호": selected["계약번호"],
        "상호": selected["상호"],
        "해지사유": cancel_reason,
        "불만유형": complaint_type,
        "세부내용": detail,
        "해지_해지일자": cancel_date.strftime("%Y-%m-%d"),
        "비고": remark
    })

    st.success("조사 정보가 저장되었습니다.")
