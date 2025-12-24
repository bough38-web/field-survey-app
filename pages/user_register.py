import streamlit as st
import pandas as pd
import time
from datetime import date
from storage import load_targets, load_results, save_result, load_reason_map

# 스타일링
st.markdown("""
<style>
    @import url("https://cdn.jsdelivr.net/gh/orioncactus/pretendard@v1.3.8/dist/web/static/pretendard.css");
    .stApp { background-color: #f8fafc; font-family: 'Pretendard', sans-serif; }
    .info-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 12px; }
    .info-box { background: white; padding: 15px; border-radius: 12px; border: 1px solid #e2e8f0; }
    .info-label { font-size: 0.8rem; color: #64748b; }
    .info-value { font-size: 1.1rem; font-weight: 700; color: #1e293b; }
    .highlight { color: #ef4444; }
</style>
""", unsafe_allow_html=True)

st.title("📝 사유 등록 및 조치")

targets = load_targets()
results = load_results()

if targets.empty:
    st.warning("데이터가 없습니다.")
    st.stop()

# 처리 완료된 건 제외
done_ids = results[results["해지사유"].notna()]["계약번호"].unique() if not results.empty else []
pending = targets[~targets["계약번호"].isin(done_ids)]

# 진행률
with st.container():
    c1, c2 = st.columns([4, 1])
    prog = len(done_ids) / len(targets)
    with c1: st.progress(prog); st.caption(f"진행률: {prog*100:.1f}%")
    with c2: st.metric("남은 대상", len(pending))

if pending.empty:
    st.success("완료되었습니다!")
    st.stop()

# 필터
if "관리지사" in pending.columns: pending["지사"] = pending["관리지사"].str.replace("지사","").str.strip()
else: pending["지사"] = "미지정"

with st.sidebar:
    st.header("🔍 필터")
    b_sel = st.selectbox("지사", ["전체"] + sorted(pending["지사"].unique()))
    if b_sel != "전체": pending = pending[pending["지사"] == b_sel]
    if "담당자" in pending.columns:
        o_sel = st.selectbox("담당자", ["전체"] + sorted(pending["담당자"].dropna().unique()))
        if o_sel != "전체": pending = pending[pending["담당자"] == o_sel]

# 대상 선택
idx = st.selectbox("대상 선택", pending.index, format_func=lambda i: f"[{pending.loc[i,'지사']}] {pending.loc[i,'상호']} ({pending.loc[i,'계약번호']})")
row = pending.loc[idx]

# 정보 표시
st.markdown("### 🏢 고객 정보")
od = row.get("해지일자", "-")
try: od = pd.to_datetime(od).strftime("%Y-%m-%d")
except: pass

st.markdown(f"""
<div class="info-grid">
    <div class="info-box"><div class="info-label">지사</div><div class="info-value">{row.get('관리지사','-')}</div></div>
    <div class="info-box"><div class="info-label">계약번호</div><div class="info-value">{row.get('계약번호','-')}</div></div>
    <div class="info-box" style="grid-column: span 2;"><div class="info-label">상호</div><div class="info-value">{row.get('상호','-')}</div></div>
    <div class="info-box"><div class="info-label">담당자</div><div class="info-value">{row.get('담당자','-')}</div></div>
    <div class="info-box"><div class="info-label">해지일자</div><div class="info-value highlight">{od}</div></div>
</div>
""", unsafe_allow_html=True)

# 입력 폼
reason_map = load_reason_map()
if reason_map.empty: st.error("reason_map.csv 필요"); st.stop()

st.markdown("### ✍️ 입력")
with st.container(border=True):
    c1, c2 = st.columns(2)
    with c1: r = st.selectbox("해지사유", sorted(reason_map["해지사유"].unique()))
    with c2: c = st.selectbox("불만유형", reason_map[reason_map["해지사유"]==r]["불만유형"].unique())
    d = st.text_area("상세 내용", height=100)
    c3, c4 = st.columns(2)
    with c3: rd = st.date_input("등록일", value=date.today())
    with c4: rm = st.text_area("비고")

if st.button("💾 저장 후 다음", type="primary", use_container_width=True):
    with st.spinner("저장 중..."):
        try:
            data = row.to_dict()
            data.update({
                "해지사유": r, "불만유형": c, "세부 해지사유 및 불만 내용": d,
                "해지일자": od, "사유등록일자": rd.strftime("%Y-%m-%d"), "비고": rm,
                "처리일시": pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S")
            })
            save_result(data)
            st.toast("✅ 저장되었습니다!", icon="💾")
            time.sleep(0.5)
            st.rerun()
        except Exception as e:
            st.error(f"저장 실패: {e}")
