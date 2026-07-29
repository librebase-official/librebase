# Placeholder — build with `npm run build && npm start` in data-studio-ui for now.
FROM node:22-alpine
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci
COPY . .
RUN npm run build
EXPOSE 54324
CMD ["npm", "start"]
