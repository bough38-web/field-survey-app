import streamlit as st

# [중요] 앱 전체 설정 (여기서만 실행)
st.set_page_config(page_title="현장조사 관리 시스템", layout="wide", page_icon="🏢")

# --- 페이지 정의 ---
# 1. 사용자용 페이지 (로그인 불필요)
user_pages = [
    st.Page("pages/user_register.py", title="사유 등록 및 조치", icon="📝"),
    st.Page("pages/user_dashboard.py", title="종합 현황 대시보드", icon="💧"),
]

# 2. 관리자용 페이지 (로그인 필요 - 각 파일 내부에서 체크)
admin_pages = [
    st.Page("admin_home.py", title="관리자 홈", icon="🏠"),
    st.Page("pages/admin_upload.py", title="조사 대상 업로드", icon="📤"),
    st.Page("pages/admin_monitor.py", title="등록 결과 모니터링", icon="📊"),
]

# --- 네비게이션 그룹핑 ---
st.sidebar.title("Navigation")

# 그룹으로 묶기
pg = st.navigation({
    "👤 사용자 모드 (User)": user_pages,
    "🔒 관리자 모드 (Admin)": admin_pages
})

# 페이지 실행
pg.run()
