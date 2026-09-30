# Multi-stage build: compile the Vite app, then serve the static output with
# nginx. Not referenced by the root docker-compose.yml (the frontend is run
# separately with `npm run dev` / `npm run build` today -- see the root
# README) but kept buildable on its own for later deployment.
#
# VITE_API_BASE_URL is baked in at build time (Vite inlines import.meta.env.*
# values into the bundle) -- pass it as a build arg for a non-default backend
# URL: `docker build --build-arg VITE_API_BASE_URL=https://api.example.com .`
FROM node:22-alpine AS build
WORKDIR /app

ARG VITE_API_BASE_URL=http://localhost:8000
ENV VITE_API_BASE_URL=$VITE_API_BASE_URL

COPY package.json package-lock.json ./
RUN npm ci

COPY . .
RUN npm run build

FROM nginx:alpine
COPY --from=build /app/dist /usr/share/nginx/html
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
