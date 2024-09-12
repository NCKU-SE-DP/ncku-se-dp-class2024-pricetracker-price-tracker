# 使用官方的Node.js作為基礎映像
FROM node:lts-alpine

# 設定工作目錄
WORKDIR /app

# 複製`package.json`和`package-lock.json`（如果存在）
COPY package*.json ./

# 安裝專案依賴
RUN npm install

# 複製專案檔案到工作目錄
COPY . .

# 開放容器的8080端口
EXPOSE 8080

# 啟動Vue開發服務器
CMD ["npm", "run", "serve"]
