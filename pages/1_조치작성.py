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

# =========================
# 🔹 사이드바 필터
# =========================
st.sidebar.header("🔎 필터")

branches = ["전체"] + sorted(df["관리지사"].dropna().unique().tolist())
selected_branch = st.sidebar.selectbox("관리지사", branches)

filtered = df if selected_branch == "전체" else df[df["관리지사"] == selected_branch]

owners = ["전체"] + sorted(filtered["담당자"].dropna().unique().tolist())
selected_owner = st.sidebar.selectbox("담당자", owners)

if selected_owner != "전체":
    filtered = filtered[filtered["담당자"] == selected_owner]

if filtered.empty:
    st.warning("선택한 조건에 해당하는 데이터가 없습니다.")
    st.stop()

# =========================
# 조사 대상 선택
# =========================
row = st.selectbox(
    "조사 대상 선택",
    filtered.index,
    format_func=lambda i: f"{filtered.loc[i,'계약번호']} | {filtered.loc[i,'상호']}"
)

selected = filtered.loc[row]

# =========================
# 표시 영역
# =========================
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
