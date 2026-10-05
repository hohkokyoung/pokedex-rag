# syntax=docker/dockerfile:1
# Development image: runs the Next.js dev server with hot reload.
# Source is bind-mounted via docker-compose; node_modules stays in the image.

FROM node:26-slim

WORKDIR /app

# Install dependencies first for better layer caching.
COPY package.json package-lock.json ./
RUN npm ci

COPY . .

EXPOSE 3000

CMD ["npm", "run", "dev"]
