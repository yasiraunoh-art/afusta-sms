# AFUSTA CS Result Alert System

A Django web application that lets the Department of Computer Science,
Abdullahi Fodio University of Science & Technology (AFUSTA), notify students
by SMS and email the moment an examination result is approved.

Built for the final year project *"Development of Student Based Short
Message Service and Electronic Mail Results Alert Scheme"*.

See the [visual architecture, sequence flows, and proposed roadmap](docs/system-diagrams.md).
The [detailed architecture notes](docs/architecture-and-roadmap.md) explain the
current behavior and roadmap recommendations.

## Roles

- **Student** — registers with matric number, phone and email; views their
  own approved results; receives an SMS + email the moment a result is
  approved.
- **Lecturer** — uploads results (one at a time, or as a CSV batch) for the
  courses they're assigned to.
- **Admin** — approves/rejects submitted results; adds, edits and deletes
  courses, students and lecturer accounts; manages lecturer-to-course
  assignments; and can see a full log of every notification that was sent.
  Deleting anything shows a confirmation page first, spelling out what else
  gets removed with it (a course takes its results with it, and so on).

## Quick start

```bash
python3 -m venv venv
source venv/bin/activate          # venv\Scripts\activate on Windows
pip install -r requirements.txt

python manage.py migrate
python manage.py seed_demo_data   # creates demo logins, see below
python manage.py runserver
```