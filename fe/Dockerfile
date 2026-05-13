# Sử dụng node image chính thức
FROM node:20-alpine

WORKDIR /app

# Copy file package.json và cài đặt dependencies
COPY package*.json ./
RUN npm install

# Copy toàn bộ code
COPY . .

# Mở cổng 5173
EXPOSE 5173

# Chạy Vite với flag --host để Docker có thể truy cập được
CMD ["npm", "run", "dev", "--", "--host"]