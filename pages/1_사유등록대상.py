import streamlit as st
import pandas as pd
import time
from datetime import date
from storage import load_targets, load_results, save_result, load_reason_map

# ==========================================
# 1. 페이지 설정 및 스타일링
# ==========================================
st.set_page_config(page_title="사유 등록 및 조치", layout="wide", page_icon="📝")

st.markdown("""
<style>
    .stApp {
        background-color: #f8fafc;
    }
    .stContainer {
        background-color: #ffffff;
        border-radius: 12px;
        padding: 20px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);
        border: 1px solid #e2e8f0;
        margin-bottom: 1rem;
    }
    [data-testid="stHeader"] {
        background-color: #f8fafc;
    }
    h1, h2, h3 {
        font-family: 'Pretendard', sans-serif;
        color: #1e293b;
    }
    .info-label {
        font-size: 0.85rem;
        color: #64748b;
        margin-bottom: 0.2rem;
    }
    .info-value {
        font-size: 1.1rem;
        font-weight: 600;
        color: #0f172a;
    }
    /* 중요 정보(해지일자 등) 강조 */
    .highlight-value {
        font-size: 1.1rem;
        font-weight: 700;
        color: #ef4444; /* Red color for termination date */
    }
    div.stButton > button:first-child {
        background-color: #2563eb;
        color: white;
        border-radius: 8px;
        border: none;
        padding: 0.5rem 1rem;
        font-weight: 600;
        transition: all 0.2s;
    }
    div.stButton > button:first-child:hover {
        background-color: #1d4ed8;
        transform: translateY(-1px);
        box-shadow: 0 4px 6px rgba(37, 99, 235, 0.2);
    }
</style>
""", unsafe_allow_html=True)

st.title("📝 사유 등록 및 조치")
st.markdown("조사 대상 고객의 **해지 사유** 및 **불만 내용**을 입력하는 페이지입니다.")

# ==========================================
# 2. 데이터 로드 및 전처리
# ==========================================
targets = load_targets()
results = load_results()

if targets.empty:
    st.warning("⚠️ 업로드된 조사 대상 데이터가 없습니다. '조사 대상 업로드' 메뉴를 먼저 이용해주세요.")
    st.stop()

if "계약번호" in targets.columns:
    targets["계약번호"] = targets["계약번호"].astype(str)

if not results.empty and "계약번호" in results.columns:
    results["계약번호"] = results["계약번호"].astype(str)
    registered_contracts = results[results["해지사유"].notna()]["계약번호"].unique()
else:
    registered_contracts = []

pending = targets[~targets["계약번호"].isin(registered_contracts)]

# ==========================================
# 3. 진행 상황 (Progress Bar)
# ==========================================
total_cnt = len(targets)
done_cnt = len(registered_contracts)
pending_cnt = len(pending)
progress = done_cnt / total_cnt if total_cnt > 0 else 0

col_kpi1, col_kpi2 = st.columns([3, 1])
with col_kpi1:
    st.progress(progress)
with col_kpi2:
    st.caption(f"진행률: **{progress*100:.1f}%** ({done_cnt}/{total_cnt}) | 잔여: **{pending_cnt}건**")

if pending.empty:
    st.success("🎉 모든 대상이 처리되었습니다! 수고하셨습니다.")
    st.stop()

# ==========================================
# 4. 사이드바 필터
# ==========================================
if "관리지사" in pending.columns:
    pending["관리지사표시"] = pending["관리지사"].str.replace("지사", "").str.strip()
else:
    pending["관리지사표시"] = "미지정"

st.sidebar.header("🔍 작업 대상 필터")

BRANCH_ORDER = ["중앙", "강북", "서대문", "고양", "의정부", "남양주", "강릉", "원주"]
available_branches = [b for b in BRANCH_ORDER if b in pending["관리지사표시"].unique()]
other_branches = [b for b in pending["관리지사표시"].unique() if b not in BRANCH_ORDER]
branch_options = ["전체"] + available_branches + other_branches

branch = st.sidebar.selectbox("관리지사 선택", branch_options)

if branch != "전체":
    pending = pending[pending["관리지사표시"] == branch]

if "담당자" in pending.columns:
    owners = sorted(pending["담당자"].dropna().unique().tolist())
    owner = st.sidebar.selectbox("담당자 선택", ["전체"] + owners)

    if owner != "전체":
        pending = pending[pending["담당자"] == owner]

# ==========================================
# 5. 작업 대상 선택
# ==========================================
st.markdown("---")

if pending.empty:
    st.warning("선택한 조건에 맞는 대상이 없습니다.")
    st.stop()

col_sel1, col_sel2 = st.columns([1, 2])
with col_sel1:
    st.info(f"💡 현재 조건 대기 건수: **{len(pending)}건**")

with col_sel2:
    idx = st.selectbox(
        "작업할 대상을 선택하세요",
        pending.index,
        format_func=lambda i: f"[{pending.loc[i, '관리지사표시']}] {pending.loc[i, '상호']} ({pending.loc[i, '계약번호']})"
    )
row = pending.loc[idx]

# ==========================================
# 6. 고객 정보 및 입력 폼 (수정됨)
# ==========================================

# --- [카드 1] 고객 기본 정보 (해지일자 고정 표시) ---
with st.container():
    st.markdown("### 🏢 고객 기본 정보")
    
    # 원본 파일의 해지일자 가져오기 (없으면 '-')
    origin_cancel_date = row.get("해지_해지일자")
    if pd.isna(origin_cancel_date):
        origin_cancel_date = "-"
    else:
        # 날짜 형식만 깔끔하게 표시
        try:
            origin_cancel_date = pd.to_datetime(origin_cancel_date).strftime("%Y-%m-%d")
        except:
            pass

    c1, c2, c3, c4, c5 = st.columns(5)
    with c1:
        st.markdown(f"<div class='info-label'>관리지사</div><div class='info-value'>{row.get('관리지사', '-')}</div>", unsafe_allow_html=True)
    with c2:
        st.markdown(f"<div class='info-label'>계약번호</div><div class='info-value'>{row.get('계약번호', '-')}</div>", unsafe_allow_html=True)
    with c3:
        st.markdown(f"<div class='info-label'>상호</div><div class='info-value'>{row.get('상호', '-')}</div>", unsafe_allow_html=True)
    with c4:
        st.markdown(f"<div class='info-label'>담당자</div><div class='info-value'>{row.get('담당자', '-')}</div>", unsafe_allow_html=True)
    with c5:
        # [수정] 원본 해지일자를 여기에 고정 (수정 불가)
        st.markdown(f"<div class='info-label'>원본 해지일자</div><div class='highlight-value'>{origin_cancel_date}</div>", unsafe_allow_html=True)

# --- [카드 2] 조치 내용 입력 (사유 등록 일자 적용) ---
reason_map = load_reason_map()
if reason_map.empty:
    st.error("❌ 'reason_map.csv' 파일이 없습니다.")
    st.stop()

with st.container():
    st.markdown("### ✍️ 조치 내용 입력")
    
    # 1행: 사유 및 불만유형
    rc1, rc2 = st.columns(2)
    with rc1:
        reason = st.selectbox("해지사유 (필수)", sorted(reason_map["해지사유"].unique()))
    with rc2:
        complaints = reason_map[reason_map["해지사유"] == reason]["불만유형"].unique()
        complaint = st.selectbox("불만유형 (필수)", complaints)

    # 2행: 세부 내용
    detail = st.text_area(
        "세부 해지사유 및 불만 내용",
        height=120,
        placeholder="고객의 구체적인 불만 사항이나 해지 사유를 상세히 기록해주세요."
    )

    # 3행: 사유 등록 일자(Today) 및 비고
    rc3, rc4 = st.columns(2)
    with rc3:
        # [수정] 해지(예정)일자 -> 사유 등록 일자 (기본값: 오늘)
        reg_date = st.date_input("사유 등록 일자", value=date.today(), help="실제 사유를 등록/처리하는 일자입니다.")

    with rc4:
        remark = st.text_area("비고", height=80, placeholder="기타 특이사항 입력")

# ==========================================
# 7. 저장 및 알림
# ==========================================
st.markdown("###") 

if st.button("💾 저장 후 다음 (Save & Next)", type="primary", use_container_width=True):
    # 1. 데이터 패키징
    save_data = {
        "관리지사": row.get("관리지사", ""),
        "계약번호": row.get("계약번호", ""),
        "상호": row.get("상호", ""),
        "담당자": row.get("담당자", ""),
        "해지사유": reason,
        "불만유형": complaint,
        "세부 해지사유 및 불만 내용": detail,
        
        # [수정] 데이터 저장 방식 변경
        "해지_해지일자": row.get("해지_해지일자", ""), # 원본 엑셀 값 그대로 보존
        "사유등록일자": reg_date.strftime("%Y-%m-%d"), # 입력한 등록일자 저장
        
        "비고": remark,
        "처리일시": pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    
    # 2. 저장 실행
    save_result(save_data)
    
    # 3. 알림 및 리로드
    st.toast(f"✅ [{row.get('상호')}] 저장 완료! 다음 건으로 이동합니다.", icon="💾")
    time.sleep(0.7)
    st.rerun()
