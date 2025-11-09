FROM node:20-alpine AS build
WORKDIR /app

# Install all dependencies
COPY package*.json ./
RUN npm ci

# Build TypeScript
COPY tsconfig.json ./
COPY src ./src
RUN npm run build

# Production stage
FROM node:20-alpine AS production
WORKDIR /app
ENV NODE_ENV=production

# Copy package files and install only production dependencies
COPY package*.json ./
RUN npm ci --only=production

# Copy built application
COPY --from=build /app/dist ./dist

USER node
ENV PORT=3000
EXPOSE 3000
CMD ["node", "dist/src/index.js"]


