import streamlit as st
import pandas as pd
from storage import load_results

st.set_page_config(page_title="등록 결과 모니터링", layout="wide")
st.title("📊 등록 결과 모니터링")

# ==========================================
# 1. 데이터 로드 및 오류 방지 (핵심 수정)
# ==========================================
results = load_results()

# [수정] 데이터가 아예 없는 경우 안내 문구 표시 후 중단
if results.empty:
    st.info("📭 아직 등록된 조치 결과가 없습니다. '사유 등록 대상' 메뉴에서 조치를 입력해주세요.")
    st.stop()

# [수정] '계약번호' 컬럼이 존재할 때만 문자열 변환 수행 (KeyError 방지)
if "계약번호" in results.columns:
    results["계약번호"] = results["계약번호"].astype(str)

# ==========================================
# 2. 현황 요약 (Metrics)
# ==========================================
col1, col2, col3 = st.columns(3)

total_count = len(results)

# 지사별 최다 등록 지사 확인
if "관리지사" in results.columns:
    top_branch = results["관리지사"].value_counts().idxmax()
else:
    top_branch = "-"

# 최근 등록일 확인
if "처리일시" in results.columns:
    last_update = pd.to_datetime(results["처리일시"]).max().strftime("%Y-%m-%d %H:%M")
else:
    last_update = "-"

with col1:
    st.metric("총 등록 건수", f"{total_count}건")
with col2:
    st.metric("최다 등록 지사", top_branch)
with col3:
    st.metric("최근 업데이트", last_update)

st.markdown("---")

# ==========================================
# 3. 데이터 필터링 및 조회
# ==========================================
st.subheader("📋 등록 내역 상세")

# 검색 기능 (계약번호 또는 상호)
search_query = st.text_input("🔍 검색 (계약번호 또는 상호)", placeholder="검색어를 입력하세요...")

if search_query:
    # 문자열로 변환 후 검색
    mask = (
        results["계약번호"].astype(str).str.contains(search_query) | 
        results["상호"].astype(str).str.contains(search_query)
    )
    filtered_df = results[mask]
else:
    filtered_df = results

# 필터링된 결과 보여주기
st.dataframe(
    filtered_df, 
    use_container_width=True,
    hide_index=True
)

# ==========================================
# 4. 다운로드 기능
# ==========================================
csv = filtered_df.to_csv(index=False).encode('utf-8-sig') # 한글 깨짐 방지 인코딩

st.download_button(
    label="📥 조회 결과 다운로드 (CSV)",
    data=csv,
    file_name="survey_results.csv",
    mime="text/csv",
    type="primary"
)
