import streamlit as st
import pandas as pd
import time
from datetime import date
import io # 추가됨
import openai # 추가됨
from streamlit_mic_recorder import mic_recorder # 추가됨

from storage import load_targets, load_results, save_result, load_reason_map

# ==========================================
# [설정] OpenAI API 키 (필수 설정)
# ==========================================
# 실제 배포 시에는 st.secrets["OPENAI_API_KEY"] 사용을 권장합니다.
openai.api_key = "sk-..." # 👈 여기에 실제 API Key를 입력하세요

# ==========================================
# 0. AI 음성 처리 함수 (추가됨)
# ==========================================
def process_audio_summary(audio_bytes):
    try:
        # 1. Bytes -> File 객체 변환
        audio_file = io.BytesIO(audio_bytes)
        audio_file.name = "voice.wav"
        
        # 2. STT (Whisper)
        transcript = openai.audio.transcriptions.create(
            model="whisper-1", 
            file=audio_file, 
            language="ko"
        )
        raw_text = transcript.text

        # 3. LLM 요약 (GPT-4o)
        response = openai.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "현장 조치 내용을 보고서용으로 간결하게 요약(~~함, ~~했음 체)해줘."},
                {"role": "user", "content": raw_text}
            ]
        )
        summary = response.choices[0].message.content
        return raw_text, summary
    except Exception as e:
        return None, f"오류: {e}"

# ==========================================
# 1. High-End UI & CSS 스타일링
# ==========================================
st.markdown("""
<style>
    @import url("https://cdn.jsdelivr.net/gh/orioncactus/pretendard@v1.3.8/dist/web/static/pretendard.css");
    
    .stApp {
        background-color: #f8fafc;
        font-family: 'Pretendard', sans-serif;
    }
    
    /* 1. 반응형 정보 그리드 */
    .info-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
        gap: 12px;
        margin-bottom: 20px;
    }
    
    .info-box {
        background: white;
        padding: 16px;
        border-radius: 12px;
        border: 1px solid #e2e8f0;
        box-shadow: 0 2px 4px rgba(0,0,0,0.02);
        display: flex;
        flex-direction: column;
    }
    
    .info-label { font-size: 0.8rem; color: #64748b; margin-bottom: 4px; font-weight: 500; }
    .info-value { font-size: 1.1rem; font-weight: 700; color: #1e293b; word-break: break-all; }
    .highlight { color: #ef4444; }

    /* 2. 입력 폼 컨테이너 */
    .form-container {
        background-color: white;
        padding: 24px;
        border-radius: 16px;
        border: 1px solid #e2e8f0;
        box-shadow: 0 4px 6px -1px rgba(0,0,0,0.05);
    }
    
    /* 3. 저장 버튼 */
    div.stButton > button:first-child {
        background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%);
        color: white; border: none; padding: 0.7rem; font-weight: bold; border-radius: 10px;
        transition: transform 0.1s;
    }
    div.stButton > button:first-child:hover { transform: scale(1.02); }
</style>
""", unsafe_allow_html=True)

st.title("📝 사유 등록 및 조치")

# ==========================================
# 2. 데이터 로드 및 전처리
# ==========================================
targets = load_targets()
results = load_results()

if targets.empty:
    st.warning("⚠️ 데이터가 없습니다. 관리자에게 문의하세요.")
    st.stop()

# 처리 완료된 건 제외
done_ids = results[results["해지사유"].notna()]["계약번호"].unique() if not results.empty else []
pending = targets[~targets["계약번호"].isin(done_ids)]

# 진행률 대시보드
total = len(targets)
done = len(done_ids)
remain = len(pending)
prog = done / total if total > 0 else 0

with st.container():
    c1, c2, c3 = st.columns([1, 4, 1])
    with c1: st.metric("남은 대상", f"{remain}건", delta_color="inverse")
    with c2: st.markdown(f"**진행률** ({done}/{total})"); st.progress(prog)
    with c3: st.metric("완료", f"{done}건")

if pending.empty:
    st.success("🎉 모든 업무가 완료되었습니다!")
    st.stop()

# ==========================================
# 3. 필터 및 대상 선택
# ==========================================
if "관리지사" in pending.columns: 
    pending["지사"] = pending["관리지사"].str.replace("지사", "").str.strip()
else: 
    pending["지사"] = "미지정"

with st.sidebar:
    st.header("🔍 필터")
    b_sel = st.selectbox("관리지사", ["전체"] + sorted(pending["지사"].unique()))
    if b_sel != "전체": pending = pending[pending["지사"] == b_sel]
    
    if "담당자" in pending.columns:
        o_sel = st.selectbox("담당자", ["전체"] + sorted(pending["담당자"].dropna().unique()))
        if o_sel != "전체": pending = pending[pending["담당자"] == o_sel]
    
    st.caption(f"작업 대기: {len(pending)}건")

idx = st.selectbox(
    "처리 대상 선택",
    pending.index,
    format_func=lambda i: f"[{pending.loc[i, '지사']}] {pending.loc[i, '상호']} ({pending.loc[i, '계약번호']})"
)
row = pending.loc[idx]

# ==========================================
# 4. 고객 정보 (반응형 Grid)
# ==========================================
st.markdown("### 🏢 고객 기본 정보")

origin_date = row.get("해지일자", row.get("해지_해지일자", "-"))
try: 
    if pd.notna(origin_date) and str(origin_date).strip() != "-":
        origin_date = pd.to_datetime(origin_date).strftime("%Y-%m-%d")
    else:
        origin_date = "-"
except: 
    pass

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
    <div class="info-box" style="grid-column: span 2;">
        <div class="info-label">상호 (고객명)</div>
        <div class="info-value">{row.get('상호', '-')}</div>
    </div>
    <div class="info-box">
        <div class="info-label">담당자</div>
        <div class="info-value">{row.get('담당자', '-')}</div>
    </div>
    <div class="info-box">
        <div class="info-label">해지일자</div>
        <div class="info-value highlight">{origin_date}</div>
    </div>
</div>
""", unsafe_allow_html=True)

# ==========================================
# 5. 입력 폼 (녹음 기능 통합)
# ==========================================
reason_map = load_reason_map()
if reason_map.empty:
    st.error("⚠️ 'reason_map.csv' 파일이 필요합니다.")
    st.stop()

st.markdown("### ✍️ 조치 내용 입력")

# [Session State] 텍스트 영역 값을 제어하기 위한 초기화
if "current_detail" not in st.session_state:
    st.session_state["current_detail"] = ""

st.markdown('<div class="form-container">', unsafe_allow_html=True)

# 5-1. 상단 선택박스
c1, c2 = st.columns(2)
with c1: r = st.selectbox("해지 사유 (필수)", sorted(reason_map["해지사유"].unique()))
with c2: c = st.selectbox("불만 유형 (필수)", reason_map[reason_map["해지사유"]==r]["불만유형"].unique())

st.divider() # 구분선

# 5-2. 녹음 기능 (New!)
col_mic, col_desc = st.columns([1, 5])
with col_mic:
    # 녹음 버튼
    audio = mic_recorder(
        start_prompt="🎤 녹음",
        stop_prompt="⏹️ 완료",
        just_once=True,
        key='voice_rec'
    )

with col_desc:
    if audio:
        with st.spinner("🎧 음성 분석 및 요약 중..."):
            # AI 함수 호출
            raw_text, summary_text = process_audio_summary(audio['bytes'])
            
            if raw_text:
                # 요약된 내용을 세션 상태(텍스트박스 키)에 반영
                st.session_state["current_detail"] = summary_text
                st.caption(f"📝 원본: {raw_text}") # 원본 내용을 작게 표시
                st.rerun() # 화면 갱신하여 텍스트박스에 반영
    else:
        st.caption("👈 버튼을 눌러 내용을 말하면 자동으로 요약 입력됩니다.")

# 5-3. 상세 내용 텍스트 영역 (Session State 연결)
# key="current_detail"을 사용하여 코드에서 값을 변경(녹음 시)하거나 유저가 직접 수정 가능
d = st.text_area(
    "상세 내용", 
    height=100, 
    placeholder="내용을 입력하거나 녹음 기능을 사용하세요.",
    key="current_detail" 
)

# 5-4. 하단 정보
c3, c4 = st.columns(2)
with c3: rd = st.date_input("사유 등록 일자", value=date.today())
with c4: rm = st.text_area("비고", height=70, placeholder="특이사항")

st.markdown('</div>', unsafe_allow_html=True)

# ==========================================
# 6. 저장 로직
# ==========================================
st.markdown("---")

if st.button("💾 저장 후 다음", type="primary", use_container_width=True):
    with st.spinner("저장 중..."):
        try:
            save_data = row.to_dict()
            
            save_data.update({
                "해지사유": r,
                "불만유형": c,
                "세부 해지사유 및 불만 내용": d, # 텍스트 영역의 최종 값(d) 저장
                "해지일자": origin_date,
                "사유등록일자": rd.strftime("%Y-%m-%d"),
                "비고": rm,
                "처리일시": pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S")
            })
            
            if "해지_해지일자" in save_data: del save_data["해지_해지일자"]
            
            save_result(save_data)
            
            # [중요] 저장 완료 후 텍스트 내용 초기화
            st.session_state["current_detail"] = "" 
            
            st.toast(f"✅ 저장되었습니다! [{row.get('상호')}]", icon="💾")
            time.sleep(0.5)
            st.rerun()
            
        except Exception as e:
            st.error(f"⛔ 저장 실패: {e}")
