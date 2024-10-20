FROM node:18-alpine

# Install pnpm
RUN npm install -g pnpm

WORKDIR /app

COPY package*.json ./
RUN pnpm install

COPY . .

# Disable Astro telemetry
ENV ASTRO_TELEMETRY_DISABLED=1

# RUN npm run build

EXPOSE 4321

CMD ["pnpm", "run", "preview", "--host", "0.0.0.0"]