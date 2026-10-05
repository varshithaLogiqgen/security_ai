FROM node:24-bookworm-slim AS build
WORKDIR /app
COPY frontend/package*.json ./
RUN npm ci
COPY frontend/ ./
ENV VITE_DEMO_MODE=false VITE_API_BASE_URL=/api/v1
RUN npm run build
FROM caddy:2-alpine
COPY --from=build /app/dist /srv
COPY deployment/Caddyfile /etc/caddy/Caddyfile
