# Temporary Render demo

This project can be deployed as a public demo using Render's free web service
and free PostgreSQL database. It uses PostgreSQL on Render because Render's
web-service filesystem is temporary: a local SQLite file would be lost when
the service restarts, redeploys, or sleeps.

## Important limits

- The free web service sleeps after 15 minutes without traffic and may take
  about a minute to wake up.
- The free PostgreSQL database expires 30 days after creation. Render provides
  a 14-day grace period to upgrade before deleting the database and its data.
- Render free services cannot make outbound SMTP connections on ports 25,
  465, or 587. This demo uses Django's console email backend, so email content
  appears in service logs rather than being delivered.
- No SMS credentials are configured by the blueprint. SMS is recorded as
  simulated and does not send to real phones.
- The deployment seeds fictional demo accounts and a sample result. Do not put
  real student details, grades, password hashes, `.env`, or `db.sqlite3` in
  the Render service or its Git repository.

## Deploy

1. Put this project in a **dedicated GitHub repository**. The current Git
   remote in this workspace is `Shullyson/sales-report-agent`, which is not
   this app; do not deploy that repository as this project. Ensure `.env`,
   `db.sqlite3`, `venv/`, and generated `staticfiles/` are not committed.
2. In Render, choose **New → Blueprint**, connect the dedicated repository,
   and deploy the `render.yaml` blueprint.
3. When prompted for `DEMO_ADMIN_PASSWORD`, enter a unique, long password.
   It is used for the synthetic demo's `admin` account and is not stored in
   the repository. Do not reuse a password from another service.
4. Wait for the build and first deploy to finish. Render runs migrations,
   creates only the seed demo records in its PostgreSQL database, and starts
   Gunicorn. Open the `onrender.com` URL shown on the Render service page.
5. Keep the admin password private. The existing local SQLite records are
   intentionally not included; the demo database starts with synthetic data.

The blueprint uses the service hostname Render provides to configure allowed
hosts and HTTPS CSRF origin automatically. It generates a Django secret key
for the hosted service. The local `.env.example` is only a template for local
development, not a file to upload to Render.

## Existing SQLite data

The project's current SQLite database is deliberately kept local. It may
contain student names, matriculation numbers, contact details, results, and
password hashes. This deployment guide does not export or upload it. If real
records are ever needed in a hosted environment, the data owner should first
approve an appropriate private hosting and data-protection arrangement.

## Official Render references

- [Deploy a Django app](https://render.com/docs/deploy-django)
- [Blueprint specification](https://render.com/docs/blueprint-spec)
- [Free instance limitations](https://render.com/docs/free)
