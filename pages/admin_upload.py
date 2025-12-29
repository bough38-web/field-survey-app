import streamlit as st
import pandas as pd
from io import StringIO
import os
import time

# storage.py가 상위 폴더가 아닌 같은 pages 폴더에 있다면 import 경로 주의 필요
# 보통 pages 폴더 안에 있는 파일에서 상위 모듈을 불러올 때는 sys.path 설정이 필요할 수 있으나,
# 같은 폴더에 storage.py를 두셨거나, 프로젝트 루트에 두셨다면 아래와 같이 사용합니다.
# (만약 에러나면 storage.py 위치를 확인해야 합니다)
from storage import save_targets, load_targets, load_logs, normalize_columns, BACKUP_DIR, check_admin_password

# [수정됨] set_page_config 삭제 (app.py에서 이미 설정했으므로 중복 실행 방지)

# 🔒 인증 실행 (관리자 페이지이므로 필수)
check_admin_password()

st.title("📤 조사 대상 업로드")

# 탭 구성
tab1, tab2, tab3 = st.tabs(["🆕 신규 업로드 (덮어쓰기)", "✏️ 데이터 수정", "📜 이력 및 백업"])

# -------------------------------------------------------------------------
# Tab 1: 신규 업로드 (기존 데이터 덮어쓰기 모드)
# -------------------------------------------------------------------------
with tab1:
    st.markdown("### ⚠️ 데이터 전체 교체 모드")
    st.warning(
        """
        **주의:** 이 기능은 **기존에 등록된 모든 데이터를 삭제**하고, 
        새로 업로드하는 파일로 **완전히 교체(Overwrite)** 합니다.
        (이전 데이터는 자동으로 백업 폴더에 저장됩니다.)
        """
    )

    method = st.radio("업로드 방식 선택", ["파일 업로드 (Excel/CSV)", "엑셀 붙여넣기"], horizontal=True)
    df_new = None
    
    if "파일" in method:
        file = st.file_uploader("파일을 드래그하거나 선택하세요", type=["xlsx", "csv"])
        if file:
            try:
                if file.name.endswith('.xlsx'):
                    df_new = pd.read_excel(file)
                else:
                    df_new = pd.read_csv(file)
            except Exception as e:
                st.error(f"❌ 파일 읽기 실패: {e}")
    else:
        txt = st.text_area("엑셀 데이터를 복사(Ctrl+C) 후 붙여넣기(Ctrl+V) 하세요.", height=150)
        if txt:
            try:
                df_new = pd.read_csv(StringIO(txt), sep="\t")
            except Exception as e:
                st.error(f"❌ 데이터 파싱 실패: {e}")

    if df_new is not None:
        df_new = normalize_columns(df_new)
        curr_data = load_targets()
        curr_count = len(curr_data) if not curr_data.empty else 0
        new_count = len(df_new)
        
        st.divider()
        col1, col2, col3 = st.columns(3)
        col1.metric("현재 데이터 건수", f"{curr_count:,} 건", delta="삭제 예정", delta_color="inverse")
        col2.metric("신규 데이터 건수", f"{new_count:,} 건", delta="교체 예정", delta_color="normal")
        
        with st.expander("🔍 업로드 데이터 미리보기", expanded=True):
            st.dataframe(df_new.head(), use_container_width=True)

        st.write("")
        confirm_overwrite = st.checkbox("🚨 기존 데이터를 모두 삭제하고 교체함에 동의합니다.", value=False)
        
        if st.button("🚀 전체 덮어쓰기 실행", type="primary", disabled=not confirm_overwrite):
            with st.spinner("데이터 교체 및 백업 중..."):
                save_targets(df_new, "Full Overwrite Upload")
                time.sleep(1)
                st.toast("✅ 데이터가 성공적으로 교체되었습니다!", icon="🎉")
                time.sleep(1)
                st.rerun()

# -------------------------------------------------------------------------
# Tab 2: 데이터 수정
# -------------------------------------------------------------------------
with tab2:
    st.info("💡 등록된 데이터를 직접 수정하거나 행을 삭제할 수 있습니다.")
    curr = load_targets()
    
    if not curr.empty:
        edt = st.data_editor(curr, num_rows="dynamic", use_container_width=True, key="editor_tab2")
        if st.button("💾 수정사항 저장", type="primary"):
            save_targets(edt, "Manual Edit")
            st.success("✅ 수정 완료")
            time.sleep(1)
            st.rerun()
    else:
        st.warning("데이터가 없습니다.")

# -------------------------------------------------------------------------
# Tab 3: 이력 및 백업
# -------------------------------------------------------------------------
with tab3:
    st.markdown("### 📋 작업 로그")
    st.dataframe(load_logs(), use_container_width=True, hide_index=True)
    
    st.divider()
    st.markdown("### 📦 백업 파일 다운로드")
    if BACKUP_DIR.exists():
        files = sorted(list(BACKUP_DIR.glob("*.csv")), key=os.path.getmtime, reverse=True)[:5]
        for f in files:
            col_d1, col_d2 = st.columns([4, 1])
            with col_d1:
                st.text(f"📄 {f.name}")
            with col_d2:
                with open(f, "rb") as fd:
                    st.download_button("다운로드", fd, file_name=f.name, key=f.name)
