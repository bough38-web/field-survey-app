import streamlit as st

# 1. 전역 페이지 설정 (앱 실행 시 최초 1회만 설정)
st.set_page_config(page_title="현장조사 관리 시스템", layout="wide", page_icon="🏢")

# 2. 페이지 정의
# [사용자용 메뉴]
user_pages = [
    st.Page("pages/1_사유등록대상.py", title="사유 등록 및 조치", icon="📝"),
    st.Page("pages/3_현황대시보드.py", title="종합 현황 대시보드", icon="💧"),
]

# [관리자용 메뉴] - 관리자 홈 포함
admin_pages = [
    st.Page("admin_home.py", title="관리자 홈", icon="🏠"),
    st.Page("pages/0_조사대상업로드.py", title="조사 대상 업로드", icon="📤"),
    st.Page("pages/2_등록결과모니터링.py", title="등록 결과 모니터링", icon="📊"),
]

# 3. 네비게이션 그룹핑
st.sidebar.title("Navigation")
pg = st.navigation({
    "👤 사용자 모드 (User)": user_pages,
    "🔒 관리자 모드 (Admin)": admin_pages
})

# 4. 페이지 실행
pg.run()
