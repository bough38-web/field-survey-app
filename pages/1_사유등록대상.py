import streamlit as st
import pandas as pd
import time
from datetime import date
from storage import load_targets, load_results, save_result, load_reason_map

# ==========================================
# 1. CSS 스타일링 (High-End & Responsive)
# ==========================================
st.markdown("""
<style>
    @import url("https://cdn.jsdelivr.net/gh/orioncactus/pretendard@v1.3.8/dist/web/static/pretendard.css");
    
    .stApp {
        background-color: #f8fafc;
        font-family: 'Pretendard', sans-serif;
    }
    
    /* 카드 컨테이너 스타일 */
    .card-container {
        background-color: #ffffff;
        padding: 24px;
        border-radius: 16px;
        border: 1px solid #e2e8f0;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);
        margin-bottom: 20px;
    }

    /* 반응형 정보 그리드 (핵심 개선) */
    .info-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
        gap: 16px;
    }
    
    /* 상호 등 긴 내용은 2칸 차지 (화면 넓을 때) */
    .wide-col {
        grid-column: span 2;
    }
    @media (max-width: 768px) {
        .wide-col { grid-column: span 1; } /* 모바일에서는 1칸 */
    }

    /* 정보 박스 디자인 */
    .info-box {
        background-color: #f8fafc;
        padding: 16px;
        border-radius: 12px;
        border: 1px solid #e2e8f0;
        display: flex;
        flex-direction: column;
        justify-content: center;
    }
    .info-label {
        font-size: 0.85rem;
        color: #64748b;
        margin-bottom: 6px;
        font-weight: 500;
    }
    .info-value {
        font-size: 1.15rem;
        font-weight: 700;
        color: #1e293b;
        word-break: break-all; /* 긴 텍스트 줄바꿈 */
    }
    .highlight-value {
        font-size: 1.15rem;
        font-weight: 800;
        color: #ef4444; /* 붉은색 강조 */
    }

    /* 저장 버튼 스타일 */
    div.stButton > button:first-child {
        background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%);
        color: white;
        border: none;
        padding: 0.6rem 1rem;
        font-weight: 600;
        border-radius: 8px;
        box-shadow: 0 2px 4px rgba(37, 99, 235, 0.2);
    }
    div.stButton > button:first-child:hover {
        transform: translateY(-1px);
    }
</style>
""", unsafe_allow_html=True)

st.title("📝 사유 등록 및 조치")

# ==========================================
# 2. 데이터 로드 및 전처리
# ==========================================
targets = load_targets()
results = load_results()

if targets.empty:
    st.warning("⚠️ 업로드된 데이터가 없습니다. 관리자에게 문의하세요.")
    st.stop()

# -------------------------------------------------------
# [핵심 수정] 해지_해지일자 -> 해지일자 컬럼명 통일 로직
# -------------------------------------------------------
if "해지_해지일자" in targets.columns:
    targets.rename(columns={"해지_해지일자": "해지일자"}, inplace=True)

# 계약번호 .0 제거 및 문자열 변환
if "계약번호" in targets.columns:
    targets["계약번호"] = targets["계약번호"].astype(str).str.replace(r'\.0$', '', regex=True)

if not results.empty and "계약번호" in results.columns:
    results["계약번호"] = results["계약번호"].astype(str).str.replace(r'\.0$', '', regex=True)
    registered_contracts = results[results["해지사유"].notna()]["계약번호"].unique()
else:
    registered_contracts = []

# 미처리 대상 필터링
pending = targets[~targets["계약번호"].isin(registered_contracts)]

# ==========================================
# 3. 진행률 대시보드
# ==========================================
total_cnt = len(targets)
done_cnt = len(registered_contracts)
pending_cnt = len(pending)
progress = done_cnt / total_cnt if total_cnt > 0 else 0

with st.container():
    c1, c2, c3 = st.columns([1, 4, 1])
    with c1: st.metric("남은 대상", f"{pending_cnt}건", delta_color="inverse")
    with c2: st.markdown(f"**전체 진행률** ({done_cnt}/{total_cnt})"); st.progress(progress)
    with c3: st.metric("완료", f"{done_cnt}건")

if pending.empty:
    st.success("🎉 모든 대상 처리가 완료되었습니다!")
    st.stop()

# ==========================================
# 4. 사이드바 필터 & 대상 선택
# ==========================================
if "관리지사" in pending.columns:
    pending["관리지사표시"] = pending["관리지사"].str.replace("지사", "").str.strip()
else:
    pending["관리지사표시"] = "미지정"

with st.sidebar:
    st.header("🔍 필터 옵션")
    br_list = ["전체"] + sorted(pending["관리지사표시"].unique().tolist())
    branch = st.selectbox("관리지사", br_list)
    if branch != "전체": pending = pending[pending["관리지사표시"] == branch]
    
    if "담당자" in pending.columns:
        owners = ["전체"] + sorted(pending["담당자"].dropna().unique().tolist())
        owner = st.selectbox("담당자", owners)
        if owner != "전체": pending = pending[pending["담당자"] == owner]
    
    st.caption(f"작업 대기: {len(pending)}건")

# 메인 선택창
idx = st.selectbox(
    "처리할 대상을 선택하세요:",
    pending.index,
    format_func=lambda i: f"[{pending.loc[i, '관리지사표시']}] {pending.loc[i, '상호']} ({pending.loc[i, '계약번호']})"
)
row = pending.loc[idx]

# ==========================================
# 5. 고객 정보 (반응형 UI 적용)
# ==========================================
st.markdown("### 🏢 고객 기본 정보")

# 날짜 포맷팅 (해지일자 사용)
origin_date = row.get("해지일자", "-") # 수정됨: 해지_해지일자 -> 해지일자
try: 
    if pd.notna(origin_date) and origin_date != "-":
        origin_date = pd.to_datetime(origin_date).strftime("%Y-%m-%d")
except: 
    pass

# HTML/CSS Grid로 정보 표시 (상호 길어도 깨지지 않음)
st.markdown(f"""
<div class="info-grid">
    <div class="info-box">
        <div class="info-label">관리지사</div>
        <div class="info-value">{row.get('관리지사', '-')}</div>
    </div>
    <div class="info-box">
        <div class="info-label">계약번호</div>
        <div class="info-value">{row.get('계약번호', '-')}</div>
    </div>
    <div class="info-box wide-col"> <div class="info-label">상호 (고객명)</div>
        <div class="info-value">{row.get('상호', '-')}</div>
    </div>
    <div class="info-box">
        <div class="info-label">담당자</div>
        <div class="info-value">{row.get('담당자', '-')}</div>
    </div>
    <div class="info-box">
        <div class="info-label">원본 해지일자</div>
        <div class="highlight-value">{origin_date}</div>
    </div>
</div>
""", unsafe_allow_html=True)

# ==========================================
# 6. 입력 폼 (Card Style)
# ==========================================
reason_map = load_reason_map()
if reason_map.empty:
    st.error("❌ 'reason_map.csv' 데이터가 없습니다.")
    st.stop()

st.markdown("### ✍️ 조치 내용 입력")

# 카드 스타일 컨테이너 시작
st.markdown('<div class="card-container">', unsafe_allow_html=True)

# 1행
c1, c2 = st.columns(2)
with c1:
    r = st.selectbox("해지 사유 (필수)", sorted(reason_map["해지사유"].unique()))
with c2:
    c = st.selectbox("불만 유형 (필수)", reason_map[reason_map["해지사유"]==r]["불만유형"].unique())

# 2행
d = st.text_area("상세 내용", height=100, placeholder="고객의 불만 사항이나 해지 사유를 상세히 입력해주세요.")

# 3행
c3, c4 = st.columns(2)
with c3:
    rd = st.date_input("사유 등록 일자", value=date.today())
with c4:
    rm = st.text_area("비고", height=70, placeholder="특이사항 입력")

st.markdown('</div>', unsafe_allow_html=True)
# 카드 스타일 컨테이너 끝

# ==========================================
# 7. 저장 로직 (안전장치 추가)
# ==========================================
st.markdown("---")

if st.button("💾 저장 후 다음 (Save & Next)", type="primary", use_container_width=True):
    # 로딩 표시
    with st.spinner("데이터를 저장하고 있습니다..."):
        try:
            # 저장할 데이터 구성
            save_data = {
                "관리지사": row.get("관리지사", ""),
                "계약번호": row.get("계약번호", ""),
                "상호": row.get("상호", ""),
                "담당자": row.get("담당자", ""),
                "해지사유": r,
                "불만유형": c,
                "세부 해지사유 및 불만 내용": d,
                
                # [수정] 해지일자 필드명 통일
                "해지일자": origin_date, 
                
                "사유등록일자": rd.strftime("%Y-%m-%d"),
                "비고": rm,
                "처리일시": pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            
            # 저장 함수 실행
            save_result(save_data)
            
            # 성공 알림
            st.toast(f"✅ 저장되었습니다! [{row.get('상호')}]", icon="💾")
            
            # 0.5초 후 새로고침 (즉시 반응)
            time.sleep(0.5)
            st.rerun()
            
        except Exception as e:
            # 에러 발생 시 무한 로딩 대신 에러 메시지 출력
            st.error(f"⛔ 저장 중 오류가 발생했습니다: {e}")
            st.error("혹시 엑셀 파일(survey_results.csv)이 열려있다면 닫고 다시 시도해주세요.")
