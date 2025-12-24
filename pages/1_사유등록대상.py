import streamlit as st
import pandas as pd
from datetime import date
from storage import load_targets, load_results, save_result, load_reason_map

st.set_page_config(page_title="사유등록대상", layout="wide")
st.title("📝 사유 등록 대상")

BRANCH_ORDER = ["중앙", "강북", "서대문", "고양", "의정부", "남양주", "강릉", "원주"]

st.info("📢 정지처리계획입니다. 2025-12-31일까지 등록해 주세요.")

# =========================
# 1. 데이터 로드 및 초기화 (버그 수정 핵심)
# =========================
targets = load_targets()
results = load_results()

# 업로드된 대상이 아예 없는 경우 처리
if targets.empty:
    st.warning("⚠️ 아직 업로드된 조사 대상이 없습니다. '조사 대상 업로드' 메뉴를 먼저 이용해주세요.")
    st.stop()

# '계약번호' 컬럼을 문자열로 통일 (대상 데이터)
if "계약번호" in targets.columns:
    targets["계약번호"] = targets["계약번호"].astype(str)

# '계약번호' 컬럼을 문자열로 통일 (결과 데이터)
# 수정사항: results가 비어있거나 컬럼이 없을 때 에러 방지
if not results.empty and "계약번호" in results.columns:
    results["계약번호"] = results["계약번호"].astype(str)
    registered_contracts = results[results["해지사유"].notna()]["계약번호"].unique()
else:
    registered_contracts = []

# 미등록 대상 필터링
pending = targets[~targets["계약번호"].isin(registered_contracts)]

if pending.empty:
    st.success("🎉 모든 대상이 등록 완료되었습니다! 수고하셨습니다.")
    st.stop()

# =========================
# 2. 사이드바 필터
# =========================
if "관리지사" in pending.columns:
    pending["관리지사표시"] = pending["관리지사"].str.replace("지사", "").str.strip()
else:
    pending["관리지사표시"] = "미지정"

st.sidebar.header("🔎 필터")

# 지사 필터
available_branches = [b for b in BRANCH_ORDER if b in pending["관리지사표시"].unique()]
# 기타 지사가 있을 경우 추가
other_branches = [b for b in pending["관리지사표시"].unique() if b not in BRANCH_ORDER]
branch_options = ["전체"] + available_branches + other_branches

branch = st.sidebar.radio("관리지사", branch_options)

if branch != "전체":
    pending = pending[pending["관리지사표시"] == branch]

# 담당자 필터
if "담당자" in pending.columns:
    owners = sorted(pending["담당자"].dropna().unique().tolist())
    owner = st.sidebar.radio("담당자", ["전체"] + owners)

    if owner != "전체":
        pending = pending[pending["담당자"] == owner]

# =========================
# 3. 대상 선택 (Pending 목록이 있을 때만)
# =========================
if pending.empty:
    st.warning("조건에 맞는 대상이 없습니다.")
    st.stop()

idx = st.selectbox(
    "사유 등록 대상 선택",
    pending.index,
    format_func=lambda i: f"{pending.loc[i, '계약번호']} | {pending.loc[i, '상호']}"
)
row = pending.loc[idx]

# =========================
# 4. 입력 폼
# =========================
st.markdown("### 🏢 기본 정보")
col1, col2, col3, col4 = st.columns(4)
with col1:
    st.text_input("관리지사", row.get("관리지사", ""), disabled=True)
with col2:
    st.text_input("계약번호", row.get("계약번호", ""), disabled=True)
with col3:
    st.text_input("상호", row.get("상호", ""), disabled=True)
with col4:
    st.text_input("담당자", row.get("담당자", ""), disabled=True)

st.markdown("---")
st.markdown("### ✍️ 조치 내용 입력")

# 해지사유 데이터 로드
reason_map = load_reason_map()

if reason_map.empty:
    st.error("❌ 'reason_map.csv' 파일이 없거나 비어 있습니다.")
    st.stop()

# 사유 선택
c1, c2 = st.columns(2)
with c1:
    reason = st.selectbox("해지사유", sorted(reason_map["해지사유"].unique()))
with c2:
    complaints = reason_map[reason_map["해지사유"] == reason]["불만유형"].unique()
    complaint = st.selectbox("불만유형", complaints)

detail = st.text_area(
    "세부 해지사유 및 불만 내용",
    height=100,
    placeholder="불만 내용이 있다면 구체적으로 작성해주세요.",
    disabled=(complaint == "불만없음")
)

# 날짜 및 비고
c3, c4 = st.columns(2)
with c3:
    # 업로드된 해지일자가 있으면 가져오고, 없으면 오늘 날짜
    try:
        if pd.notna(row.get("해지_해지일자")):
            default_date = pd.to_datetime(row.get("해지_해지일자")).date()
        else:
            default_date = date.today()
    except:
        default_date = date.today()
        
    cancel_date = st.date_input("해지(예정) 일자", value=default_date)

with c4:
    remark = st.text_area("비고", height=100)

# =========================
# 5. 저장 로직
# =========================
st.markdown("---")
if st.button("💾 저장 후 다음", type="primary", use_container_width=True):
    save_data = {
        "관리지사": row.get("관리지사", ""),
        "계약번호": row.get("계약번호", ""),
        "상호": row.get("상호", ""),
        "담당자": row.get("담당자", ""),
        "해지사유": reason,
        "불만유형": complaint,
        "세부 해지사유 및 불만 내용": detail,
        "해지_해지일자": cancel_date.strftime("%Y-%m-%d"),
        "비고": remark,
        "처리일시": pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S") # 처리 시간 기록 추가
    }
    
    save_result(save_data)
    st.success("✅ 저장되었습니다! 다음 대상으로 이동합니다.")
    st.rerun()
