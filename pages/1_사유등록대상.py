import streamlit as st
import pandas as pd
import time
from datetime import date
from storage import load_targets, load_results, save_result, load_reason_map

# st.set_page_config는 app.py에서 처리됨

st.markdown("""
<style>
    @import url("https://cdn.jsdelivr.net/gh/orioncactus/pretendard@v1.3.8/dist/web/static/pretendard.css");
    .stApp { background-color: #f8fafc; font-family: 'Pretendard', sans-serif; }
    .stContainer { background-color: #ffffff; border-radius: 16px; padding: 24px; box-shadow: 0 4px 20px rgba(0,0,0,0.03); border: 1px solid #f1f5f9; margin-bottom: 20px; }
    .info-box { background-color: #f8fafc; padding: 15px; border-radius: 12px; border: 1px solid #e2e8f0; text-align: center; }
    .info-label { font-size: 0.85rem; color: #64748b; margin-bottom: 5px; }
    .info-value { font-size: 1.15rem; font-weight: 700; color: #0f172a; }
    .highlight-value { font-size: 1.15rem; font-weight: 800; color: #ef4444; }
</style>
""", unsafe_allow_html=True)

st.title("📝 사유 등록 및 조치")

targets = load_targets()
results = load_results()

if targets.empty:
    st.warning("데이터가 없습니다. 관리자에게 문의하세요.")
    st.stop()

if "계약번호" in targets.columns:
    targets["계약번호"] = targets["계약번호"].astype(str).str.replace(r'\.0$', '', regex=True)
if not results.empty and "계약번호" in results.columns:
    results["계약번호"] = results["계약번호"].astype(str).str.replace(r'\.0$', '', regex=True)
    registered_contracts = results[results["해지사유"].notna()]["계약번호"].unique()
else:
    registered_contracts = []

pending = targets[~targets["계약번호"].isin(registered_contracts)]

total_cnt = len(targets)
done_cnt = len(registered_contracts)
pending_cnt = len(pending)
progress = done_cnt / total_cnt if total_cnt > 0 else 0

with st.container():
    c1, c2, c3 = st.columns([1, 4, 1])
    with c1: st.metric("남은 대상", f"{pending_cnt}건")
    with c2: st.markdown(f"**진행률** ({done_cnt}/{total_cnt})"); st.progress(progress)
    with c3: st.metric("완료", f"{done_cnt}건")

if pending.empty:
    st.success("모든 대상 처리가 완료되었습니다!")
    st.stop()

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

idx = st.selectbox("작업 대상 선택", pending.index, format_func=lambda i: f"[{pending.loc[i, '관리지사표시']}] {pending.loc[i, '상호']} ({pending.loc[i, '계약번호']})")
row = pending.loc[idx]

st.markdown("### 🏢 고객 정보")
origin_date = row.get("해지일자", "-")
try: origin_date = pd.to_datetime(origin_date).strftime("%Y-%m-%d")
except: pass

cols = st.columns(5)
infos = [("관리지사", row.get('관리지사','-')), ("계약번호", row.get('계약번호','-')), ("상호", row.get('상호','-')), ("담당자", row.get('담당자','-')), ("원본 해지일자", origin_date)]
for i, (l, v) in enumerate(infos):
    cls = "highlight-value" if l == "원본 해지일자" else "info-value"
    cols[i].markdown(f"<div class='info-box'><div class='info-label'>{l}</div><div class='{cls}'>{v}</div></div>", unsafe_allow_html=True)

reason_map = load_reason_map()
if reason_map.empty: st.error("reason_map.csv 없음"); st.stop()

st.markdown("### ✍️ 조치 내용")
with st.container():
    c1, c2 = st.columns(2)
    with c1: r = st.selectbox("해지 사유", sorted(reason_map["해지사유"].unique()))
    with c2: c = st.selectbox("불만 유형", reason_map[reason_map["해지사유"]==r]["불만유형"].unique())
    
    d = st.text_area("상세 내용", height=100)
    c3, c4 = st.columns(2)
    with c3: rd = st.date_input("사유 등록 일자", value=date.today())
    with c4: rm = st.text_area("비고", height=70)

st.markdown("---")
if st.button("💾 저장 후 다음 (Save & Next)", type="primary", use_container_width=True):
    data = {
        "관리지사": row.get("관리지사",""), "계약번호": row.get("계약번호",""), "상호": row.get("상호",""), "담당자": row.get("담당자",""),
        "해지사유": r, "불만유형": c, "세부 해지사유 및 불만 내용": d,
        "해지_해지일자": row.get("해지일자",""), "사유등록일자": rd.strftime("%Y-%m-%d"), "비고": rm,
        "처리일시": pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    save_result(data)
    
    # 팝업 알림 (Toast) 및 리로드
    st.toast(f"✅ 저장되었습니다. [{row.get('상호')}]", icon="💾")
    time.sleep(0.7)
    st.rerun()
