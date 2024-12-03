FROM node:18-alpine AS base
RUN npm install -g pnpm

# Install dependencies only when package files change
FROM base AS deps
WORKDIR /app
COPY package.json pnpm-lock.yaml ./
RUN pnpm install

# Development stage
FROM base AS development
WORKDIR /app
COPY --from=deps /app/node_modules ./node_modules
COPY . .
ENV ASTRO_TELEMETRY_DISABLED=1
CMD ["pnpm", "run", "dev", "--host"]

# Build stage (for production)
FROM base AS builder
WORKDIR /app
COPY --from=deps /app/node_modules ./node_modules
COPY . .
RUN pnpm run build

# Production runtime
FROM base AS runner
WORKDIR /app
COPY --from=builder /app/dist ./dist
COPY --from=deps /app/node_modules ./node_modules
COPY package.json ./
EXPOSE 4321
ENV HOST=0.0.0.0
ENV PORT=4321
ENV ASTRO_TELEMETRY_DISABLED=1
CMD ["node", "./dist/server/entry.mjs"]