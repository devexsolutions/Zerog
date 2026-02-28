# Usa una imagen oficial de Node.js (Alpine es más ligera)
FROM node:20-alpine

# Establece el directorio de trabajo
WORKDIR /app

# Copia los archivos de dependencias
COPY package*.json ./

# Instala dependencias
RUN npm install

# Copia el código del frontend
COPY . .

# Argumento de construcción para la URL de la API
ARG NEXT_PUBLIC_API_URL=http://localhost:8000
ENV NEXT_PUBLIC_API_URL=$NEXT_PUBLIC_API_URL

# Construye la aplicación para producción
RUN npm run build

# Expone el puerto 3000
EXPOSE 3000

# Comando para correr la aplicación
CMD ["npm", "start"]
