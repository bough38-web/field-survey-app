import streamlit as st
from datetime import date
from storage import load_targets, load_results, save_result, load_reason_map

BRANCH_ORDER = ["중앙","강북","서대문","고양","의정부","남양주","강릉","원주"]

st.set_page_config(page_title="사유등록대상", layout="wide")
st.title("✍️ 사유등록대상")

targets = load_targets()
results = load_results()

# 이미 처리된 계약번호 제외
if not results.empty and "해지사유" in results.columns:
    done = results[results["해지사유"].notna()]["계약번호"].astype(str).unique()
    targets = targets[~targets["계약번호"].astype(str).isin(done)]

targets = targets.dropna(subset=["관리지사","계약번호"])
targets["관리지사표시"] = targets["관리지사"].str.replace("지사","",regex=False).str.strip()

if targets.empty:
    st.success("🎉 모든 대상이 처리 완료되었습니다.")
    st.stop()

st.sidebar.header("🔎 필터")
branches = [b for b in BRANCH_ORDER if b in targets["관리지사표시"].unique()]
sel_branch = st.sidebar.radio("관리지사", ["전체"] + branches)
df = targets if sel_branch=="전체" else targets[targets["관리지사표시"]==sel_branch]

owners = sorted(df["담당자"].dropna().unique().tolist())
sel_owner = st.sidebar.radio("담당자", ["전체"] + owners)
if sel_owner!="전체":
    df = df[df["담당자"]==sel_owner]

df = df.reset_index(drop=True)

idx = st.selectbox(
    "처리 대상 선택",
    range(len(df)),
    format_func=lambda i: f"{df.loc[i,'계약번호']} | {df.loc[i,'상호']}"
)
row = df.loc[idx]

st.text_input("관리지사", row["관리지사"], disabled=True)
st.text_input("계약번호", row["계약번호"], disabled=True)
st.text_input("상호", row["상호"], disabled=True)
st.text_input("담당자", row.get("담당자",""), disabled=True)

reason_map = load_reason_map()
reason = st.selectbox("해지사유", sorted(reason_map["해지사유"].unique()))
complaints = reason_map[reason_map["해지사유"]==reason]["불만유형"].unique()
complaint = st.selectbox("불만유형", complaints)

detail = st.text_area("세부 해지사유 및 불만 내용")
cancel_date = st.date_input("해지_해지일자", value=date.today())
remark = st.text_area("비고")

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
    st.experimental_rerun()
