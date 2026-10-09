# ==============================================================================
# CampusOS Web (Next.js) Production Multi-Stage Dockerfile
# Optimized for minimal image size, zero devDependencies, and non-root execution.
# ==============================================================================

# ------------------------------------------------------------------------------
# Stage 1: Base dependencies
# ------------------------------------------------------------------------------
FROM node:20-alpine AS deps
RUN apk add --no-cache libc6-compat
WORKDIR /app

# Copy root package files and workspace packages
COPY package.json package-lock.json ./
COPY packages/types/package.json ./packages/types/
COPY packages/config/package.json ./packages/config/
COPY apps/web/package.json ./apps/web/

# Deterministic clean install
RUN npm ci

# ------------------------------------------------------------------------------
# Stage 2: Production Builder
# ------------------------------------------------------------------------------
FROM node:20-alpine AS builder
RUN apk add --no-cache libc6-compat
WORKDIR /app

COPY --from=deps /app/node_modules ./node_modules
COPY package.json package-lock.json tsconfig.base.json ./
COPY packages ./packages
COPY apps/web ./apps/web

# Set production environment flags for build
ENV NEXT_TELEMETRY_DISABLED=1
ENV NODE_ENV=production

# Build the Next.js application with standalone output
RUN npm run build --workspace=apps/web

# ------------------------------------------------------------------------------
# Stage 3: Production Runner (Minimal & Hardened)
# ------------------------------------------------------------------------------
FROM node:20-alpine AS runner
WORKDIR /app

ENV NODE_ENV=production
ENV NEXT_TELEMETRY_DISABLED=1
ENV PORT=3000
ENV HOSTNAME="0.0.0.0"

# Create dedicated non-root user and group
RUN addgroup --system --gid 10001 nodejs && \
    adduser --system --uid 10001 nextjs

# Copy public assets and standalone output
COPY --from=builder /app/apps/web/public ./apps/web/public
COPY --from=builder --chown=nextjs:nodejs /app/apps/web/.next/standalone ./
COPY --from=builder --chown=nextjs:nodejs /app/apps/web/.next/static ./apps/web/.next/static

USER nextjs

EXPOSE 3000

# Container healthcheck
HEALTHCHECK --interval=30s --timeout=5s --start-period=15s --retries=3 \
    CMD wget -qO- http://localhost:3000 || exit 1

# Start the standalone Next.js server
CMD ["node", "apps/web/server.js"]
