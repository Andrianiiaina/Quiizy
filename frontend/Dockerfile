# ===== Stage 1 : dépendances (réutilisé aussi en dev pour le hot-reload) =====
FROM node:20-alpine AS deps

WORKDIR /app

COPY package.json ./
RUN npm install

# ===== Stage 2 : build de l'application React =====
FROM deps AS builder

COPY . .
RUN npm run build

# ===== Stage 3 : service Nginx avec les fichiers statiques =====
FROM nginx:alpine AS production

COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=builder /app/dist /usr/share/nginx/html

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
