import streamlit as st

# ==========================================
# [1] 페이지 기본 설정 (앱에서 가장 먼저 실행되어야 함 / 1회만 호출)
# ==========================================
st.set_page_config(
    page_title="현장조사 관리 시스템", 
    layout="wide", 
    page_icon="🏢",
    initial_sidebar_state="expanded"
)

# ==========================================
# [2] 한글 폰트(Pretendard) 및 브라우저 언어(ko) 강제 적용
# ==========================================
st.components.v1.html("""
    <script>
        // 1. HTML lang 속성 변경 (브라우저 번역 방지)
        window.parent.document.querySelector('html').lang = 'ko';
        
        // 2. 폰트 강제 적용 (Pretendard)
        const style = document.createElement('style');
        style.innerHTML = `
            @import url("https://cdn.jsdelivr.net/gh/orioncactus/pretendard@v1.3.8/dist/web/static/pretendard.css");
            body, html, .stApp {
                font-family: 'Pretendard', sans-serif !important;
            }
        `;
        window.parent.document.head.appendChild(style);
    </script>
""", height=0)

# ==========================================
# [3] 페이지 정의 (Streamlit 1.31+ st.navigation 사용)
# ==========================================

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

# ==========================================
# [4] 네비게이션 그룹핑 및 실행
# ==========================================
st.sidebar.title("Navigation")

# 그룹으로 묶기
pg = st.navigation({
    "👤 사용자 모드 (User)": user_pages,
    "🔒 관리자 모드 (Admin)": admin_pages
})

# 페이지 실행
pg.run()
