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

Visit http://127.0.0.1:8000/

## Temporary public demo on Render

The included [`render.yaml`](render.yaml) defines a free web service and a
separate PostgreSQL database. Follow [the Render deployment guide](docs/render-deployment.md)
to publish a demo with fictional seed data. The existing `db.sqlite3` and
`.env` stay local and must not be committed or uploaded.

Render's free web service sleeps when idle, and its free PostgreSQL database
expires after 30 days (with a 14-day upgrade grace period before deletion).
The free service also cannot send SMTP traffic, so demo emails are written to
the service logs; SMS is simulated unless you separately configure a provider.
This free setup is for testing, not long-term storage or production use.

## Demo logins (created by `seed_demo_data`)

| Role     | Username        | Password       |
|----------|-----------------|----------------|
| Admin    | `admin`         | `admin12345`   |
| Lecturer | `CSC-LEC-01`    | `lecturer12345`|
| Student  | `CSC/2021/001`  | `student12345` |

The seed command also creates one course (CSC301) and one result sitting in
`pending` status — log in as admin and approve it from **Pending approvals**
to see the whole notification pipeline fire.

Django's own admin panel is available at `/django-admin/` with the same
admin login, if you need to inspect/edit raw data during your defense.

## How notifications actually get sent

`notifications/services.py` is the single place this happens:

- **Email** goes through Django's normal `send_mail`. By default it uses
  the console backend, so messages just print to your terminal — good
  enough for a demo. Fill in `.env` (copy from `.env.example`) with a real
  SMTP account to send real email.
- **SMS** posts to the Africa's Talking SMS API. If the Africa's Talking
  credentials are not set, the
  system does **not** fail — it writes a `simulated` row to the
  notification log instead, containing the exact message that would have
  been sent. This means the whole approve → notify flow is demonstrable
  without paying for an SMS account. Add `AFRICASTALKING_USERNAME` and
  `AFRICASTALKING_API_KEY` to switch on live sending. Optionally add
  `AFRICASTALKING_SENDER_ID` after Africa's Talking approves your sender ID.
  Use the sandbox URL while testing and the production URL when going live.

Every attempt (real, simulated or failed) is written to `NotificationLog`
and visible to the admin at **Notification log**.

### Africa's Talking delivery reports

The application accepts delivery reports at:

```
/notifications/africastalking/delivery-reports/
```

Register the complete public HTTPS URL in the Africa's Talking dashboard under
**SMS → Callback URLs → Delivery Reports**, for example:

```
https://your-domain.example/notifications/africastalking/delivery-reports/
```

`http://127.0.0.1:8000/...` will not work because Africa's Talking cannot reach
your computer. For local testing, expose the running Django server through a
secure tunnel such as `ngrok http 8000`, then register the generated HTTPS URL
with the callback path above. The callback updates the notification log with
the final provider status and failure reason when one is supplied.

## Async delivery (optional, for a "production-grade" demo point)

By default, `NOTIFY_SYNCHRONOUSLY=True`, so approving a result sends the
alerts immediately within the same request — no extra services required to
run the project.

To actually demonstrate the Celery + Redis architecture described in the
project report:

```bash
redis-server &
celery -A resultalert worker --loglevel=info &
```

...then set `NOTIFY_SYNCHRONOUSLY=False` in your `.env`. Approving a result
will now queue a background job instead of blocking the request.

## Project layout

```
accounts/       custom User model (role: student/lecturer/admin), auth views,
                account settings + password change
academics/      Course, Result models; every dashboard + upload/approval view
notifications/  NotificationLog model, the email/SMS sending service, Celery task
templates/      all HTML, split into public pages and the post-login app shell
static/         brand CSS, the user-menu script, the crest and campus photos
```

Shared template partials worth knowing about:

- `templates/_form_fields.html` — renders any form's fields plus errors.
- `templates/_sidenav.html` — picks the sidebar nav for whichever role is
  logged in. Pages that want a link highlighted override the `sidenav`
  block and include their role's nav with an `active` key instead.
- `templates/academics/_admin_nav.html`, `_lecturer_nav.html`,
  `_student_nav.html` — the three navs themselves.

## Signing in and account settings

Every signed-in page has a user menu in the top-right corner showing the
person's name and role. It opens onto **Settings** and **Sign out**.

Settings (`/accounts/settings/`) is available to all three roles. It shows
the profile the alerts are sent to, and lets the user change their own
password — Django's `PasswordChangeForm` does the checking, so the old
password must be correct and the new one has to pass
`AUTH_PASSWORD_VALIDATORS`. The session is refreshed on success so nobody
gets logged out by changing their own password.

Admins can also reset anyone else's password from **Students** or
**Lecturers** → Edit; leaving the password field blank there keeps the
existing one.

## Things to point out in your defense

- **Push notification model**: the student never has to request anything —
  approval triggers delivery automatically (see `academics/views.py`,
  `approve_result`).
- **Separation of concerns**: notification sending is isolated in its own
  app/service so it can be swapped (Africa's Talking, SMTP → SendGrid)
  without touching the result-approval logic.
- **Graceful degradation**: SMS "simulates" rather than crashing when
  unconfigured — a deliberate design choice, not a missing feature.
- **Data integrity**: only an admin-approved result becomes visible to a
  student or triggers a notification (`Result.Status`), directly answering
  the "prevent unauthorized access or mutilation of results" objective in
  Chapter One.
