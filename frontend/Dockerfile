# frontend/Dockerfile
# 阶段 1: 构建 Vue
FROM node:18-alpine AS builder
WORKDIR /app
COPY package*.json ./
RUN npm install
COPY . .
RUN npm run build

# 阶段 2: 部署到 Nginx
FROM nginx:alpine
# 覆盖默认的 Nginx 配置
COPY nginx.conf /etc/nginx/conf.d/default.conf
# 将阶段 1 打包出的 dist 文件复制到 Nginx 目录下
COPY --from=builder /app/dist /usr/share/nginx/html

EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]