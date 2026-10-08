pipeline {
    agent any

    parameters {
        string(name: 'DOCKERHUB_USERNAME', defaultValue: 'knightprime007', description: 'Docker Hub Registry Namespace')
        string(name: 'OCI_HOST', defaultValue: 'agent.vaikuntrix.in', description: 'Target Public Hostname')
        string(name: 'API_IMAGE_NAME', defaultValue: 'p07-api', description: 'ASP.NET Core API + frontend image name')
        string(name: 'AGENT_IMAGE_NAME', defaultValue: 'p07-agent-runtime', description: 'Python Agent Runtime image name')
        string(name: 'MCP_IMAGE_NAME', defaultValue: 'p07-mcp', description: 'MCP Server image name')
    }

    environment {
        DOCKERHUB_CRED_ID = 'docker-hub-credentials'
    }

    options {
        timeout(time: 40, unit: 'MINUTES')
        disableConcurrentBuilds()
    }

    stages {
        stage('Checkout') {
            steps {
                checkout scm
                script {
                    if (!env.GIT_COMMIT?.trim()) {
                        error('GIT_COMMIT is missing; immutable Git SHA tag is required')
                    }

                    env.GIT_SHA = env.GIT_COMMIT.take(7)
                    env.API_TAG = "${params.DOCKERHUB_USERNAME}/${params.API_IMAGE_NAME}:${env.GIT_SHA}"
                    env.API_LATEST = "${params.DOCKERHUB_USERNAME}/${params.API_IMAGE_NAME}:latest"
                    env.AGENT_TAG = "${params.DOCKERHUB_USERNAME}/${params.AGENT_IMAGE_NAME}:${env.GIT_SHA}"
                    env.AGENT_LATEST = "${params.DOCKERHUB_USERNAME}/${params.AGENT_IMAGE_NAME}:latest"
                    env.MCP_TAG = "${params.DOCKERHUB_USERNAME}/${params.MCP_IMAGE_NAME}:${env.GIT_SHA}"
                    env.MCP_LATEST = "${params.DOCKERHUB_USERNAME}/${params.MCP_IMAGE_NAME}:latest"

                    echo "Checked out commit: ${env.GIT_COMMIT} (Short SHA: ${env.GIT_SHA})"
                }
            }
        }

        stage('Secret Scan') {
            steps {
                script {
                    echo "Executing Gitleaks secret detection..."
                    sh 'docker run --rm -v "${WORKSPACE}:/source:ro" zricethezav/gitleaks:latest detect --source /source --verbose'
                }
            }
        }

        stage('Test & Quality Gates') {
            steps {
                script {
                    echo "1/3: Running Python Agent Runtime and MCP tests..."
                    sh '''
                        docker run --rm -v "${WORKSPACE}:/app" -w /app/agent-runtime python:3.12-slim sh -c "
                            pip install --no-cache-dir -r requirements.txt &&
                            PYTHONPATH=/app pytest tests/ -v
                        "
                        docker run --rm -v "${WORKSPACE}:/app" -w /app/mcp-server python:3.12-slim sh -c "
                            pip install --no-cache-dir -r requirements.txt &&
                            PYTHONPATH=/app pytest tests/ -v
                        "
                    '''

                    echo "2/3: Running ASP.NET Core Backend Tests..."
                    sh '''
                        docker run --rm -v "${WORKSPACE}:/app" -w /app mcr.microsoft.com/dotnet/sdk:10.0-preview sh -c "
                            dotnet test backend/P07.Tests/P07.Tests.csproj -c Release
                        "
                    '''

                    echo "3/3: Running SvelteKit Frontend Type Checks and Build..."
                    sh '''
                        docker run --rm -v "${WORKSPACE}:/app" -w /app/frontend node:22-alpine sh -c "
                            npm ci &&
                            npm run check &&
                            npm run build
                        "
                    '''
                }
            }
        }

        stage('Build ARM64 Images') {
            steps {
                script {
                    echo "Building production images for linux/arm64..."
                    sh """
                        docker buildx build --platform linux/arm64 -t ${API_TAG} -t ${API_LATEST} -f backend/Dockerfile . --load
                        docker buildx build --platform linux/arm64 -t ${AGENT_TAG} -t ${AGENT_LATEST} -f agent-runtime/Dockerfile agent-runtime/ --load
                        docker buildx build --platform linux/arm64 -t ${MCP_TAG} -t ${MCP_LATEST} -f mcp-server/Dockerfile mcp-server/ --load
                    """
                }
            }
        }

        stage('Container Security Scan') {
            steps {
                script {
                    echo "Scanning container images with Trivy..."
                    sh "docker run --rm -v /var/run/docker.sock:/var/run/docker.sock aquasec/trivy:latest image --severity HIGH,CRITICAL --exit-code 1 ${API_TAG}"
                    sh "docker run --rm -v /var/run/docker.sock:/var/run/docker.sock aquasec/trivy:latest image --severity HIGH,CRITICAL --exit-code 1 ${AGENT_TAG}"
                    sh "docker run --rm -v /var/run/docker.sock:/var/run/docker.sock aquasec/trivy:latest image --severity HIGH,CRITICAL --exit-code 1 ${MCP_TAG}"
                }
            }
        }

        stage('Push Docker Hub') {
            steps {
                script {
                    echo "Publishing immutable container images to Docker Hub..."
                    withCredentials([usernamePassword(credentialsId: DOCKERHUB_CRED_ID, usernameVariable: 'DH_USER', passwordVariable: 'DH_PASS')]) {
                        sh 'echo "$DH_PASS" | docker login -u "$DH_USER" --password-stdin'
                        sh "docker push ${API_TAG} && docker push ${API_LATEST}"
                        sh "docker push ${AGENT_TAG} && docker push ${AGENT_LATEST}"
                        sh "docker push ${MCP_TAG} && docker push ${MCP_LATEST}"
                    }
                }
            }
        }

        stage('Deploy OCI') {
            steps {
                script {
                    echo "Deploying P07 multi-service architecture to target host..."
                    sh """
                        if [ ! -f /opt/projects/autonomous-workspace-agent/.env ]; then
                            echo "ERROR: Production environment file /opt/projects/autonomous-workspace-agent/.env not found on deployment host!"
                            exit 1
                        fi

                        cp docker-compose.yml /opt/projects/autonomous-workspace-agent/docker-compose.yml

                        P07_API_IMAGE="${API_TAG}" \
                        P07_AGENT_IMAGE="${AGENT_TAG}" \
                        P07_MCP_IMAGE="${MCP_TAG}" \
                        docker compose --env-file /opt/projects/autonomous-workspace-agent/.env -f /opt/projects/autonomous-workspace-agent/docker-compose.yml pull

                        P07_API_IMAGE="${API_TAG}" \
                        P07_AGENT_IMAGE="${AGENT_TAG}" \
                        P07_MCP_IMAGE="${MCP_TAG}" \
                        docker compose --env-file /opt/projects/autonomous-workspace-agent/.env -f /opt/projects/autonomous-workspace-agent/docker-compose.yml up -d
                    """
                }
            }
        }

        stage('Post-Deployment Verification') {
            steps {
                script {
                    withEnv(["P07_PUBLIC_HOST=${params.OCI_HOST}"]) {
                        sh '''
                            MAX_ATTEMPTS=20
                            SLEEP_SECONDS=2
                            CURL_TIMEOUT=2
                            P07_HEALTH_URL="http://127.0.0.1:8007/health"
                            API_HEALTH_URL="http://127.0.0.1:8007/api/v1/health"

                            echo "Layer 1 Verification: P07 local endpoint readiness ($P07_HEALTH_URL)..."
                            ATTEMPT=1
                            SUCCESS=0

                            while [ $ATTEMPT -le $MAX_ATTEMPTS ]; do
                                HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" --max-time "$CURL_TIMEOUT" "$P07_HEALTH_URL") || HTTP_CODE="000"
                                if [ "$HTTP_CODE" = "200" ]; then
                                    echo "[Attempt $ATTEMPT/$MAX_ATTEMPTS] P07 endpoint healthcheck: PASS (HTTP 200 OK)"
                                    SUCCESS=1
                                    break
                                fi

                                echo "[Attempt $ATTEMPT/$MAX_ATTEMPTS] P07 starting up (HTTP $HTTP_CODE). Retrying..."
                                sleep "$SLEEP_SECONDS"
                                ATTEMPT=$((ATTEMPT + 1))
                            done

                            if [ $SUCCESS -ne 1 ]; then
                                echo "ERROR: P07 endpoint readiness check failed after $MAX_ATTEMPTS attempts against $P07_HEALTH_URL (Status: $HTTP_CODE)!"
                                exit 1
                            fi

                            echo "Layer 1b Verification: ASP.NET Core API health through same public endpoint ($API_HEALTH_URL)..."
                            API_CODE=$(curl -s -o /dev/null -w "%{http_code}" --max-time "$CURL_TIMEOUT" "$API_HEALTH_URL") || API_CODE="000"
                            if [ "$API_CODE" != "200" ]; then
                                echo "ERROR: Backend API health check returned HTTP $API_CODE at $API_HEALTH_URL"
                                exit 1
                            fi
                            echo "Layer 1b API Healthcheck: PASS (HTTP 200 OK)"

                            echo "Layer 2 Verification: Cloudflared Tunnel process verification..."
                            if pgrep cloudflared >/dev/null || systemctl is-active cloudflared >/dev/null 2>&1 || docker ps | grep -q cloudflared; then
                                echo "Cloudflared tunnel status: RUNNING"
                            else
                                echo "ERROR: Cloudflared tunnel process is not active on host!"
                                exit 1
                            fi

                            echo "Layer 3 Verification: Public HTTPS route (https://$P07_PUBLIC_HOST)..."
                            HTTP_STATUS=$(curl -o /dev/null -s -w "%{http_code}" --max-time 10 "https://$P07_PUBLIC_HOST" || echo "CURL_ERROR")
                            if [ "$HTTP_STATUS" = "200" ]; then
                                echo "Public Cloudflare route: PASS (HTTP 200 OK)"
                            elif [ "$HTTP_STATUS" = "503" ] || [ "$HTTP_STATUS" = "403" ]; then
                                echo "Public Cloudflare route: CHALLENGED (HTTP $HTTP_STATUS. Deployment Healthy)."
                            else
                                echo "ERROR: Public Cloudflare route failed with status $HTTP_STATUS"
                                exit 1
                            fi
                        '''
                    }
                }
            }
        }

        stage('Target Disk Cleanup') {
            steps {
                script {
                    echo "Performing disk cleanup for obsolete P07 images..."
                    sh """
                        docker image prune -f
                        docker container prune -f --filter "label=com.docker.compose.project=autonomous-workspace-agent"
                    """
                }
            }
        }
    }

    post {
        always {
            cleanWs(deleteDirs: true, notFailBuild: true)
        }
        success {
            echo "Successfully built, tested, scanned, published, and deployed P07 commit ${env.GIT_SHA} with Cloudflare targeting 127.0.0.1:8007!"
        }
        failure {
            echo "Pipeline execution failed on commit ${env.GIT_COMMIT}."
        }
    }
}
