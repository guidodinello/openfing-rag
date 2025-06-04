# 📦 Project Setup

## Prerequisites
Make sure you have the following installed:
- [Node.js](https://nodejs.org/) (LTS recommended)
- [Yarn 1.22.22](https://classic.yarnpkg.com/en/docs/install/) (Ensure you are using this version unless migrating to a newer one)

## 🚀 Installation

1. **Navigate to the frontend directory:**
   ```sh
   cd frontend
   ```

2. **Ensure you are using Yarn 1.22.22:**
   ```sh
   yarn -v
   ```
   If the version is different, downgrade to Yarn 1.22.22:
   ```sh
   yarn set version 1.22.22
   ```

3. **Install dependencies:**
   ```sh
   yarn install
   ```

4. **Create the React app (only for first-time setup):**
   ```sh
   yarn create react-app frontend
   ```
   _Note: If the project is already initialized, this step is not needed._

## 🔥 Running the App

Once the setup is complete, start the development server:
```sh
yarn start
```

This will launch the app on `http://localhost:3000/`. 🚀



## Correr database con nuestro docker compose

```
cd docker/
docker compose --env-file ../backend/.env up -d database
```

```
cd backend/database
python main.py
```
