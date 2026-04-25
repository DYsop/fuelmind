FROM node:20-alpine AS build

WORKDIR /app
COPY package.json tsconfig.json tsconfig.app.json vite.config.ts ./
RUN npm install
COPY index.html ./
COPY public ./public
COPY src ./src
RUN npm run build

FROM nginx:1.27-alpine

RUN apk add --no-cache gettext

COPY --from=build /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY entrypoint.sh /entrypoint.sh
COPY public/config.template.js /usr/share/nginx/html/config.template.js

RUN chmod +x /entrypoint.sh

EXPOSE 80

ENTRYPOINT ["/entrypoint.sh"]
CMD ["nginx", "-g", "daemon off;"]

