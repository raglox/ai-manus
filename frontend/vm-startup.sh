#!/bin/bash
# Pull and run frontend container with correct backend URL

docker pull us-central1-docker.pkg.dev/gen-lang-client-0415541083/manus-app/frontend:latest

# Stop any existing containers
docker stop $(docker ps -aq) 2>/dev/null || true
docker rm $(docker ps -aq) 2>/dev/null || true

# Run frontend with backend URL
docker run -d \
  --name manus-frontend \
  --restart always \
  -p 80:80 \
  -e BACKEND_URL='https://manus-backend-test-247096226016.us-central1.run.app/' \
  us-central1-docker.pkg.dev/gen-lang-client-0415541083/manus-app/frontend:latest

echo "✅ Frontend started with backend proxy"
