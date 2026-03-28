# Backend Auth API

Backend nay da duoc rut gon ve auth voi MongoDB va JWT.

## Folder structure

```text
app/
├── __init__.py
├── config.py
├── bootstrap/
│   └── container.py
├── domain/
│   ├── auth/
│   ├── sensor_station/
│   └── shared/
├── application/
│   ├── auth/
│   ├── sensor_station/
│   └── common/
├── infrastructure/
│   ├── persistence/
│   │   └── mongo/
│   └── security/
└── presentation/
    └── http/
        ├── middleware/
        ├── routes/
        ├── serializers/
        └── validators/
```

## Yeu cau

- Python 3.10+
- MongoDB Atlas hoac MongoDB server hop le

## Cau hinh

Cap nhat file `.env`:

```env
MONGO_URI=mongodb+srv://<user>:<password>@cluster0.od27giy.mongodb.net/?appName=Cluster0
MONGO_DB_NAME=dungne
JWT_SECRET_KEY=change-me
JWT_ACCESS_TOKEN_EXPIRES_MINUTES=60
```

## Cai dat va chay

```bash
cd /home/dungne/DADN/be
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python3 run.py
```

Server mac dinh chay tai `http://127.0.0.1:5000`.

## API

### Health

```bash
curl http://127.0.0.1:5000/health
```

### Register

```bash
curl -X POST http://127.0.0.1:5000/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "fullName": "Nguyen Van Chuyen Gia",
    "email": "chuyengia@water.com",
    "urlAvatar": "https://example.com/avatar.jpg",
    "password": "12345678",
    "role": "MANAGER",
    "phoneNumber": "0987654321"
  }'
```

Document luu vao collection `users` theo schema:

```json
{
  "fullName": "Nguyen Van Chuyen Gia",
  "email": "chuyengia@water.com",
  "urlAvatar": "https://example.com/avatar.jpg",
  "password": "$2b$10$...",
  "role": "MANAGER",
  "phoneNumber": "0987654321",
  "status": "ACTIVE",
  "createdAt": "2026-03-22T08:00:00.000Z",
  "updatedAt": "2026-03-22T08:00:00.000Z"
}
```

### Login

```bash
curl -X POST http://127.0.0.1:5000/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "chuyengia@water.com",
    "password": "12345678"
  }'
```

### Logout

```bash
curl -X POST http://127.0.0.1:5000/auth/logout \
  -H "Authorization: Bearer <jwt-token>"
```

### SensorStation

Tất cả API duoi day deu can `Authorization: Bearer <jwt-token>` va chi thao tac tren du lieu cua owner hien tai.

```bash
curl -X POST http://127.0.0.1:5000/api/sensors \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <jwt-token>" \
  -d '{
    "sensorName": "Tram quan trac Ho Tay",
    "location": {
      "longitude": 105.8188,
      "latitude": 21.0556
    },
    "status": "ONLINE"
  }'
```

```bash
curl -H "Authorization: Bearer <jwt-token>" \
  "http://127.0.0.1:5000/api/sensors?page=1&limit=10&status=ONLINE"
```

```bash
curl -H "Authorization: Bearer <jwt-token>" \
  http://127.0.0.1:5000/api/sensors/<sensor-id>
```

```bash
curl -X PATCH http://127.0.0.1:5000/api/sensors/<sensor-id> \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <jwt-token>" \
  -d '{
    "sensorName": "Tram quan trac Ho Tay 01",
    "status": "OFFLINE",
    "location": {
      "longitude": 105.82
    }
  }'
```

```bash
curl -X DELETE http://127.0.0.1:5000/api/sensors/<sensor-id> \
  -H "Authorization: Bearer <jwt-token>"
```
