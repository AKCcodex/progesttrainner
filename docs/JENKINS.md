# Jenkins

The stack ships a Jenkins instance for CI/CD. It runs as a Docker container
alongside the rest of the stack.

## Access

- **URL:** http://localhost:8090  (host 8090 → container 8080)
- **JNLP:** host 50001 → container 50000 (for agents)
- The setup wizard is disabled via `JAVA_OPTS=-Djenkins.install.runSetupWizard=false`
  so the UI loads directly. Auth is open (no admin user created).
  Add `JENKINS_USER` / `JENKINS_PASSWORD` to the `jenkins` service env in
  `docker-compose.yml` and restart to enable login.

## Capabilities

The Jenkins container has the host's Docker socket bind-mounted, so it can
run `docker build`, `docker compose`, and any host-side CLI tool against
the host's daemon. The repo is mounted read-only at `/workspace`.

## Pipelines

The `Jenkinsfile` at the repo root defines a 6-stage pipeline:

1. **Checkout** — sanity check on the workspace
2. **Lint (Python)** — `ruff` over `backend/app/`
3. **Test (Python)** — `pytest` over `backend/tests/unit/`
4. **Lint (TypeScript)** — `tsc --noEmit` over the frontend
5. **Build Images** — `docker compose build backend worker bot frontend`
6. **Smoke Test** — boots a temporary stack, hits `/health` and `/docs`,
   tears down

## Running a build

1. Open http://localhost:8090.
2. **New Item** → name it (e.g. `learning-coach`) → **Pipeline** → OK.
3. Under **Pipeline**:
   - Definition: **Pipeline script from SCM**
   - SCM: **Git** (or "None" if you point it at the workspace mount)
   - Repository URL: `file:///workspace` (since the repo is bind-mounted)
     or your Git remote.
   - Script Path: `Jenkinsfile`
4. Save → **Build Now**.

## Restart

```bash
docker-compose restart jenkins
```

## Reset Jenkins (nuke all state)

```bash
docker-compose down
docker volume rm learning-coach_jenkins_home
docker-compose up -d --no-deps jenkins
```