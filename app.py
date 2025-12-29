import streamlit as st

# ==========================================
# [1] 페이지 기본 설정 (앱 시작 시 1회만 호출)
# ==========================================
st.set_page_config(
    page_title="현장조사 관리 시스템", 
    layout="wide", 
    page_icon="🏢",
    initial_sidebar_state="expanded"
)

# ==========================================
# [2] 한글 폰트 및 설정 적용
# ==========================================
st.components.v1.html("""
    <script>
        window.parent.document.querySelector('html').lang = 'ko';
        const style = document.createElement('style');
        style.innerHTML = `
            @import url("https://cdn.jsdelivr.net/gh/orioncactus/pretendard@v1.3.8/dist/web/static/pretendard.css");
            body, html, .stApp { font-family: 'Pretendard', sans-serif !important; }
        `;
        window.parent.document.head.appendChild(style);
    </script>
""", height=0)

# ==========================================
# [3] 페이지 객체 정의 (변수에 담아둡니다)
# ==========================================
# 1. 사용자용 페이지
p_register = st.Page("pages/user_register.py", title="사유 등록 및 조치", icon="📝")
p_dashboard = st.Page("pages/user_dashboard.py", title="종합 현황 대시보드", icon="💧")

# 2. 관리자용 페이지
p_admin_home = st.Page("admin_home.py", title="관리자 홈", icon="🏠")
p_upload = st.Page("pages/admin_upload.py", title="조사 대상 업로드", icon="📤")
p_monitor = st.Page("pages/admin_monitor.py", title="등록 결과 모니터링", icon="📊")

# ==========================================
# [4] 네비게이션 라우팅 설정 (UI는 숨김)
# ==========================================
# position="hidden"을 주면 화면에 기본 메뉴가 안 나옵니다.
# 하지만 pg.run()을 위해 등록은 해야 합니다.
all_pages = [p_register, p_dashboard, p_admin_home, p_upload, p_monitor]
pg = st.navigation(all_pages, position="hidden")

# ==========================================
# [5] 커스텀 사이드바 메뉴 구성 (접이식 구현)
# ==========================================
with st.sidebar:
    st.title("Navigation")
    st.markdown("---")

    # 1. 사용자 모드 (기본 펼침: expanded=True)
    with st.expander("👤 사용자 모드 (User)", expanded=True):
        st.page_link(p_register)
        st.page_link(p_dashboard)

    # 2. 관리자 모드 (기본 접힘: expanded=False) 👈 여기가 핵심입니다!
    with st.expander("🔒 관리자 모드 (Admin)", expanded=False):
        st.page_link(p_admin_home)
        st.page_link(p_upload)
        st.page_link(p_monitor)

# ==========================================
# [6] 앱 실행
# ==========================================
pg.run()
