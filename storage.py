import streamlit as st
import pandas as pd
from io import StringIO
import os
# [중요] storage.py에서 정의한 함수들을 가져옵니다.
from storage import save_targets, load_targets, load_logs, normalize_columns, BACKUP_DIR

# ==========================================
# 1. 페이지 설정 및 스타일링
# ==========================================
st.set_page_config(page_title="데이터 관리 센터", layout="wide", page_icon="💾")

st.markdown("""
<style>
    @import url("https://cdn.jsdelivr.net/gh/orioncactus/pretendard@v1.3.8/dist/web/static/pretendard.css");
    .stApp { background-color: #f8fafc; font-family: 'Pretendard', sans-serif; }
    
    /* 탭 스타일 */
    .stTabs [data-baseweb="tab-list"] { gap: 8px; }
    .stTabs [data-baseweb="tab"] {
        height: 50px; white-space: pre-wrap; background-color: #ffffff;
        border-radius: 8px 8px 0 0; box-shadow: 0 -1px 2px rgba(0,0,0,0.05);
        font-weight: 600; color: #64748b;
    }
    .stTabs [aria-selected="true"] {
        background-color: #ffffff; color: #2563eb; border-top: 3px solid #2563eb;
    }
    
    /* 카드 디자인 */
    .card-box {
        background-color: white; padding: 20px; border-radius: 12px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05); border: 1px solid #e2e8f0;
    }
    h1, h2, h3 { color: #1e293b; }
</style>
""", unsafe_allow_html=True)

st.title("💾 데이터 관리 센터")
st.markdown("조사 대상 데이터를 **업로드**, **수정**, **백업** 관리하는 통합 페이지입니다.")

# ==========================================
# 2. 탭 구성
# ==========================================
tab1, tab2, tab3 = st.tabs(["📤 신규 업로드", "✏️ 데이터 수정 (Editor)", "🕰️ 이력 및 백업"])

# ------------------------------------------
# [Tab 1] 신규 업로드
# ------------------------------------------
with tab1:
    st.markdown("### 📤 새로운 조사 대상 업로드")
    st.info("새 파일을 업로드하면 기존 데이터는 자동으로 **백업**된 후 덮어씌워집니다.")
    
    method = st.radio("데이터 입력 방식", ["파일 업로드 (Excel/CSV)", "엑셀 복사 붙여넣기"], horizontal=True)
    
    df_new = None
    
    if method == "파일 업로드 (Excel/CSV)":
        file = st.file_uploader("파일을 드래그하여 놓으세요", type=["xlsx", "csv"])
        if file:
            try:
                df_new = pd.read_excel(file) if file.name.endswith(".xlsx") else pd.read_csv(file)
            except Exception as e:
                st.error(f"파일을 읽는 중 오류가 발생했습니다: {e}")

    else:
        pasted = st.text_area("엑셀 데이터를 복사해서 붙여넣으세요", height=200, placeholder="ContractID   CustomerName ...")
        if pasted.strip():
            try:
                df_new = pd.read_csv(StringIO(pasted), sep="\t")
            except:
                st.error("데이터 형식을 확인해주세요.")

    if df_new is not None:
        df_new = normalize_columns(df_new)
        st.write("▼ 업로드 데이터 미리보기 (상위 5건)")
        st.dataframe(df_new.head(), use_container_width=True)
        
        if st.button("🚀 데이터 반영하기", type="primary"):
            save_targets(df_new, action_type="New Upload")
            st.success(f"✅ 총 {len(df_new)}건이 성공적으로 반영되었습니다. (자동 백업 완료)")
            time.sleep(1) # 잠시 대기
            st.rerun()

# ------------------------------------------
# [Tab 2] 데이터 수정 (Editor)
# ------------------------------------------
with tab2:
    st.markdown("### ✏️ 현재 데이터 직접 수정")
    
    current_df = load_targets()
    
    if current_df.empty:
        st.warning("현재 저장된 데이터가 없습니다. 먼저 업로드해주세요.")
    else:
        st.caption(f"현재 총 데이터: {len(current_df)}건 | 셀을 더블 클릭하여 수정하세요.")
        
        # 데이터 에디터 (수정 가능)
        edited_df = st.data_editor(
            current_df,
            num_rows="dynamic", # 행 추가/삭제 가능
            use_container_width=True,
            key="data_editor"
        )
        
        col_edit1, col_edit2 = st.columns([1, 4])
        with col_edit1:
            if st.button("💾 수정사항 저장", type="primary", use_container_width=True):
                # 변경사항 저장 로직
                save_targets(edited_df, action_type="Manual Edit")
                st.success("✅ 수정사항이 저장되었습니다.")
                time.sleep(1)
                st.rerun()

# ------------------------------------------
# [Tab 3] 이력 및 백업 (Logs)
# ------------------------------------------
with tab3:
    c1, c2 = st.columns(2)
    
    # 1. 활동 로그
    with c1:
        st.markdown("### 📜 활동 로그 (Recent Activity)")
        logs = load_logs()
        if not logs.empty:
            st.dataframe(logs, use_container_width=True, hide_index=True)
        else:
            st.info("아직 기록된 활동이 없습니다.")

    # 2. 백업 파일 관리
    with c2:
        st.markdown("### 📦 백업 파일 목록")
        
        if BACKUP_DIR.exists():
            files = sorted(list(BACKUP_DIR.glob("*.csv")), key=os.path.getmtime, reverse=True)
            
            if files:
                for f in files[:10]: # 최신 10개만 표시
                    col_f1, col_f2 = st.columns([3, 1])
                    file_size = f.stat().st_size / 1024 # KB 단위
                    
                    with col_f1:
                        st.text(f"📄 {f.name} ({file_size:.1f} KB)")
                    with col_f2:
                        # 다운로드 버튼
                        with open(f, "rb") as file_data:
                            st.download_button(
                                label="다운로드",
                                data=file_data,
                                file_name=f.name,
                                mime="text/csv",
                                key=f.name
                            )
            else:
                st.info("백업 파일이 없습니다.")
        else:
            st.info("백업 폴더가 생성되지 않았습니다.")
