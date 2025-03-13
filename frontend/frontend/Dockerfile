# Step 1: Build the React app
FROM node:18 AS build

WORKDIR /app

# Copy package.json and yarn.lock
COPY package.json yarn.lock ./

# Install dependencies
RUN yarn install

# Copy the entire project
COPY . .

# Build the React app (this creates the 'build/' folder)
RUN yarn build

# Step 2: Serve with Nginx
FROM nginx:alpine

# Copy build files to Nginx directory
COPY --from=build /app/build /usr/share/nginx/html

# Expose port 80
EXPOSE 80

# Start Nginx
CMD ["nginx", "-g", "daemon off;"]
