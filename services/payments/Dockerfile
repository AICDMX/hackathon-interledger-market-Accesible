FROM node:20-alpine AS base
WORKDIR /app

# Install production deps
FROM base AS deps
COPY package.json ./
RUN npm install --omit=dev

# Build stage with dev deps
FROM base AS build
COPY package.json ./
RUN npm install
COPY tsconfig.json ./
COPY . .
RUN npm run build

# Runtime image
FROM base AS runner
ENV NODE_ENV=production
COPY --from=deps /app/node_modules ./node_modules
COPY --from=build /app/dist ./dist
COPY --from=build /app/private.key ./private.key
USER node
ENV PORT=3000
EXPOSE 3000
CMD ["node", "dist/index.js"]


