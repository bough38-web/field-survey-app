import streamlit as st
import pandas as pd
import altair as alt
from storage import load_targets, load_results

# st.set_page_config는 app.py에서 처리됨

st.markdown("""
<style>
    @import url("https://cdn.jsdelivr.net/gh/orioncactus/pretendard@v1.3.8/dist/web/static/pretendard.css");
    .stApp { background-color: #f8fafc; font-family: 'Pretendard', sans-serif; }
    .styled-table { width: 100%; border-collapse: collapse; margin: 25px 0; font-size: 0.95em; box-shadow: 0 0 20px rgba(0,0,0,0.05); border-radius: 10px; overflow: hidden; }
    .styled-table thead tr { background-color: #2563eb; color: #ffffff; text-align: center; }
    .styled-table th, .styled-table td { padding: 12px 15px; text-align: center; border-bottom: 1px solid #dddddd; }
    .styled-table tbody tr:nth-of-type(even) { background-color: #f8fafc; }
    .progress-bg { background-color: #e2e8f0; border-radius: 10px; width: 100px; height: 8px; margin: 0 auto; overflow: hidden; }
    .progress-fill { height: 100%; background: linear-gradient(90deg, #60a5fa 0%, #2563eb 100%); }
</style>
""", unsafe_allow_html=True)

st.title("💧 종합 현황 대시보드")

targets = load_targets()
results = load_results()
BRANCH_ORDER = ["중앙", "강북", "서대문", "고양", "의정부", "남양주", "강릉", "원주"]

if targets.empty: st.warning("데이터가 없습니다."); st.stop()

if "관리지사" in targets.columns: targets["관리지사표시"] = targets["관리지사"].str.replace("지사","").str.strip()
else: targets["관리지사표시"] = "미지정"
if "계약번호" in targets.columns: targets["계약번호"] = targets["계약번호"].astype(str).str.replace(r'\.0$', '', regex=True)

if not results.empty:
    if "관리지사" in results.columns: results["관리지사표시"] = results["관리지사"].str.replace("지사","").str.strip()
    else: results["관리지사표시"] = "미지정"
    if "계약번호" in results.columns: results["계약번호"] = results["계약번호"].astype(str).str.replace(r'\.0$', '', regex=True)

with st.sidebar:
    st.header("🔍 필터")
    all_br = [b for b in BRANCH_ORDER if b in targets["관리지사표시"].unique()] + [b for b in targets["관리지사표시"].unique() if b not in BRANCH_ORDER]
    sel_br = st.multiselect("지사 선택", all_br, default=[], placeholder="전체 (비워두면)")
    
    tmp = targets[targets["관리지사표시"].isin(sel_br)] if sel_br else targets
    owners = sorted(tmp["담당자"].dropna().unique()) if "담당자" in tmp.columns else []
    sel_own = st.multiselect("담당자 선택", owners, default=[], placeholder="전체 (비워두면)")
    if st.button("초기화"): st.rerun()

filt_tgt = targets
if sel_br: filt_tgt = filt_tgt[filt_tgt["관리지사표시"].isin(sel_br)]
if sel_own: filt_tgt = filt_tgt[filt_tgt["담당자"].isin(sel_own)]

ids = filt_tgt["계약번호"].unique()
filt_res = results[results["계약번호"].isin(ids)] if not results.empty else pd.DataFrame()

col1, col2, col3, col4 = st.columns(4)
tgt_n, res_n = len(filt_tgt), len(filt_res)
prog = (res_n/tgt_n*100) if tgt_n>0 else 0
with col1: st.metric("대상", f"{tgt_n}건")
with col2: st.metric("완료", f"{res_n}건", f"{prog:.1f}%")
with col3: st.metric("잔여", f"{tgt_n-res_n}건", delta_color="inverse")
with col4: st.metric("최다 사유", filt_res["해지사유"].mode()[0] if not filt_res.empty and "해지사유" in filt_res.columns else "-")

st.markdown("---")

bstats = filt_tgt.groupby("관리지사표시").size().reset_index(name="대상건수")
if not filt_res.empty:
    dstats = filt_res.groupby("관리지사표시").size().reset_index(name="완료건수")
    bstats = pd.merge(bstats, dstats, on="관리지사표시", how="left")
else: bstats["완료건수"] = 0
bstats = bstats.fillna(0)
bstats["진행률"] = (bstats["완료건수"]/bstats["대상건수"]*100).fillna(0)

c1 = alt.Chart(bstats).mark_bar().encode(x="관리지사표시", y="완료건수").properties(title="지사별 완료", height=300)
st.altair_chart(c1, use_container_width=True)

html = '<table class="styled-table"><thead><tr><th>지사명</th><th>대상</th><th>완료</th><th>진행률</th><th>Bar</th></tr></thead><tbody>'
for _, r in bstats.iterrows():
    rt = r['진행률']
    html += f"<tr><td>{r['관리지사표시']}</td><td>{int(r['대상건수'])}</td><td>{int(r['완료건수'])}</td><td>{rt:.1f}%</td><td><div class='progress-bg'><div class='progress-fill' style='width:{rt}%;'></div></div></td></tr>"
html += "</tbody></table>"
st.markdown(html, unsafe_allow_html=True)
