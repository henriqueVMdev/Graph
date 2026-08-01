FROM node:22-slim AS build

WORKDIR /app

COPY package.json package-lock.json ./
# Cache local do npm (BuildKit)
RUN --mount=type=cache,target=/root/.npm \
    npm ci

COPY index.html vite.config.js tailwind.config.js postcss.config.js ./
COPY src ./src
RUN npm run build

FROM nginx:alpine
COPY --from=build /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
