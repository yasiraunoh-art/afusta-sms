# AFUSTA Result Alert System — Visual Overview

Open this file in a Markdown preview that renders Mermaid diagrams.

## High-level architecture

```mermaid
flowchart LR
    Student[Student]
    Lecturer[Lecturer]
    Admin[Department admin]

    subgraph Django["Django application"]
        UI[Server-rendered pages]
        Accounts[Accounts and role checks]
        Academics[Courses and results]
        Alerts[Notification service]
        Callback[SMS delivery callback]
        UI --> Accounts
        UI --> Academics
        Academics --> Alerts
        Callback --> Alerts
    end

    DB[(SQLite by default)]
    Email[Email backend]
    AT[Africa's Talking SMS]
    Redis[(Redis broker)]
    Celery[Celery worker]

    Student --> UI
    Lecturer --> UI
    Admin --> UI
    Accounts --> DB
    Academics --> DB
    Alerts --> DB
    Alerts --> Email
    Alerts --> AT
    AT -->|Delivery report| Callback
    Academics -. Optional async delivery .-> Redis
    Redis --> Celery
    Celery --> Alerts
```

## Result approval and notification sequence

```mermaid
sequenceDiagram
    actor Lecturer
    actor Admin
    actor Student
    participant App as Django app
    participant DB as Database
    participant Queue as Redis / Celery
    participant Notify as Notification service
    participant Mail as Email backend
    participant SMS as Africa's Talking

    Lecturer->>App: Submit result
    App->>DB: Save as pending
    Admin->>App: Approve result
    App->>DB: Mark approved and record approver
    alt Synchronous mode (default)
        App->>Notify: Send alerts in request
    else Asynchronous mode
        App->>Queue: Enqueue result ID
        Queue->>Notify: Worker runs alert task
    end
    Notify->>Mail: Send email
    Mail-->>Notify: Delivery attempt result
    Notify->>DB: Log email outcome
    alt SMS credentials configured
        Notify->>SMS: Submit SMS
        SMS-->>Notify: Submission status and message ID
        Notify->>DB: Log SMS outcome
        SMS-->>App: Later delivery report
        App->>DB: Update SMS delivery status
    else SMS credentials absent
        Notify->>DB: Log simulated SMS
    end
    App-->>Admin: Approval confirmed
    Student->>App: Open results dashboard
    App->>DB: Query approved results
    DB-->>App: Approved results only
    App-->>Student: Display released result
```

## CSV result-upload sequence

```mermaid
sequenceDiagram
    actor Lecturer
    participant App as Django app
    participant DB as Database

    Lecturer->>App: Upload CSV
    App->>DB: Load lecturer's assigned courses
    loop Each CSV row
        App->>DB: Look up student and course
        alt Student exists and course is assigned
            App->>DB: Save or update pending result
        else Invalid or unauthorized row
            App->>App: Count row as skipped
        end
    end
    App-->>Lecturer: Show submitted and skipped counts
```

## Proposed roadmap

```mermaid
flowchart LR
    P1["1 · Pilot safety<br/>Secure configuration<br/>Guard approval transitions<br/>Validate scores and CSV<br/>Test roles and callbacks"]
    G1{"Safe pilot<br/>criteria met?"}
    P2["2 · Delivery reliability<br/>Transactional outbox<br/>Retry with idempotency<br/>Track provider IDs and states<br/>Test failure and recovery"]
    G2{"Delivery recovery<br/>verified?"}
    P3["3 · Production rollout<br/>Managed database<br/>Backups and rollback<br/>Monitoring and alerting<br/>Onboarding and support"]
    Live["Institutional rollout"]

    P1 --> G1
    G1 -->|Yes| P2
    G1 -->|Not yet| P1
    P2 --> G2
    G2 -->|Yes| P3
    G2 -->|Not yet| P2
    P3 --> Live
```

Roadmap boxes are recommendations, not implemented features. Agree the
department's result-correction, onboarding, and retention policies before
production rollout. See [the detailed notes](architecture-and-roadmap.md)
for current behavior and phase exit criteria.
