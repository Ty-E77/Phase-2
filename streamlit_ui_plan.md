# Streamlit UI Plan

## Overview
This document records the approved Streamlit UI plan for the student-facing enrollment app. The UI will be a thin layer that calls the Session 1 backend (`enrollment_starter.py`) service layer only. Do not modify or duplicate database SQL in the UI.

## App goal and user assumptions
- Build a student-facing enrollment app for the seeded/current student (Maya Patel).
- Assume the student is already logged in; do NOT implement authentication, registration, or password handling.
- Focus: viewing current enrollments, enrolling via a course key, soft-unenrolling (status update), and inspecting available course keys.

## Backend (Session 1) contract
The UI must not access SQLite directly. All persistence and business rules are in the backend. The UI will call only the `EnrollmentService` API exposed by `enrollment_starter.py`.

Required service methods the UI will use (assume these exist):
- `get_available_course_keys() -> list[dict]`
- `get_enrolled_classes(user_id: str) -> list[dict]`
- `get_student_summary(user_id: str) -> dict` (counts)
- `get_student_course_record(user_id: str, course_id: str) -> dict | None`
- `enroll_with_key(user_id: str, email: str, enrollment_key: str) -> dict | None`
- `soft_unenroll_student(user_id: str, course_id: str) -> bool`

If small, read-only wrappers are necessary they should live in the service layer, not in the UI.

## Routing and ephemeral state
Use `st.session_state` for routing and UI state. Keys and values:
- `page`: string, either `"dashboard"` (default) or `"class"`.
- `selected_class`: dict representing the selected enrollment/class row, or `None`.
- `message`: feedback string to show after actions.
- `message_type`: one of `"success"`, `"warning"`, or `"error"` to control message style.

Routing behavior: change `st.session_state` values and let Streamlit re-run; do not call private/experimental APIs.

## Pages

### Dashboard (default)
- Header: student name and id (use `CURRENT_STUDENT` from the backend).
- Metrics: show `total_records`, `enrolled`, and `unenrolled` using `st.metric`.
- Enrolled classes: display enrolled classes as compact cards. Each card shows:
  - `course_id`, `course_name`, `instructor`, `enrolled_at`, `status`.
  - Buttons: `Open` (set `selected_class` + `page='class'`) and `Unenroll` (confirmation UI, calls `soft_unenroll_student`).
  - Soft-unenroll must call the service method and only update status (no row deletion). On success set `message`/`message_type` and return to dashboard view.
- Enrollment form: a `st.form` with a single `Enrollment key` input and submit button. On submit call `enroll_with_key(user_id, email, key)`.
  - On success set `message='Enrolled in {course_id}'` and `message_type='success'` and show updated dashboard.
  - On failure set `message` and `message_type='error'`.
- Available course keys: informational table or list showing `course_id`, `course_name`, `enrollment_key`.

### Selected Class page
- Show full class details for `selected_class`.
- Provide a visible message area (reads `message`/`message_type`).
- Actions:
  - `Soft Unenroll` with confirmation step (expander or modal equivalent). Calls `soft_unenroll_student`. On success show success message and return to dashboard.
  - `Back to Dashboard` (set `page='dashboard'`).

## UI behavior and UX constraints
- Do not duplicate backend validation or summary counting in the UI.
- Use `st.set_page_config(layout='wide')`.
- Use a compact card style (CSS injected via `unsafe_allow_html=True` only for styling).
- Use `st.form` for the enrollment input and clear form on submit.
- Feedback messages must be clear: success (`st.success`), warning (`st.warning`), error (`st.error`).
- After any action (enroll or unenroll), the dashboard should reflect updated data from the service layer.

## Visual polish (non-functional)
- Two-column main layout on the dashboard: left = enrolled classes + enrollment form, right = available keys and summary/metrics.
- Use `st.metric` for key counts.
- Cards should be compact, readable, and include an `Actions` expander for confirmation workflows.

## Accessibility and clarity
- Buttons should have clear labels (e.g., `Confirm Unenroll`).
- Enrollment key input should have placeholder text and be trimmed/normalized in the service layer.
- Provide inline notes explaining that unenroll is a soft-unenroll.

## Constraints and forbidden changes
- Do not write SQL or open the DB from the UI.
- Do not add authentication or other unrelated features.
- Keep soft-unenroll as a status update in the backend.

## Testing & run steps (developer)
- Local run: `streamlit run streamlit_app.py`.
- Manual test checklist:
  - Dashboard loads and shows metrics matching `EnrollmentService.get_student_summary`.
  - Enrolling with a valid key produces a success message and updates enrolled classes.
  - Enrolling with an invalid key shows an error message.
  - Soft-unenroll changes status to `unenrolled` (verify via snapshot or dashboard counts) and does not delete the row.
  - All backend calls go through the `EnrollmentService`.

## Deliverable
- A single UI file: `streamlit_app.py` implementing the design above.
- No backend changes except small read-only wrappers in the service if absolutely necessary.



