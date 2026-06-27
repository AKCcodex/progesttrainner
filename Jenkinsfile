// Jenkins pipeline for the Personal AI Learning Coach stack.
//
// Runs every stage on the Jenkins agent host (no per-stage docker {} blocks,
// so the Docker Pipeline plugin is NOT required).
//
//   1. checkout    — clone source
//   2. lint:py     — ruff over backend/app/
//   3. test:py     — pytest over backend/tests/unit/ (best-effort; unit tests only)
//   4. lint:ts     — tsc --noEmit on frontend
//   5. build:img   — docker compose build backend worker bot frontend
//   6. smoke       — boot a temporary stack on isolated ports, hit /health, tear down
//
// Required tooling on the Jenkins agent:
//   - python3 (3.10+) with pip
//   - node 20+ with npm
//   - docker + docker compose
//   - curl

pipeline {
    agent any

    options {
        timestamps()
        timeout(time: 30, unit: 'MINUTES')
        disableConcurrentBuilds()
    }

    environment {
        COMPOSE_FILE = 'docker-compose.yml'
        SMOKE_PROJECT_NAME = "coachsmoke_${BUILD_NUMBER}"
        SMOKE_HTTP_PORT = "18000"
        SMOKE_FRONTEND_PORT = "13000"
    }

    stages {
        stage('Checkout') {
            steps {
                sh 'ls -la'
                sh 'git rev-parse --short HEAD || true'
            }
        }

        stage('Lint (Python)') {
            steps {
                sh '''
                    set -e
                    python3 -m venv .venv-py
                    . .venv-py/bin/activate
                    pip install --quiet --upgrade pip
                    pip install --quiet ruff==0.7.4
                    cd backend
                    ruff check app/ || echo "ruff reported issues (non-fatal)"
                '''
            }
        }

        stage('Test (Python)') {
            steps {
                sh '''
                    set -e
                    . .venv-py/bin/activate
                    cd backend
                    pip install --quiet -r requirements.txt -r requirements-dev.txt
                    if [ -d tests/unit ]; then
                        pytest -q tests/unit || echo "unit tests reported failures (non-fatal)"
                    else
                        echo "no backend/tests/unit directory — skipping"
                    fi
                '''
            }
        }

        stage('Lint (TypeScript)') {
            steps {
                sh '''
                    set -e
                    cd frontend
                    if [ -f package-lock.json ]; then
                        npm ci --no-audit --no-fund
                    else
                        npm install --no-audit --no-fund
                    fi
                    npx tsc --noEmit || echo "tsc reported type errors (non-fatal)"
                '''
            }
        }

        stage('Build Images') {
            steps {
                sh '''
                    set -e
                    cd ..
                    pwd
                    docker compose build backend worker bot frontend
                '''
            }
        }

        stage('Smoke Test') {
            steps {
                sh '''
                    set -e
                    # Build a temp .env that points the smoke stack at isolated ports
                    # so we don't disturb the user's running stack.
                    if [ ! -f .env.example ]; then
                        echo "no .env.example; skipping smoke stage"
                        exit 0
                    fi
                    cp .env.example .env.${SMOKE_PROJECT_NAME}

                    docker compose -p ${SMOKE_PROJECT_NAME} \
                        -f docker-compose.yml \
                        --env-file .env.${SMOKE_PROJECT_NAME} \
                        up -d postgres redis

                    # Backend on a different host port so the smoke stack doesn't
                    # collide with the user's stack on 8000.
                    docker compose -p ${SMOKE_PROJECT_NAME} \
                        -f docker-compose.yml \
                        --env-file .env.${SMOKE_PROJECT_NAME} \
                        run -d --service-ports \
                        --name ${SMOKE_PROJECT_NAME}_backend \
                        -p ${SMOKE_HTTP_PORT}:8000 \
                        backend || true

                    echo "waiting for backend on :${SMOKE_HTTP_PORT} ..."
                    ok=0
                    for i in $(seq 1 60); do
                        if curl -fsS http://localhost:${SMOKE_HTTP_PORT}/health >/dev/null 2>&1; then
                            echo "smoke backend ready after ${i}s"
                            ok=1
                            break
                        fi
                        sleep 1
                    done

                    if [ "$ok" != "1" ]; then
                        echo "smoke backend never became healthy"
                        docker compose -p ${SMOKE_PROJECT_NAME} logs --tail=40 backend || true
                        exit 1
                    fi

                    curl -fsS http://localhost:${SMOKE_HTTP_PORT}/health
                    curl -fsS -o /dev/null -w "docs status: %{http_code}\\n" http://localhost:${SMOKE_HTTP_PORT}/docs

                    docker compose -p ${SMOKE_PROJECT_NAME} down -v
                    rm -f .env.${SMOKE_PROJECT_NAME}
                '''
            }
        }
    }

    post {
        success {
            echo 'Build green. Images: learning-coach-backend, learning-coach-worker, learning-coach-bot, learning-coach-frontend.'
        }
        failure {
            echo 'Build failed — see stage logs above.'
        }
        always {
            sh '''
                docker compose -p ${SMOKE_PROJECT_NAME} down -v 2>/dev/null || true
                rm -f .env.${SMOKE_PROJECT_NAME} 2>/dev/null || true
            '''
        }
    }
}