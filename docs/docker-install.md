# Install Nepal Compliance using Docker
**This guide will help you to install and run Nepal Compliance using Docker and Docker Compose.**

### Dependencies
You need to have the Docker installed and ready in your system:
* Docker Engine & Docker CLI. Check using `docker --version`
* Docker Compose. Check using `docker compose version`

## Step 1: Clone the Repository
First, clone the Nepal Compliance repository from GitHub:
```
git clone https://github.com/lynxx-st/nepal-compliance.git
```
Change directory into the folder:
```
cd nepal-compliance
```

## Step 2: Set Up Environment Variables

Copy the `.env.example` to `.env`

```
cp .env.example .env
```

Edit the `.env` file with your own values. For eg:

```
ADMIN_PASSWORD=your-admin-password
DB_ROOT_PASSWORD=your-db-root-password
FRAPPE_SITE=frontend
REQUIRED_FRAPPE_APPS=erpnext,hrms,crm,print_designer,insights,mail,raven,nepal_compliance
STALWART_HOSTNAME=mail.example.com
STALWART_MAIL_DOMAIN=example.com
STALWART_ADMIN_URL=https://127.0.0.1:4443
STALWART_ACCOUNT_ID=d333333
STALWART_RECOVERY_ADMIN=admin:replace-with-a-strong-password
```
***Note: The `.env` file should be placed at the root of the project directory next to your `compose.yaml` file.***


## Step 3: Pull the Docker Image
### Pull the default `latest` tag from DockerHub
```
docker pull lynxxstein/nepal-compliance
```
**Or**, specify a VERSION_TAG. For eg:
```
docker pull lynxxstein/nepal-compliance:latest
```

## Step 4: Run Nepal Compliance with Docker Compose

```
docker compose up -d
```

### Access your ERP instance running at `http://localhost:8080`

Now you should have Nepal Compliance up and running using Docker.

After Docker Compose starts, the `create-site-1` container creates the `frontend` site when needed and reconciles the required app list. On an existing site, it installs only missing apps and then runs migrations. This can take several minutes, so check its logs before accessing the site.
```
docker logs {container-name} -f
```

Also after setting up the `.env` file, you can check variables and values used by your Compose to interpolate the Compose model by running:
```
docker compose config --environment
```
This command should display all environment variables in `.env` being used in your Docker Compose.

---
### Environment Variables
These variables are defined in an `.env` file and used to inject configuration into services via `docker compose`.

| Key                         | Value                     | Description                                               |
|-----------------------------|---------------------------|-----------------------------------------------------------|
| `VERSION_TAG`               | `latest`                  | Version of the current Docker image tag. Default `latest` |
| `DB_HOST`                   | `db`                      | Hostname of the MariaDB container.                        |
| `DB_PORT`                   | `"3306"`                  | Port for the database (MySQL/MariaDB).                    |
| `MYSQL_ROOT_PASSWORD`       | `your-mysql-root-password`| Root password for MySQL (if used).                        |
| `MARIADB_ROOT_PASSWORD`     | `your-db-root-password`   | MariaDB root password (primary for ERPNext setup).        |
| `DB_ROOT_PASSWORD`          | `your-db-root-password`   | General DB root password (may overlap with MariaDB one).  |
| `REDIS_CACHE`               | `redis-cache:6379`        | Redis instance for caching.                               |
| `REDIS_QUEUE`               | `redis-queue:6379`        | Redis instance for task queues.                           |
| `SOCKETIO_PORT`             | `"9000"`                  | Port used by the WebSocket server.                        |
| `SOCKETIO`                  | `websocket:9000`          | WebSocket address used by the frontend.                   |
| `ADMIN_PASSWORD`            | `your-admin-password`     | Administrator password for `bench new-site {site} --admin-password`|
| `FRAPPE_SITE`               | `frontend`                | Site to create, migrate, and reconcile during setup.       |
| `REQUIRED_FRAPPE_APPS`      | `erpnext,hrms,crm,print_designer,insights,mail,raven,nepal_compliance` | Idempotent app set installed on new and existing sites. |
| `STALWART_HOSTNAME`         | `mail.example.com`         | Public hostname and internal network alias for Stalwart. |
| `STALWART_MAIL_DOMAIN`      | `example.com`              | Domain accepted by the Stalwart mailbox helper.          |
| `STALWART_ADMIN_URL`        | `https://127.0.0.1:4443`   | Local Stalwart administration and JMAP endpoint.          |
| `STALWART_ACCOUNT_ID`       | `d333333`                  | Stalwart tenant/account identifier used for provisioning. |
| `STALWART_RECOVERY_ADMIN`   | `admin:...`                | Initial Stalwart recovery account; use a strong secret.   |
| `BACKEND`                   | `backend:8000`            | Backend app server address used by frontend.              |
| `FRAPPE_SITE_NAME_HEADER`   | `frontend`                | Site name. Host header to route requests in multi-site setup.|
| `UPSTREAM_REAL_IP_ADDRESS`  | `127.0.0.1`               | Upstream proxy IP for real IP resolution.                   |
| `UPSTREAM_REAL_IP_HEADER`   | `X-Forwarded-For`         | Header to extract the real IP of the client.              |
| `UPSTREAM_REAL_IP_RECURSIVE`| `"off"`                   | Enables/disables recursive lookup for real IPs.            |

### Reconcile apps on an existing deployment

Every release deployment runs the app reconciliation automatically. For a manual deployment, run:

```bash
bash scripts/install-required-apps.sh
```

The command skips apps that are already installed, installs missing bundled apps, migrates the site, clears its cache, and fails if the image does not contain a required app.

### Stalwart mail service

Stalwart is included in the Compose stack and persists its configuration in the `stalwart-data` volume. Before the first start, set a strong `STALWART_RECOVERY_ADMIN` value and replace the example hostname/domain. The stack exposes SMTP, submission, IMAP, JMAP, and its administration endpoint; restrict these ports with your server firewall to the networks that require them.

To provision a mailbox and corresponding ERPNext/Raven records after Stalwart is configured:

```bash
python3 scripts/add-mail-user person@example.com "Person Name"
```

# Next
* Learn how to [contribute to this project](/CONTRIBUTING.md)
* [Manual Install - Nepal Compliance](/docs/manual-install.md)

**If you liked our work, then we would love to get your stars on our GitHub and Docker repositories.** 😀
