import streamlit as st
from storage import load_events

st.set_page_config(page_title="📋 현장 조사 · 조치 요청", layout="wide")
st.title("📋 현장 조사 · 조치 요청")

events = load_events()

if events.empty:
    st.info("현재 등록된 조사/이벤트가 없습니다.")
else:
    for _, e in events.iterrows():
        st.subheader(e["title"])
        st.caption(f"유형: {e['type']} | 마감일: {e['due_date']}")
        st.write(e["description"])
        if e.get("reference"):
            st.markdown(f"[참고 자료]({e['reference']})")
        st.divider()