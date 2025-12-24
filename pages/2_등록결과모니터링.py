import streamlit as st
import pandas as pd
from datetime import date
from storage import load_targets, load_results

st.set_page_config(page_title="등록결과 모니터링", layout="wide")
st.title("📊 등록결과 모니터링")

BRANCH_ORDER = ["중앙", "강북", "서대문", "고양", "의정부", "남양주", "강릉", "원주"]

targets = load_targets()
results = load_results()

targets["계약번호"] = targets["계약번호"].astype(str)
results["계약번호"] = results["계약번호"].astype(str)

targets["관리지사표시"] = targets["관리지사"].str.replace("지사","").str.strip()
results["관리지사표시"] = results["관리지사"].str.replace("지사","").str.strip()

registered = results[results["해지사유"].notna()]

# =========================
# KPI
# =========================
total = targets["계약번호"].nunique()
done = registered["계약번호"].nunique()
remain = total - done
rate = round(done / total * 100, 1) if total else 0

today = date.today().strftime("%Y-%m-%d")
today_cnt = (registered["해지_해지일자"] == today).sum()

c1,c2,c3,c4,c5 = st.columns(5)
c1.metric("대상", total)
c2.metric("등록", done)
c3.metric("미등록", remain)
c4.metric("등록율", f"{rate}%")
c5.metric("오늘 등록", today_cnt)

# =========================
# 지사별 현황
# =========================
st.subheader("🏢 지사별 대상 vs 등록")

branch_target = targets.groupby("관리지사표시")["계약번호"].nunique().reindex(BRANCH_ORDER, fill_value=0)
branch_done = registered.groupby("관리지사표시")["계약번호"].nunique().reindex(BRANCH_ORDER, fill_value=0)

summary = pd.DataFrame({
    "대상건수": branch_target,
    "등록건수": branch_done
})
summary["등록율(%)"] = (summary["등록건수"] / summary["대상건수"] * 100).round(1)

st.bar_chart(summary[["대상건수","등록건수"]])
st.dataframe(summary.reset_index(), use_container_width=True)

# =========================
# 담당자 미등록
# =========================
st.subheader("👤 담당자별 미등록 건수")

unreg = targets[~targets["계약번호"].isin(registered["계약번호"])]
owner_unreg = unreg.groupby("담당자")["계약번호"].count().sort_values(ascending=False)

st.bar_chart(owner_unreg)

# =========================
# 관리자
# =========================
st.divider()
pw = st.text_input("관리자 비밀번호", type="password")

if pw == "3867":
    st.subheader("🟢 등록 완료 대상 (수정 가능)")
    edited = st.data_editor(
        registered.fillna("").drop(columns=["관리지사표시"], errors="ignore"),
        use_container_width=True
    )
    if st.button("저장"):
        edited.to_csv("storage/survey_results.csv", index=False)
        st.success("저장 완료")
