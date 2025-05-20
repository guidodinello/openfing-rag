## Correr database con nuestro docker compose

```
cd docker/
docker compose --env-file ../backend/generative/.env up -d database
```

```
cd backend/database
python main.py
```
