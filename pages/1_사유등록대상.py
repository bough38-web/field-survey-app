import streamlit as st
import pandas as pd
from datetime import date
from storage import load_targets, load_results, save_result, load_reason_map

st.set_page_config(page_title="사유등록대상", layout="wide")
st.title("📝 사유 등록 대상")

BRANCH_ORDER = ["중앙", "강북", "서대문", "고양", "의정부", "남양주", "강릉", "원주"]

st.info("📢 정지처리계획입니다. 2025-12-31일까지 등록해 주세요.")

# =========================
# 데이터 로드
# =========================
targets = load_targets()
results = load_results()

targets["계약번호"] = targets["계약번호"].astype(str)
results["계약번호"] = results["계약번호"].astype(str)

# 등록 완료 제외 (해지사유 기준)
registered_contracts = (
    results[results["해지사유"].notna()]["계약번호"].unique()
    if "해지사유" in results.columns else []
)

pending = targets[~targets["계약번호"].isin(registered_contracts)]

if pending.empty:
    st.success("🎉 모든 대상이 등록 완료되었습니다.")
    st.stop()

# =========================
# 사이드 필터
# =========================
pending["관리지사표시"] = pending["관리지사"].str.replace("지사", "").str.strip()

st.sidebar.header("🔎 필터")

branch = st.sidebar.radio(
    "관리지사",
    ["전체"] + [b for b in BRANCH_ORDER if b in pending["관리지사표시"].unique()]
)

if branch != "전체":
    pending = pending[pending["관리지사표시"] == branch]

owners = sorted(pending["담당자"].dropna().unique().tolist())
owner = st.sidebar.radio("담당자", ["전체"] + owners)

if owner != "전체":
    pending = pending[pending["담당자"] == owner]

# =========================
# 대상 선택
# =========================
idx = st.selectbox(
    "사유 등록 대상 선택",
    pending.index,
    format_func=lambda i: f"{pending.loc[i,'계약번호']} | {pending.loc[i,'상호']}"
)
row = pending.loc[idx]

# =========================
# 기본 정보
# =========================
st.text_input("관리지사", row["관리지사"], disabled=True)
st.text_input("계약번호", row["계약번호"], disabled=True)
st.text_input("상호", row["상호"], disabled=True)
st.text_input("담당자", row.get("담당자",""), disabled=True)

# =========================
# 해지사유
# =========================
reason_map = load_reason_map()

reason = st.selectbox("해지사유", sorted(reason_map["해지사유"].unique()))
complaints = reason_map[reason_map["해지사유"] == reason]["불만유형"].unique()

complaint = st.selectbox("불만유형", complaints)

detail = st.text_area(
    "세부 해지사유 및 불만 내용",
    disabled=(complaint == "불만없음")
)

# 업로드된 해지일자 기본 적용
try:
    default_date = pd.to_datetime(row.get("해지_해지일자")).date()
except:
    default_date = date.today()

cancel_date = st.date_input("해지_해지일자", value=default_date)
remark = st.text_area("비고")

# =========================
# 저장
# =========================
if st.button("💾 저장 후 다음"):
    save_result({
        "관리지사": row["관리지사"],
        "계약번호": row["계약번호"],
        "상호": row["상호"],
        "담당자": row.get("담당자",""),
        "해지사유": reason,
        "불만유형": complaint,
        "세부 해지사유 및 불만 내용": detail,
        "해지_해지일자": cancel_date.strftime("%Y-%m-%d"),
        "비고": remark
    })
    st.success("저장 완료! 다음 대상으로 이동합니다.")
    st.rerun()
