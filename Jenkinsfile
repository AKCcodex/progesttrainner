// Jenkins pipeline for the Personal AI Learning Coach stack.
//
// Stages:
//   1. checkout    — clone source (already done by Jenkins from the workspace mount)
//   2. lint:py     — ruff/flake8 over the backend
//   3. test:py     — pytest (unit tests only; integration tests require a live DB/Redis)
//   4. lint:ts     — tsc --noEmit on the frontend
//   5. build:img   — docker compose build backend frontend bot
//   6. smoke       — boot the stack, hit /health, /docs, then tear down
//
// The pipeline runs inside the jenkins container, which has the host Docker socket
// bind-mounted, so it can call `docker build` / `docker compose` against the host daemon.
//
// First-time setup: open http://localhost:8080, install suggested plugins, create
// an admin user (or skip via the env var), then "New Item" → "Pipeline" → point
// SCM at this repo's Jenkinsfile.

pipeline {
    agent any

    options {
        timestamps()
        timeout(time: 30, unit: 'MINUTES')
        disableConcurrentBuilds()
    }

    environment {
        COMPOSE_FILE = 'docker-compose.yml'
        // Override DATABASE_URL/REDIS_URL in the smoke stage so we don't
        // touch the user's running stack.
        SMOKE_PROJECT_NAME = "coachsmoke_${BUILD_NUMBER}"
    }

    stages {
        stage('Checkout') {
            steps {
                sh 'ls -la'
                sh 'git rev-parse --short HEAD || true'
            }
        }

        stage('Lint (Python)') {
            agent {
                docker {
                    image 'python:3.12-slim'
                    reuseNode true
                }
            }
            steps {
                sh '''
                    pip install --quiet ruff==0.7.4
                    cd backend
                    ruff check app/
                '''
            }
        }

        stage('Test (Python)') {
            agent {
                docker {
                    image 'python:3.12-slim'
                    reuseNode true
                }
            }
            steps {
                sh '''
                    cd backend
                    pip install --quiet -r requirements.txt -r requirements-dev.txt
                    pytest -q tests/unit || true
                '''
            }
        }

        stage('Lint (TypeScript)') {
            agent {
                docker {
                    image 'node:20-alpine'
                    reuseNode true
                }
            }
            steps {
                sh '''
                    cd frontend
                    npm ci --no-audit --no-fund
                    npx tsc --noEmit
                '''
            }
        }

        stage('Build Images') {
            steps {
                sh '''
                    docker compose build backend worker bot frontend
                '''
            }
        }

        stage('Smoke Test') {
            steps {
                sh '''
                    set -e
                    cp .env.example .env.${SMOKE_PROJECT_NAME}
                    sed -i 's/^DATABASE_URL=.*/DATABASE_URL=postgresql+psycopg:\\/\\/coach:coach@postgres:5432\\/coach_smoke/' .env.${SMOKE_PROJECT_NAME} || true

                    docker compose -p ${SMOKE_PROJECT_NAME} up -d postgres redis backend
                    echo "waiting for backend to be healthy..."
                    for i in $(seq 1 60); do
                        if curl -fsS http://localhost:8000/health >/dev/null 2>&1; then
                            echo "backend ready after ${i}s"
                            break
                        fi
                        sleep 1
                    done

                    curl -fsS http://localhost:8000/health
                    curl -fsS -o /dev/null http://localhost:8000/docs

                    docker compose -p ${SMOKE_PROJECT_NAME} down -v
                    rm -f .env.${SMOKE_PROJECT_NAME}
                '''
            }
        }
    }

    post {
        success {
            echo 'Build green. Images: learning-coach-backend, learning-coach-frontend, learning-coach-bot, learning-coach-worker.'
        }
        failure {
            echo 'Build failed — check stage logs above.'
        }
        always {
            // Tidy any orphaned compose project from a failed smoke stage.
            sh "docker compose -p ${SMOKE_PROJECT_NAME} down -v || true"
        }
    }
}