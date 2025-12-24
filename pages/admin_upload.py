import streamlit as st
import pandas as pd
from io import StringIO
import os
import time
from storage import save_targets, load_targets, load_logs, normalize_columns, BACKUP_DIR, check_admin_password

# 🔒 인증 실행
check_admin_password()

st.title("📤 데이터 업로드 & 관리")

tab1, tab2, tab3 = st.tabs(["신규 업로드", "데이터 수정", "이력/백업"])

with tab1:
    st.info("파일 업로드 시 기존 데이터는 백업 후 덮어씌워집니다.")
    method = st.radio("방식", ["파일 업로드", "붙여넣기"], horizontal=True)
    df_new = None
    
    if method == "파일 업로드":
        file = st.file_uploader("Excel/CSV 파일", type=["xlsx", "csv"])
        if file:
            try: df_new = pd.read_excel(file) if file.name.endswith('.xlsx') else pd.read_csv(file)
            except Exception as e: st.error(f"Error: {e}")
    else:
        txt = st.text_area("엑셀 복사 내용 붙여넣기")
        if txt:
            try: df_new = pd.read_csv(StringIO(txt), sep="\t")
            except: st.error("형식 오류")
            
    if df_new is not None:
        df_new = normalize_columns(df_new)
        st.dataframe(df_new.head())
        if st.button("🚀 반영하기", type="primary"):
            save_targets(df_new, "New Upload")
            st.success("✅ 저장 완료")
            time.sleep(1)
            st.rerun()

with tab2:
    curr = load_targets()
    if not curr.empty:
        edt = st.data_editor(curr, num_rows="dynamic", use_container_width=True)
        if st.button("💾 수정사항 저장", type="primary"):
            save_targets(edt, "Manual Edit")
            st.success("✅ 수정 완료")
            time.sleep(1)
            st.rerun()
    else:
        st.warning("데이터가 없습니다.")

with tab3:
    st.dataframe(load_logs(), use_container_width=True, hide_index=True)
    if BACKUP_DIR.exists():
        files = sorted(list(BACKUP_DIR.glob("*.csv")), key=os.path.getmtime, reverse=True)[:5]
        for f in files:
            with open(f, "rb") as fd:
                st.download_button(f"📄 {f.name}", fd, file_name=f.name)
