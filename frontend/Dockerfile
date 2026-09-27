FROM node:18-alpine AS builder

WORKDIR /app

COPY package.json ./

RUN npm install

COPY . .

# ==========================================================
# React API URL
# This is embedded into the React production build.
# ==========================================================

ARG REACT_APP_API_URL=/api

ENV REACT_APP_API_URL=$REACT_APP_API_URL

# Build React application
RUN npm run build


# ==========================================================
# Production image
# ==========================================================

FROM node:18-alpine

WORKDIR /app

RUN npm install -g serve

COPY --from=builder /app/build ./build

EXPOSE 3000

CMD ["serve", "-s", "build", "-l", "3000"]