# ai-assisted-coding-project-enrollment-manager

This repository contains a small SQLite-backed student enrollment backend used for teaching separation
of concerns: a database layer and a service (business rules) layer.

**Refactor (implemented)**
- `EnrollmentDatabase`: handles SQLite connection, table creation, seeding, and SQL queries.
- `EnrollmentService`: contains enrollment-key validation, enrollment logic, soft-unenroll (status update), and student summary counting.

Files of interest
- `enrollment_starter.py`: Small terminal runner that builds the DB, seeds sample data, demonstrates enrollment, and exports a JSON snapshot.
- `student_enrollment_practice.db`: SQLite database file created when running the script.
- `student_enrollment_snapshot.json`: JSON export of seeded data produced by the script.

Quickstart

1. (Optional) create and activate a virtual environment.

```bash
python3 -m venv .venv
source .venv/bin/activate
```

2. Install optional dependencies (this project uses only the Python stdlib for the backend):

```bash
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

3. Run the terminal runner to create the database, seed data, exercise enrollment, and write the snapshot:

```bash
python3 enrollment_starter.py
```

4. Inspect the snapshot:

```bash
cat student_enrollment_snapshot.json
```

Notes
- The backend uses a soft-unenroll approach (status = `unenrolled`) instead of deleting rows.
- Enrollment key normalization and summary counting remain in the service layer.
- There is no Streamlit UI in this refactor; `requirements.txt` still lists `streamlit` for optional exercises.

If you want, I can add unit tests for `EnrollmentService` next.