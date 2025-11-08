# ============================================
# Dockerfile para Node.js Payment Service
# Open Payments API Wrapper para Interledger
# ============================================

# Usar imagen oficial de Node.js (LTS Alpine para menor tamaño)
FROM node:20-alpine

# Metadata
LABEL maintainer="Native Language Market"
LABEL description="Node.js microservice for Open Payments API integration"

# Crear directorio de la aplicación
WORKDIR /app

# Copiar archivos de dependencias primero (mejor cache de Docker)
COPY package*.json ./

# Instalar dependencias de producción
# --omit=dev solo instala production dependencies
RUN npm ci --omit=dev

# Copiar el resto del código
COPY . .

# Crear directorio para logs si es necesario
RUN mkdir -p /app/logs

# Variables de entorno por defecto (se pueden sobrescribir con docker-compose o -e)
ENV NODE_ENV=production
ENV PORT=3001

# Exponer el puerto del servicio
EXPOSE 3001

# Usuario no-root por seguridad (buena práctica)
USER node

# Health check (opcional, útil para orquestadores como Kubernetes)
HEALTHCHECK --interval=30s --timeout=3s --start-period=40s --retries=3 \
  CMD node -e "require('http').get('http://localhost:3001/health', (r) => {process.exit(r.statusCode === 200 ? 0 : 1)})"

# Comando por defecto para ejecutar la app
# Por ahora ejecuta index.js, pero cuando lo convirtamos a servicio Express
# será algo como: CMD ["node", "server.js"]
CMD ["node", "index.js"]
