FROM node:20-alpine

WORKDIR /app

# Install dependencies
COPY package.json ./
RUN npm install --omit=dev

# Copy app source
COPY server.js ./
COPY public ./public

# Expose port
EXPOSE 3000

# Run as non-root user (best practice, but app stays vulnerable)
RUN addgroup -g 1001 -S appuser && \
    adduser -S appuser -u 1001 -G appuser
USER appuser

# Start app
CMD ["node", "server.js"]
