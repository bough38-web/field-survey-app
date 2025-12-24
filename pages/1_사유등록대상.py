import streamlit as st
import pandas as pd
import time
from datetime import date
from storage import load_targets, load_results, save_result, load_reason_map

# ==========================================
# 1. 페이지 설정 및 스타일링 (High-End CSS)
# ==========================================
st.set_page_config(page_title="사유 등록 및 조치", layout="wide", page_icon="📝")

st.markdown("""
<style>
    /* 1. 전체 폰트 및 배경 설정 */
    @import url("https://cdn.jsdelivr.net/gh/orioncactus/pretendard@v1.3.8/dist/web/static/pretendard.css");
    
    .stApp {
        background-color: #f8fafc; /* 아주 연한 회색 배경 */
        font-family: 'Pretendard', sans-serif;
    }

    /* 2. 헤더 스타일링 */
    h1, h2, h3 {
        font-family: 'Pretendard', sans-serif;
        color: #1e293b;
        letter-spacing: -0.5px;
    }
    
    /* 3. 컨테이너(카드) 디자인 */
    .stContainer {
        background-color: #ffffff;
        border-radius: 16px;
        padding: 24px;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.03); /* 부드러운 그림자 */
        border: 1px solid #f1f5f9;
        margin-bottom: 20px;
    }

    /* 4. 정보 라벨 및 값 스타일링 (고객정보 카드용) */
    .info-box {
        background-color: #f8fafc;
        padding: 15px;
        border-radius: 12px;
        border: 1px solid #e2e8f0;
        text-align: center;
        transition: transform 0.2s;
    }
    .info-box:hover {
        transform: translateY(-2px);
        border-color: #cbd5e1;
    }
    .info-label {
        font-size: 0.85rem;
        color: #64748b;
        margin-bottom: 5px;
        font-weight: 500;
    }
    .info-value {
        font-size: 1.15rem;
        font-weight: 700;
        color: #0f172a;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
    }
    /* 중요 정보(원본 해지일자) 강조 - 붉은색 */
    .highlight-value {
        font-size: 1.15rem;
        font-weight: 800;
        color: #ef4444; 
    }

    /* 5. 버튼 스타일링 (Primary Button) */
    div.stButton > button:first-child {
        background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%);
        color: white;
        border-radius: 10px;
        border: none;
        padding: 0.6rem 1.2rem;
        font-weight: 600;
        box-shadow: 0 4px 6px -1px rgba(37, 99, 235, 0.2);
        transition: all 0.2s;
    }
    div.stButton > button:first-child:hover {
        transform: translateY(-2px);
        box-shadow: 0 10px 15px -3px rgba(37, 99, 235, 0.3);
    }

    /* 6. 입력 필드 테두리 부드럽게 */
    .stTextInput > div > div > input, 
    .stSelectbox > div > div > div, 
    .stDateInput > div > div > input,
    .stTextArea > div > div > textarea {
        border-radius: 8px;
        border-color: #e2e8f0;
    }
    .stProgress > div > div > div > div {
        background: linear-gradient(90deg, #3b82f6, #60a5fa);
    }
</style>
""", unsafe_allow_html=True)

# 헤더 영역
col_header, col_logo = st.columns([4, 1])
with col_header:
    st.title("📝 사유 등록 및 조치")
    st.markdown("<div style='color:#64748b; margin-top:-10px;'>고객의 <b>해지 사유</b>를 분석하고 <b>조치 결과</b>를 등록하는 업무 페이지입니다.</div>", unsafe_allow_html=True)

# ==========================================
# 2. 데이터 로드 및 전처리 (로직 유지)
# ==========================================
targets = load_targets()
results = load_results()

if targets.empty:
    st.warning("⚠️ 업로드된 조사 대상 데이터가 없습니다. '조사 대상 업로드' 메뉴를 이용해주세요.")
    st.stop()

# 계약번호 .0 제거 로직
if "계약번호" in targets.columns:
    targets["계약번호"] = targets["계약번호"].astype(str).str.replace(r'\.0$', '', regex=True)

if not results.empty and "계약번호" in results.columns:
    results["계약번호"] = results["계약번호"].astype(str).str.replace(r'\.0$', '', regex=True)
    registered_contracts = results[results["해지사유"].notna()]["계약번호"].unique()
else:
    registered_contracts = []

pending = targets[~targets["계약번호"].isin(registered_contracts)]

# ==========================================
# 3. 진행 상황 (Progress Dashboard)
# ==========================================
total_cnt = len(targets)
done_cnt = len(registered_contracts)
pending_cnt = len(pending)
progress = done_cnt / total_cnt if total_cnt > 0 else 0

# Progress Container
with st.container():
    c1, c2, c3 = st.columns([1, 4, 1])
    with c1:
        st.metric("남은 대상", f"{pending_cnt}건", delta="Work to do", delta_color="inverse")
    with c2:
        st.markdown(f"**전체 진행률** ({done_cnt}/{total_cnt})")
        st.progress(progress)
    with c3:
        st.metric("완료", f"{done_cnt}건", delta="Done")

if pending.empty:
    st.balloons()
    st.success("🎉 모든 대상 처리가 완료되었습니다! 수고하셨습니다.")
    st.stop()

# ==========================================
# 4. 필터 및 선택 (Sidebar & Main)
# ==========================================
if "관리지사" in pending.columns:
    pending["관리지사표시"] = pending["관리지사"].str.replace("지사", "").str.strip()
else:
    pending["관리지사표시"] = "미지정"

# 사이드바 디자인 개선
with st.sidebar:
    st.header("🔍 필터 옵션")
    
    BRANCH_ORDER = ["중앙", "강북", "서대문", "고양", "의정부", "남양주", "강릉", "원주"]
    available_branches = [b for b in BRANCH_ORDER if b in pending["관리지사표시"].unique()]
    other_branches = [b for b in pending["관리지사표시"].unique() if b not in BRANCH_ORDER]
    
    branch = st.selectbox("🏢 관리지사", ["전체"] + available_branches + other_branches)
    
    if branch != "전체":
        pending = pending[pending["관리지사표시"] == branch]
        
    if "담당자" in pending.columns:
        owners = sorted(pending["담당자"].dropna().unique().tolist())
        owner = st.selectbox("👤 담당자", ["전체"] + owners)
        if owner != "전체":
            pending = pending[pending["담당자"] == owner]
            
    st.divider()
    st.caption(f"필터링 결과: {len(pending)}건 대기 중")

# 메인 선택창
st.markdown("### 📌 작업 대상 선택")
idx = st.selectbox(
    "처리할 대상을 선택해주세요:",
    pending.index,
    format_func=lambda i: f"[{pending.loc[i, '관리지사표시']}] {pending.loc[i, '상호']} (계약번호: {pending.loc[i, '계약번호']})"
)
row = pending.loc[idx]

# ==========================================
# 5. 고객 정보 카드 (Visual Styling)
# ==========================================
st.markdown("### 🏢 고객 기본 정보")

# HTML/CSS를 활용한 정보 카드 그리드
# 원본 해지일자 처리
origin_cancel_date = row.get("해지일자")
if pd.isna(origin_cancel_date):
    origin_cancel_date = "-"
else:
    try:
        origin_cancel_date = pd.to_datetime(origin_cancel_date).strftime("%Y-%m-%d")
    except:
        pass

# 5열 정보 카드 렌더링
info_cols = st.columns(5)
infos = [
    ("관리지사", row.get('관리지사', '-')),
    ("계약번호", row.get('계약번호', '-')),
    ("상호", row.get('상호', '-')),
    ("담당자", row.get('담당자', '-')),
    ("해지일자", origin_cancel_date) # 붉은색 강조 적용됨
]

for i, (label, value) in enumerate(infos):
    with info_cols[i]:
        # 마지막 항목(해지일자)일 경우 강조 스타일 적용
        value_class = "highlight-value" if label == "원본 해지일자" else "info-value"
        st.markdown(f"""
        <div class="info-box">
            <div class="info-label">{label}</div>
            <div class="{value_class}">{value}</div>
        </div>
        """, unsafe_allow_html=True)

# ==========================================
# 6. 입력 폼 (Card Style)
# ==========================================
reason_map = load_reason_map()
if reason_map.empty:
    st.error("❌ 데이터 로드 실패: 'reason_map.csv'가 없습니다.")
    st.stop()

st.markdown("### ✍️ 조치 내용 입력")

with st.container():
    # 1. 사유 선택 영역
    c1, c2 = st.columns(2)
    with c1:
        reason = st.selectbox("해지 사유 (필수)", sorted(reason_map["해지사유"].unique()))
    with c2:
        complaints = reason_map[reason_map["해지사유"] == reason]["불만유형"].unique()
        complaint = st.selectbox("불만 유형 (필수)", complaints)

    # 2. 상세 내용 영역
    detail = st.text_area(
        "상세 사유 및 고객 불만 내용",
        height=120,
        placeholder="고객의 구체적인 불만 사항이나 해지 사유를 상세히 기록해주세요.\n(예: 타사 프로모션 제안으로 인한 이탈 고민 중)"
    )

    # 3. 날짜 및 비고 영역
    c3, c4 = st.columns(2)
    with c3:
        reg_date = st.date_input("사유 등록 일자 (업무 처리일)", value=date.today(), help="실제 사유를 등록/처리하는 일자입니다.")
    with c4:
        remark = st.text_area("비고 (특이사항)", height=80, placeholder="추가적인 메모가 있다면 작성해주세요.")

# ==========================================
# 7. 저장 버튼 및 처리
# ==========================================
st.markdown("---")
col_save, _ = st.columns([1, 3])

with col_save:
    if st.button("💾 저장 후 다음 (Save & Next)", type="primary", use_container_width=True):
        # 데이터 패키징
        save_data = {
            "관리지사": row.get("관리지사", ""),
            "계약번호": row.get("계약번호", ""),
            "상호": row.get("상호", ""),
            "담당자": row.get("담당자", ""),
            "해지사유": reason,
            "불만유형": complaint,
            "세부 해지사유 및 불만 내용": detail,
            "해지_해지일자": row.get("해지_해지일자", ""), # 원본 유지
            "사유등록일자": reg_date.strftime("%Y-%m-%d"), # 신규 등록일
            "비고": remark,
            "처리일시": pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        
        save_result(save_data)
        
        # Toast 알림
        st.toast(f"✅ [{row.get('상호')}] 저장되었습니다! 다음 건으로 이동합니다.", icon="💾")
        time.sleep(0.7)
        st.rerun()
