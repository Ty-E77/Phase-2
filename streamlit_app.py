
import streamlit as st
from typing import Any

from enrollment_starter import EnrollmentDatabase, EnrollmentService, CURRENT_STUDENT

# Initialize DB and service (UI layer calls only service methods)
_db = EnrollmentDatabase()
_service = EnrollmentService(_db, CURRENT_STUDENT)

# Page config
st.set_page_config(page_title="Student Dashboard", layout="wide")

# Simple CSS to make compact cards
st.markdown(
    """
    <style>
    .card {padding:12px; border-radius:8px; background:#0f1720; box-shadow:0 2px 6px rgba(0,0,0,0.5); margin-bottom:12px}
    .card h4{margin:0}
    .muted{color:#9ca3af}
    </style>
    """,
    unsafe_allow_html=True,
)

# Session state defaults
if "page" not in st.session_state:
    st.session_state.page = "dashboard"
if "selected_class" not in st.session_state:
    st.session_state.selected_class = None
if "message" not in st.session_state:
    st.session_state.message = None
if "message_type" not in st.session_state:
    st.session_state.message_type = None


def show_message():
    msg = st.session_state.get("message")
    mtype = st.session_state.get("message_type")
    if not msg:
        return
    if mtype == "success":
        st.success(msg)
    elif mtype == "warning":
        st.warning(msg)
    else:
        st.error(msg)
    # clear after showing
    st.session_state.message = None
    st.session_state.message_type = None


def go_to_dashboard(msg: str | None = None, mtype: str | None = None):
    st.session_state.page = "dashboard"
    st.session_state.selected_class = None
    st.session_state.message = msg
    st.session_state.message_type = mtype



def go_to_class(selected: dict[str, Any]):
    st.session_state.selected_class = selected
    st.session_state.page = "class"



def dashboard_view():
    # Header with name and metrics
    left, right = st.columns([3, 1])
    with left:
        st.markdown("# Student Dashboard")
        st.markdown(f"### {CURRENT_STUDENT['name']} — {CURRENT_STUDENT['user_id']}")
    with right:
        summary = _service.get_student_summary(CURRENT_STUDENT["user_id"])  # service call
        st.metric("Total", summary.get("total_records", 0))
        st.metric("Enrolled", summary.get("enrolled", 0))

    show_message()

    st.write("---")

    # Two-column layout: left = enrolled + enroll form, right = available keys
    left_col, right_col = st.columns([2, 1])

    with left_col:
        st.subheader("Enrolled Classes")
        enrolled = _service.get_enrolled_classes(CURRENT_STUDENT["user_id"])  # service call
        if not enrolled:
            st.info("No enrolled classes.")
        else:
            for rec in enrolled:
                st.markdown(f"<div class='card'>", unsafe_allow_html=True)
                st.markdown(f"### {rec['course_id']} — {rec['course_name']}")
                st.markdown(f"<div class='muted'>Instructor: {rec['instructor']} &nbsp;·&nbsp; Enrolled at: {rec.get('enrolled_at')}</div>", unsafe_allow_html=True)
                r1, r2 = st.columns([6, 1])
                if r2.button("Open", key=f"open-{rec['course_id']}"):
                    go_to_class(rec)
                # confirmation via expander
                with r1.expander("Actions"):
                    st.write("If you unenroll, your record will be marked as `unenrolled`.")
                    if st.button("Confirm Unenroll", key=f"confirm-unenroll-{rec['course_id']}"):
                        ok = _service.soft_unenroll_student(CURRENT_STUDENT["user_id"], rec["course_id"])
                        if ok:
                            st.session_state.message = f"Unenrolled from {rec['course_id']}"
                            st.session_state.message_type = "success"
                        else:
                            st.session_state.message = f"Could not unenroll from {rec['course_id']}"
                            st.session_state.message_type = "error"
                st.markdown("</div>", unsafe_allow_html=True)

        st.write("---")
        st.subheader("Enroll with Key")
        with st.form(key="enroll_form", clear_on_submit=True):
            key_input = st.text_input("Enrollment key", placeholder="e.g. DATA210-SPRING")
            submitted = st.form_submit_button("Enroll")
            if submitted:
                result = _service.enroll_with_key(CURRENT_STUDENT["user_id"], CURRENT_STUDENT["email"], key_input)
                if result:
                    st.session_state.message = f"Enrolled in {result['course_id']}"
                    st.session_state.message_type = "success"
                else:
                    st.session_state.message = "Enrollment failed. Check key and try again."
                    st.session_state.message_type = "error"

    with right_col:
        st.subheader("Available Course Keys")
        keys = _service.get_available_course_keys()
        if not keys:
            st.info("No course keys available.")
        else:
            for k in keys:
                st.markdown(f"**{k['course_id']}** — {k['course_name']}")
                st.markdown(f"`{k['enrollment_key']}`")
                st.write("---")


def class_view():
    selected = st.session_state.get("selected_class")
    if not selected:
        go_to_dashboard()
        return

    st.title(f"Class: {selected['course_id']} - {selected['course_name']}")
    show_message()

    st.write(f"Instructor: {selected['instructor']}")
    st.write(f"Status: {selected.get('status')}")
    st.write(f"Enrolled at: {selected.get('enrolled_at')}")

    col1, col2 = st.columns(2)
    if col1.button("Soft Unenroll"):
        ok = _service.soft_unenroll_student(CURRENT_STUDENT["user_id"], selected["course_id"])
        if ok:
            st.session_state.message = f"You have been unenrolled from {selected['course_id']}"
            st.session_state.message_type = "success"
        else:
            st.session_state.message = f"Unable to unenroll from {selected['course_id']}"
            st.session_state.message_type = "error"
        go_to_dashboard()

    if col2.button("Back to Dashboard"):
        go_to_dashboard()


# Router
if st.session_state.page == "dashboard":
    dashboard_view()
else:
    class_view()
