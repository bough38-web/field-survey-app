import streamlit as st
import pandas as pd
import time
from datetime import date
from storage import load_targets, load_results, save_result, load_reason_map

# ==========================================
# 1. CSS 스타일링 (반응형 & 디자인 개선)
# ==========================================
st.markdown("""
<style>
    @import url("https://cdn.jsdelivr.net/gh/orioncactus/pretendard@v1.3.8/dist/web/static/pretendard.css");
    
    /* 전체 폰트 적용 */
    .stApp {
        background-color: #f8fafc;
        font-family: 'Pretendard', sans-serif;
    }

    /* 반응형 정보 카드 그리드 */
    .info-grid-container {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); /* 화면 좁으면 줄바꿈 */
        gap: 12px;
        margin-bottom: 20px;
    }
    
    /* 특정 카드는 넓게 쓰기 (상호 등) - CSS Grid의 span 활용 */
    .info-box-wide {
        grid-column: span 2;
    }
    @media (max-width: 768px) {
        .info-box-wide { grid-column: span 1; } /* 모바일에서는 1칸으로 */
    }

    /* 정보 박스 디자인 */
    .info-box {
        background-color: #ffffff;
        padding: 16px;
        border-radius: 12px;
        border: 1px solid #e2e8f0;
        box-shadow: 0 2px 4px rgba(0,0,0,0.02);
        display: flex;
        flex-direction: column;
        justify-content: center;
    }
    
    .info-label {
        font-size: 0.8rem;
        color: #64748b;
        margin-bottom: 4px;
        font-weight: 500;
    }
    
    .info-value {
        font-size: 1.1rem;
        font-weight: 700;
        color: #0f172a;
        word-break: break-all; /* 긴 단어 줄바꿈 */
        line-height: 1.4;
    }
    
    .highlight-value {
        font-size: 1.1rem;
        font-weight: 800;
        color: #ef4444; /* 붉은색 강조 */
    }

    /* 입력 폼 컨테이너 */
    .form-container {
        background-color: white;
        padding: 24px;
        border-radius: 16px;
        border: 1px solid #e2e8f0;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);
    }
</style>
""", unsafe_allow_html=True)

st.title("📝 사유 등록 및 조치")

# ==========================================
# 2. 데이터 로드
# ==========================================
targets = load_targets()
results = load_results()

if targets.empty:
    st.warning("⚠️ 데이터가 없습니다. 관리자에게 문의하세요.")
    st.stop()

# 전처리
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
# 3. 진행률 표시 (상단)
# ==========================================
total_cnt = len(targets)
done_cnt = len(registered_contracts)
pending_cnt = len(pending)
progress = done_cnt / total_cnt if total_cnt > 0 else 0

with st.container():
    c1, c2, c3 = st.columns([1, 4, 1])
    with c1: st.metric("남은 대상", f"{pending_cnt}건")
    with c2: st.markdown(f"**전체 진행률** ({done_cnt}/{total_cnt})"); st.progress(progress)
    with c3: st.metric("완료", f"{done_cnt}건")

if pending.empty:
    st.success("🎉 모든 대상 처리가 완료되었습니다!")
    st.stop()

# ==========================================
# 4. 필터 및 대상 선택 (사이드바)
# ==========================================
if "관리지사" in pending.columns:
    pending["관리지사표시"] = pending["관리지사"].str.replace("지사", "").str.strip()
else:
    pending["관리지사표시"] = "미지정"

with st.sidebar:
    st.header("🔍 필터")
    br_list = ["전체"] + sorted(pending["관리지사표시"].unique().tolist())
    branch = st.selectbox("관리지사", br_list)
    if branch != "전체": pending = pending[pending["관리지사표시"] == branch]
    
    if "담당자" in pending.columns:
        owners = ["전체"] + sorted(pending["담당자"].dropna().unique().tolist())
        owner = st.selectbox("담당자", owners)
        if owner != "전체": pending = pending[pending["담당자"] == owner]
    
    st.caption(f"대기 건수: {len(pending)}건")

# 메인 선택창
idx = st.selectbox(
    "작업 대상 선택", 
    pending.index, 
    format_func=lambda i: f"[{pending.loc[i, '관리지사표시']}] {pending.loc[i, '상호']} ({pending.loc[i, '계약번호']})"
)
row = pending.loc[idx]

# ==========================================
# 5. 고객 정보 (반응형 그리드 적용)
# ==========================================
st.markdown("### 🏢 고객 정보")

origin_date = row.get("해지_해지일자", "-")
try: origin_date = pd.to_datetime(origin_date).strftime("%Y-%m-%d")
except: pass

# HTML 그리드 생성 (상호는 넓게 보기 위해 class='info-box-wide' 적용 가능)
# 여기서는 CSS Grid가 자동 조절하도록 구성
html_content = f"""
<div class="info-grid-container">
    <div class="info-box">
        <div class="info-label">관리지사</div>
        <div class="info-value">{row.get('관리지사', '-')}</div>
    </div>
    <div class="info-box">
        <div class="info-label">계약번호</div>
        <div class="info-value">{row.get('계약번호', '-')}</div>
    </div>
    <div class="info-box info-box-wide"> <div class="info-label">상호 (고객명)</div>
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
"""
st.markdown(html_content, unsafe_allow_html=True)

# ==========================================
# 6. 입력 폼 (디자인 컨테이너 적용)
# ==========================================
reason_map = load_reason_map()
if reason_map.empty:
    st.error("⚠️ 'reason_map.csv' 파일이 없습니다. 관리자에게 문의하세요.")
    st.stop()

st.markdown("### ✍️ 조치 내용")

# 폼 컨테이너 시작
with st.container():
    st.markdown('<div class="form-container">', unsafe_allow_html=True)
    
    # 1행
    c1, c2 = st.columns(2)
    with c1: 
        r = st.selectbox("해지 사유 (필수)", sorted(reason_map["해지사유"].unique()))
    with c2: 
        c = st.selectbox("불만 유형 (필수)", reason_map[reason_map["해지사유"]==r]["불만유형"].unique())
    
    # 2행 (넓게)
    d = st.text_area("상세 내용", height=120, placeholder="구체적인 사유를 입력하세요.")
    
    # 3행
    c3, c4 = st.columns(2)
    with c3: 
        rd = st.date_input("사유 등록 일자", value=date.today())
    with c4: 
        rm = st.text_area("비고", height=75, placeholder="특이사항 입력")
        
    st.markdown('</div>', unsafe_allow_html=True)

# ==========================================
# 7. 저장 로직 (안전장치 추가)
# ==========================================
st.markdown("---")

# 버튼 클릭 감지
if st.button("💾 저장 후 다음 (Save & Next)", type="primary", use_container_width=True):
    # 저장 중임을 시각적으로 표시
    with st.spinner("데이터를 저장하고 있습니다..."):
        try:
            # 1. 저장할 데이터 구성
            data = {
                "관리지사": row.get("관리지사", ""),
                "계약번호": row.get("계약번호", ""),
                "상호": row.get("상호", ""),
                "담당자": row.get("담당자", ""),
                "해지사유": r,
                "불만유형": c,
                "세부 해지사유 및 불만 내용": d,
                "해지_해지일자": row.get("해지_해지일자", ""),
                "사유등록일자": rd.strftime("%Y-%m-%d"),
                "비고": rm,
                "처리일시": pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            
            # 2. 실제 파일 저장 실행 (storage.py 호출)
            save_result(data)
            
            # 3. 성공 알림 및 리로드
            st.toast(f"✅ 저장되었습니다! [{row.get('상호')}]", icon="💾")
            time.sleep(0.7) # 사용자가 알림을 볼 시간을 줌
            st.rerun()
            
        except PermissionError:
            st.error("⛔ 저장 실패: 'survey_results.csv' 파일이 엑셀에서 열려있습니다. 엑셀을 닫고 다시 시도해주세요.")
        except Exception as e:
            st.error(f"⛔ 알 수 없는 오류 발생: {e}")
