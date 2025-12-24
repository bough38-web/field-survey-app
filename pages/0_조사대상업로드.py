import streamlit as st
import pandas as pd
from io import StringIO
import os
import time
from storage import save_targets, load_targets, load_logs, normalize_columns, BACKUP_DIR, check_admin_password

# 🔒 관리자 인증
check_admin_password()

st.title("💾 데이터 관리 센터")
st.markdown("조사 대상 데이터를 **업로드**, **수정**, **백업** 관리하는 통합 페이지입니다.")

tab1, tab2, tab3 = st.tabs(["📤 신규 업로드", "✏️ 데이터 수정 (Editor)", "🕰️ 이력 및 백업"])

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
                st.error(f"오류: {e}")
    else:
        pasted = st.text_area("엑셀 데이터 붙여넣기", height=200, placeholder="ContractID...")
        if pasted.strip():
            try:
                df_new = pd.read_csv(StringIO(pasted), sep="\t")
            except:
                st.error("형식 오류")

    if df_new is not None:
        df_new = normalize_columns(df_new)
        st.dataframe(df_new.head(), use_container_width=True)
        if st.button("🚀 데이터 반영하기", type="primary"):
            save_targets(df_new, action_type="New Upload")
            st.success(f"✅ 총 {len(df_new)}건 반영 완료.")
            time.sleep(1)
            st.rerun()

with tab2:
    st.markdown("### ✏️ 현재 데이터 수정")
    current_df = load_targets()
    if not current_df.empty:
        edited_df = st.data_editor(current_df, num_rows="dynamic", use_container_width=True, key="data_editor")
        if st.button("💾 수정사항 저장", type="primary"):
            save_targets(edited_df, action_type="Manual Edit")
            st.success("✅ 저장되었습니다.")
            time.sleep(1)
            st.rerun()
    else:
        st.warning("데이터가 없습니다.")

with tab3:
    c1, c2 = st.columns(2)
    with c1:
        st.markdown("### 📜 활동 로그")
        st.dataframe(load_logs(), use_container_width=True, hide_index=True)
    with c2:
        st.markdown("### 📦 백업 파일")
        if BACKUP_DIR.exists():
            files = sorted(list(BACKUP_DIR.glob("*.csv")), key=os.path.getmtime, reverse=True)
            for f in files[:10]:
                with open(f, "rb") as fd:
                    st.download_button(f"📄 {f.name}", fd, file_name=f.name)
