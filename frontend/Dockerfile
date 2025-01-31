FROM node:20-slim

WORKDIR /app

# Install curl for health checks
RUN apt-get update && apt-get install -y --no-install-recommends curl && rm -rf /var/lib/apt/lists/*

# Install dependencies first for better caching
COPY package.json yarn.lock ./
RUN yarn install --frozen-lockfile && yarn cache clean

# Copy source code
COPY . .

ENV VITE_API_URL=http://localhost:8000
ENV NODE_ENV=development

EXPOSE 3000

# Start development server with host set to 0.0.0.0
CMD ["yarn", "dev", "--host"] 