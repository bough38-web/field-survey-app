import streamlit as st
from datetime import date
from storage import load_targets, save_result, load_reason_map

# =========================
# 설정
# =========================
BRANCH_ORDER = ["중앙", "강북", "서대문", "고양", "의정부", "남양주", "강릉", "원주"]

st.markdown(
    """
    ### 🚨 안내
    **정지처리계획입니다.  
    2025-12-31일까지 등록하여 주시기 바랍니다.**
    """
)

# =========================
# 데이터 로드
# =========================
df = load_targets()

if df.empty:
    st.warning("조사 대상 데이터가 없습니다.")
    st.stop()

# =========================
# 전처리 (nan 제거 + 지사명 정리)
# =========================
df = df.dropna(subset=["관리지사", "계약번호", "상호"])

df["관리지사표시"] = (
    df["관리지사"]
    .astype(str)
    .str.replace("지사", "", regex=False)
    .str.strip()
)

# =========================
# 🔹 사이드바 필터 (버튼식)
# =========================
st.sidebar.header("🔎 필터")

# 관리지사 버튼 (고정 순서)
available_branches = [
    b for b in BRANCH_ORDER
    if b in df["관리지사표시"].unique()
]

selected_branch = st.sidebar.radio(
    "관리지사",
    ["전체"] + available_branches
)

if selected_branch != "전체":
    df_f = df[df["관리지사표시"] == selected_branch]
else:
    df_f = df.copy()

# 담당자 버튼 (지사 선택에 따라 동적)
if "담당자" in df_f.columns:
    owners = sorted(
        df_f["담당자"]
        .dropna()
        .unique()
        .tolist()
    )

    selected_owner = st.sidebar.radio(
        "담당자",
        ["전체"] + owners
    )

    if selected_owner != "전체":
        df_f = df_f[df_f["담당자"] == selected_owner]
else:
    selected_owner = "전체"

if df_f.empty:
    st.warning("선택한 조건에 해당하는 조사 대상이 없습니다.")
    st.stop()

# =========================
# 조사 대상 선택
# =========================
row = st.selectbox(
    "조사 대상 선택",
    df_f.index,
    format_func=lambda i: f"{df_f.loc[i,'계약번호']} | {df_f.loc[i,'상호']}"
)

selected = df_f.loc[row]

# =========================
# 기본 정보 (읽기 전용)
# =========================
st.text_input("관리지사", selected.get("관리지사", ""), disabled=True)
st.text_input("계약번호", selected["계약번호"], disabled=True)
st.text_input("상호", selected["상호"], disabled=True)

if "담당자" in selected:
    st.text_input("담당자", selected.get("담당자", ""), disabled=True)

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
    .dropna()
    .unique()
    .tolist()
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
        "관리지사": selected.get("관리지사", ""),
        "계약번호": selected["계약번호"],
        "상호": selected["상호"],
        "담당자": selected.get("담당자", ""),
        "해지사유": cancel_reason,
        "불만유형": complaint_type,
        "세부내용": detail,
        "해지_해지일자": cancel_date.strftime("%Y-%m-%d"),
        "비고": remark
    })

    st.success("조치 정보가 저장되었습니다.")
