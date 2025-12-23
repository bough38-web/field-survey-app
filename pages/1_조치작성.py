import streamlit as st
from storage import load_events, save_action
from datetime import datetime

st.title("✍️ 조치 내역 작성")

events = load_events()
event_ids = events["event_id"].tolist() if not events.empty else []

event_id = st.selectbox("이벤트 선택", event_ids)
dept = st.text_input("부서")
name = st.text_input("담당자")
status = st.selectbox("조치 상태", ["완료", "진행중", "해당없음"])
comment = st.text_area("조치 내용")

if st.button("제출"):
    save_action({
        "event_id": event_id,
        "department": dept,
        "owner": name,
        "status": status,
        "comment": comment,
        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M")
    })
    st.success("조치 내역이 저장되었습니다.")