# Backend API Contract

This document describes the current HTTP contract implemented by the backend code in `be/app`.

It is intentionally based on the code as it exists now, not on intended behavior from older notes or screenshots. Where the implementation has known gaps, they are called out explicitly.

## 1. Overview

- Base URL: `http://<host>:<port>`
- Default local port in development: `5000`
- Default container port in Docker: `8080`
- Content type: `application/json` unless stated otherwise
- Authentication: `Authorization: Bearer <access_token>` for protected endpoints
- CORS: enabled globally for all routes

## 2. Common Conventions

### 2.1 Error Response

Most application-layer errors use this JSON shape:

```json
{
  "error": "Human-readable message"
}
```

Typical status mapping:

| Status | Meaning |
|---|---|
| `400` | Validation error / invalid payload |
| `401` | Missing or invalid authentication |
| `403` | Authenticated but not allowed |
| `404` | Resource not found |
| `409` | Conflict, such as duplicate email |
| `500` | Unhandled server error |
| `503` | Infrastructure dependency unavailable, such as MongoDB |

If a protected endpoint is called without a bearer token, the response is:

```json
{
  "error": "Authorization token is missing"
}
```

### 2.2 Time Format

The API uses a mix of timestamp formats:

- Most user and sensor management responses use ISO 8601 UTC strings ending in `Z`
- Some prediction and sensor data endpoints return ISO-style strings generated from stored MongoDB values
- `GET /health` returns Mongo connection state without special date fields

### 2.3 Authentication and Roles

Protected endpoints require a bearer token returned by `POST /auth/login`.

Supported user roles:

- `ADMIN`
- `MANAGER`
- `USER`

Supported user statuses:

- `ACTIVE`
- `INACTIVE`

If `role` is omitted during registration, the backend defaults it to `MANAGER`.

### 2.4 Sensor Status Values

For create and update requests, the accepted values are:

- `ONLINE`
- `OFFLINE`

However, the sensor health service may also write `ERROR` directly into the database. In practice, read responses may therefore contain `ERROR` even though create/update validation does not accept it.

## 3. System Endpoints

### GET `/`

Returns a simple service status message.

Response `200`

```json
{
  "status": "ok",
  "message": "Backend is running"
}
```

### GET `/health`

Returns API health plus MongoDB connection state.

Response `200`

```json
{
  "status": "ok",
  "mongo": {
    "configured": true,
    "connected": true,
    "db_name": "dungne",
    "error": null
  }
}
```

Notes:

- `status` is `ok` when MongoDB is connected, or when MongoDB is intentionally not configured
- `status` is `degraded` when MongoDB is configured but not connected

## 4. Authentication API

Base path: `/auth`

### POST `/auth/register`

Creates a user account.

Request body:

```json
{
  "fullName": "Alice Nguyen",
  "email": "alice@example.com",
  "password": "secret123",
  "urlAvatar": "https://example.com/avatar.png",
  "phoneNumber": "0123456789",
  "role": "USER"
}
```

Required fields:

- `fullName`
- `email`
- `password`

Response `201`

```json
{
  "message": "User registered successfully",
  "user": {
    "id": "6813d17e8f1d9d8f8f8f8f8f",
    "_id": "6813d17e8f1d9d8f8f8f8f8f",
    "fullName": "Alice Nguyen",
    "email": "alice@example.com",
    "urlAvatar": "https://example.com/avatar.png",
    "role": "USER",
    "phoneNumber": "0123456789",
    "status": "ACTIVE",
    "createdAt": "2026-05-01T16:00:00.000Z",
    "updatedAt": "2026-05-01T16:00:00.000Z"
  }
}
```

Possible errors:

- `400` if payload is invalid
- `409` if email already exists

### POST `/auth/login`

Authenticates a user and returns an access token.

Request body:

```json
{
  "email": "alice@example.com",
  "password": "secret123"
}
```

Response `200`

```json
{
  "message": "Login successful",
  "access_token": "<jwt>",
  "user": {
    "id": "6813d17e8f1d9d8f8f8f8f8f",
    "_id": "6813d17e8f1d9d8f8f8f8f8f",
    "fullName": "Alice Nguyen",
    "email": "alice@example.com",
    "urlAvatar": "",
    "role": "MANAGER",
    "phoneNumber": "",
    "status": "ACTIVE",
    "createdAt": "2026-05-01T16:00:00.000Z",
    "updatedAt": "2026-05-01T16:00:00.000Z"
  }
}
```

Possible errors:

- `400` if `email` or `password` is missing
- `401` if credentials are invalid
- `403` if the user is inactive

### POST `/auth/logout`

Protected: yes

Stateless logout. The server returns a message and expects the client to discard the token.

Response `200`

```json
{
  "message": "Logout successful. Remove the token on the client."
}
```

### GET `/auth/me`

Protected: yes

Returns the authenticated user.

Response `200`

```json
{
  "id": "6813d17e8f1d9d8f8f8f8f8f",
  "_id": "6813d17e8f1d9d8f8f8f8f8f",
  "fullName": "Alice Nguyen",
  "email": "alice@example.com",
  "urlAvatar": "",
  "role": "MANAGER",
  "phoneNumber": "",
  "status": "ACTIVE",
  "createdAt": "2026-05-01T16:00:00.000Z",
  "updatedAt": "2026-05-01T16:00:00.000Z"
}
```

### PATCH `/auth/password`

Protected: yes

Changes the authenticated user's password.

Request body:

```json
{
  "currentPassword": "secret123",
  "newPassword": "new-secret456"
}
```

Response `200`

```json
{
  "message": "Password changed successfully"
}
```

Possible errors:

- `400` if required fields are missing
- `401` if the current password is incorrect
- `404` if the current user no longer exists

### GET `/auth/users`

Protected: yes

Admin only.

Returns an array of users.

Response `200`

```json
[
  {
    "id": "6813d17e8f1d9d8f8f8f8f8f",
    "_id": "6813d17e8f1d9d8f8f8f8f8f",
    "fullName": "Alice Nguyen",
    "email": "alice@example.com",
    "urlAvatar": "",
    "role": "MANAGER",
    "phoneNumber": "",
    "status": "ACTIVE",
    "createdAt": "2026-05-01T16:00:00.000Z",
    "updatedAt": "2026-05-01T16:00:00.000Z"
  }
]
```

Possible errors:

- `403` if the caller is not an admin

### GET `/auth/users/{user_id}`

Protected: yes

Admin only.

Returns a single user.

Response `200`

```json
{
  "id": "6813d17e8f1d9d8f8f8f8f8f",
  "_id": "6813d17e8f1d9d8f8f8f8f8f",
  "fullName": "Alice Nguyen",
  "email": "alice@example.com",
  "urlAvatar": "",
  "role": "MANAGER",
  "phoneNumber": "",
  "status": "ACTIVE",
  "createdAt": "2026-05-01T16:00:00.000Z",
  "updatedAt": "2026-05-01T16:00:00.000Z"
}
```

### PATCH `/auth/users/{user_id}`

Protected: yes

Admin only. Partial update endpoint.

Request body:

```json
{
  "fullName": "Alice Updated",
  "phoneNumber": "0987654321",
  "urlAvatar": "https://example.com/avatar-2.png",
  "role": "ADMIN",
  "status": "ACTIVE"
}
```

Not allowed in this endpoint:

- `_id`
- `id`
- `email`
- `password`
- `passwordHash`
- `createdAt`

Response `200`

```json
{
  "id": "6813d17e8f1d9d8f8f8f8f8f",
  "_id": "6813d17e8f1d9d8f8f8f8f8f",
  "fullName": "Alice Updated",
  "email": "alice@example.com",
  "urlAvatar": "https://example.com/avatar-2.png",
  "role": "ADMIN",
  "phoneNumber": "0987654321",
  "status": "ACTIVE",
  "createdAt": "2026-05-01T16:00:00.000Z",
  "updatedAt": "2026-05-01T16:10:00.000Z"
}
```

Possible errors:

- `400` if no valid fields are provided
- `403` if the caller is not an admin
- `404` if the user does not exist

### DELETE `/auth/users/{user_id}`

Protected: yes

Admin only. This is a soft delete that sets user status to `INACTIVE`.

Response `200`

```json
{
  "id": "6813d17e8f1d9d8f8f8f8f8f",
  "_id": "6813d17e8f1d9d8f8f8f8f8f",
  "fullName": "Alice Nguyen",
  "email": "alice@example.com",
  "urlAvatar": "",
  "role": "MANAGER",
  "phoneNumber": "",
  "status": "INACTIVE",
  "createdAt": "2026-05-01T16:00:00.000Z",
  "updatedAt": "2026-05-01T16:20:00.000Z"
}
```

## 5. Sensor Station Management API

Base path: `/api/sensors`

All endpoints in this section are protected.

### POST `/api/sensors`

Creates a sensor station owned by the authenticated user.

Request body:

```json
{
  "sensorName": "Pond A",
  "location": {
    "longitude": 106.6297,
    "latitude": 10.8231
  },
  "status": "OFFLINE"
}
```

Rules:

- `location` is required
- `location.longitude` must be between `-180` and `180`
- `location.latitude` must be between `-90` and `90`
- `userId` must not be supplied by the client
- `status` defaults to `OFFLINE` if omitted

Response `201`

```json
{
  "message": "Sensor station created successfully",
  "sensor": {
    "_id": "6813d2e88f1d9d8f8f8f8f90",
    "sensorName": "Pond A",
    "userId": "6813d17e8f1d9d8f8f8f8f8f",
    "location": {
      "longitude": 106.6297,
      "latitude": 10.8231
    },
    "status": "OFFLINE",
    "isDeleted": false,
    "dateCreated": "2026-05-01T16:00:00.000Z",
    "lastDateUpdate": "2026-05-01T16:00:00.000Z"
  }
}
```

### GET `/api/sensors`

Lists sensor stations for the authenticated user.

Query parameters:

| Name | Type | Default | Notes |
|---|---|---|---|
| `page` | integer | `1` | Must be positive |
| `limit` | integer | `10` | Must be positive; effective maximum is `100` |
| `status` | string | none | Accepted values: `ONLINE`, `OFFLINE` |

Response `200`

```json
{
  "message": "Sensor stations fetched successfully",
  "data": [
    {
      "_id": "6813d2e88f1d9d8f8f8f8f90",
      "sensorName": "Pond A",
      "userId": "6813d17e8f1d9d8f8f8f8f8f",
      "location": {
        "longitude": 106.6297,
        "latitude": 10.8231
      },
      "status": "ONLINE",
      "isDeleted": false,
      "dateCreated": "2026-05-01T16:00:00.000Z",
      "lastDateUpdate": "2026-05-01T16:30:00.000Z"
    }
  ],
  "pagination": {
    "page": 1,
    "limit": 10,
    "total": 1,
    "totalPages": 1
  }
}
```

### GET `/api/sensors/{sensor_id}`

Returns a single sensor station belonging to the authenticated user.

Response `200`

```json
{
  "message": "Sensor station fetched successfully",
  "sensor": {
    "_id": "6813d2e88f1d9d8f8f8f8f90",
    "sensorName": "Pond A",
    "userId": "6813d17e8f1d9d8f8f8f8f8f",
    "location": {
      "longitude": 106.6297,
      "latitude": 10.8231
    },
    "status": "ONLINE",
    "isDeleted": false,
    "dateCreated": "2026-05-01T16:00:00.000Z",
    "lastDateUpdate": "2026-05-01T16:30:00.000Z"
  }
}
```

### PATCH `/api/sensors/{sensor_id}`

Partially updates a sensor station belonging to the authenticated user.

Request body:

```json
{
  "sensorName": "Pond A - West",
  "location": {
    "longitude": 106.63,
    "latitude": 10.82
  },
  "status": "ONLINE"
}
```

Rules:

- `location`, if provided, must be an object
- at least one updatable field must be present
- `userId` must not be supplied by the client

Response `200`

```json
{
  "message": "Sensor station updated successfully",
  "sensor": {
    "_id": "6813d2e88f1d9d8f8f8f8f90",
    "sensorName": "Pond A - West",
    "userId": "6813d17e8f1d9d8f8f8f8f8f",
    "location": {
      "longitude": 106.63,
      "latitude": 10.82
    },
    "status": "ONLINE",
    "isDeleted": false,
    "dateCreated": "2026-05-01T16:00:00.000Z",
    "lastDateUpdate": "2026-05-01T16:40:00.000Z"
  }
}
```

### DELETE `/api/sensors/{sensor_id}`

Soft deletes a sensor station belonging to the authenticated user.

Response `200`

```json
{
  "message": "Sensor station deleted successfully",
  "sensor": {
    "_id": "6813d2e88f1d9d8f8f8f8f90",
    "sensorName": "Pond A",
    "userId": "6813d17e8f1d9d8f8f8f8f8f",
    "location": {
      "longitude": 106.6297,
      "latitude": 10.8231
    },
    "status": "ONLINE",
    "isDeleted": true,
    "dateCreated": "2026-05-01T16:00:00.000Z",
    "lastDateUpdate": "2026-05-01T16:50:00.000Z"
  }
}
```

## 6. Sensor Data API

Base path: `/api/v1/sensors`

These endpoints are currently public.

### GET `/api/v1/sensors/latest`

Returns the latest sensor data document.

Query parameters:

| Name | Type | Required | Notes |
|---|---|---|---|
| `sensor_id` | string | no | If omitted, returns the latest document across all sensors |

Response `200`

```json
{
  "id": "6813d6108f1d9d8f8f8f8fa0",
  "sensor_id": "6813d2e88f1d9d8f8f8f8f90",
  "created_at": "2026-05-01T16:55:00+00:00",
  "quality_label": "Good",
  "quality_name": "Good Water",
  "solution": "Consider treatment.",
  "sensor_data": {
    "pH": 7.2,
    "Temp": 29.4,
    "DO": 6.8,
    "Turbidity": 12.1,
    "Hardness": 102.0,
    "Alkalinity": 95.0,
    "Ammonia": 0.1,
    "BOD": 2.3,
    "CO2": 4.4,
    "Calcium": 22.0,
    "H2S": 0.0,
    "Nitrite": 0.03,
    "Phosphorus": 0.2,
    "Plankton": 3.1
  }
}
```

Possible errors:

- `404` if no sensor data exists

### GET `/api/v1/sensors/classification`

Returns a classification view derived from the latest sensor data.

Query parameters:

| Name | Type | Required | Notes |
|---|---|---|---|
| `sensor_id` | string | no | If omitted, uses the latest document across all sensors |

Response `200`

```json
{
  "sensor_id": "6813d2e88f1d9d8f8f8f8f90",
  "created_at": "2026-05-01T16:55:00+00:00",
  "overall_quality": "Good Water",
  "hardness": {
    "category": "Moderately Hard",
    "value_mgl": 102.0,
    "threshold_mgl": 150.0
  },
  "salinity": {
    "level": "Slightly Saline",
    "turbidity_ntu": 12.1,
    "note": "Server-generated classification note"
  },
  "alkalinity": {
    "level": "Moderate",
    "value_mgl": 95.0,
    "safe_range": "80-120 mg/L"
  },
  "temperature": {
    "status": "Safe",
    "value_celsius": 29.4
  },
  "ph": 7.2,
  "do": 6.8
}
```

Possible errors:

- `404` if no sensor data exists

## 7. Analytics API

Base path: `/api/analytics`

All endpoints in this section are protected.

### GET `/api/analytics/trends`

Returns trend and comparison data for sensors owned by the authenticated user.

Query parameters:

| Name | Type | Required | Notes |
|---|---|---|---|
| `date` | `YYYY-MM-DD` | no | If omitted, the backend uses yesterday in the configured analytics timezone |

Response `200`

```json
{
  "userId": "6813d17e8f1d9d8f8f8f8f8f",
  "dateRange": {
    "startTime": "2026-05-01T00:00:00+07:00",
    "endTime": "2026-05-02T00:00:00+07:00"
  },
  "phTrend": [
    {
      "time": "00:00",
      "value": 7.12
    }
  ],
  "temperatureTrend": [
    {
      "time": "00:00",
      "value": 29.4
    }
  ],
  "conductivityTrend": [
    {
      "time": "00:00",
      "value": null
    }
  ],
  "dissolvedOxygenTrend": [
    {
      "time": "00:00",
      "value": 6.8
    }
  ],
  "turbidityComparison": [
    {
      "sensorId": "6813d2e88f1d9d8f8f8f8f90",
      "sensorName": "Pond A",
      "address": null,
      "value": 12.1
    }
  ]
}
```

Notes:

- Trend buckets are grouped into labeled times such as `00:00`, `04:00`, `08:00`, `12:00`, `16:00`, `20:00`, and `23:00`
- `conductivityTrend` may contain `null` values if the persisted data does not contain a conductivity field

Possible errors:

- `400` if `date` is not a valid `YYYY-MM-DD`

## 8. Prediction API

Base path: `/prediction`

These endpoints are currently public.

### GET `/prediction/test-db`

Declared route, but not currently production-ready.

Important note:

- The route calls `AIModelService.test_db()`
- That method does not exist in the current `AIModelService` implementation
- A runtime `500` is therefore expected until the method is implemented

### POST `/prediction/train`

Declared route, but not currently production-ready.

Supported request styles in the route:

- no file: intended to train from database
- multipart form upload with `file`: intended to train from an uploaded file

Important note:

- The route calls `AIModelService.train_model_from_db()`
- The route calls `AIModelService.train_model_from_file(file)`
- Neither method exists in the current `AIModelService` implementation
- A runtime `500` is therefore expected if this route is called, except for the explicit `400` case when an uploaded file name is empty

### POST `/prediction/predict`

Runs AI prediction on the provided sensor payload and stores the result.

Request body:

```json
{
  "sensorId": "6813d2e88f1d9d8f8f8f8f90",
  "Temp": 29.4,
  "Turbidity": 12.1,
  "DO": 6.8,
  "BOD": 2.3,
  "CO2": 4.4,
  "pH": 7.2,
  "Alkalinity": 95.0,
  "Hardness": 102.0,
  "Calcium": 22.0,
  "Ammonia": 0.1,
  "Nitrite": 0.03,
  "Phosphorus": 0.2,
  "H2S": 0.0,
  "Plankton": 3.1
}
```

Accepted sensor ID aliases:

- `sensorId`
- `idSensor`

Behavior notes:

- The route only validates that the top-level payload is a JSON object
- Missing numeric fields are treated as `0` by the AI model service
- If `sensorId` or `idSensor` is present, sensor health is updated
- If the payload includes `error`, or if all tracked sensor values are `0`, the route returns `400` instead of running prediction

Response `200`

```json
{
  "best_model": "RandomForest",
  "models": [
    {
      "model": "RandomForest",
      "accuracy": 0.94,
      "confidence": 91.3,
      "wqi": {
        "prediction": 1,
        "score": 76.4,
        "label": "Good"
      },
      "risk": {
        "status": "Medium Risk",
        "level": 1
      },
      "forecast_24h": {
        "trend": "Stable",
        "predicted_wqi_range": [73.4, 79.4],
        "model_used": "RandomForest",
        "confidence_score": 91.3
      }
    }
  ],
  "ensemble": {
    "wqi": {
      "score": 74.8,
      "label": "Good"
    },
    "risk": {
      "status": "Medium Risk",
      "level": 1
    },
    "confidence": 88.7,
    "forecast_24h": {
      "trend": "Stable",
      "predicted_wqi_range": [71.8, 77.8]
    }
  },
  "summary": {
    "wqi": {
      "prediction": 1,
      "score": 76.4,
      "label": "Good"
    },
    "risk": {
      "status": "Medium Risk",
      "level": 1
    },
    "accuracy": 0.94,
    "forecast_24h": {
      "trend": "Stable",
      "predicted_wqi_range": [73.4, 79.4],
      "model_used": "RandomForest",
      "confidence_score": 91.3
    },
    "confidence": 91.3,
    "solution": "Markdown text generated by the AI solution service.",
    "weather": {
      "has_rain": false,
      "total_precipitation_mm": 0,
      "avg_temperature_c": 29.0,
      "avg_cloud_cover_pct": 45,
      "max_wind_speed_kmh": 9,
      "avg_humidity_pct": 74,
      "max_uv_index": 7
    }
  }
}
```

Possible errors:

- `400` if payload is not a JSON object
- `400` if sensor error data is detected

### POST `/prediction/predict-with-time`

Same behavior as `/prediction/predict`, but allows the client to supply the event timestamp.

Required timestamp field:

- one of `createdAt`, `created_at`, `timestamp`, or `time`

Timestamp rules:

- must be an ISO 8601 datetime string
- if it ends with `Z`, the backend converts it to UTC

Request body:

```json
{
  "sensorId": "6813d2e88f1d9d8f8f8f8f90",
  "createdAt": "2026-05-01T16:55:00Z",
  "Temp": 29.4,
  "Turbidity": 12.1,
  "DO": 6.8,
  "BOD": 2.3,
  "CO2": 4.4,
  "pH": 7.2,
  "Alkalinity": 95.0,
  "Hardness": 102.0,
  "Calcium": 22.0,
  "Ammonia": 0.1,
  "Nitrite": 0.03,
  "Phosphorus": 0.2,
  "H2S": 0.0,
  "Plankton": 3.1
}
```

Response `200`

- Same shape as `POST /prediction/predict`

Possible errors:

- `400` if no accepted timestamp field is provided
- `400` if the timestamp is not a valid ISO 8601 datetime

### GET `/prediction/history`

Returns up to the latest 50 prediction records from the `predictions` collection.

Response `200`

```json
[
  {
    "id": "6813d7018f1d9d8f8f8f8fa1",
    "idSensor": "6813d2e88f1d9d8f8f8f8f90",
    "Temp": 29.4,
    "Turbidity": 12.1,
    "DO": 6.8,
    "BOD": 2.3,
    "CO2": 4.4,
    "pH": 7.2,
    "Alkalinity": 95.0,
    "Hardness": 102.0,
    "Calcium": 22.0,
    "Ammonia": 0.1,
    "Nitrite": 0.03,
    "Phosphorus": 0.2,
    "H2S": 0.0,
    "Plankton": 3.1,
    "prediction": {
      "best_model": "RandomForest"
    },
    "created_at": "2026-05-01T16:55:00+00:00"
  }
]
```

Possible errors:

- `500` if MongoDB is not connected

## 9. Alerts API

Base path: `/api/v1/alerts`

All endpoints in this section are protected.

### GET `/api/v1/alerts`

Returns alert items for sensors owned by the authenticated user.

Query parameters:

| Name | Type | Default | Notes |
|---|---|---|---|
| `status` | string | `unread` | Only `unread` triggers server-side filtering. Any other value effectively returns all matching alerts. |

Response `200`

```json
[
  {
    "id": "6813d8e78f1d9d8f8f8f8fb0",
    "wqi_score": 28.4,
    "contamination_risk": "High Risk",
    "message": "WQI: 28.4, Risk: High Risk",
    "status": "unread",
    "time_ago": "5 minute(s) ago",
    "created_at": "2026-05-01T16:55:00+00:00",
    "level": "Critical"
  }
]
```

Notes:

- If the authenticated user owns no sensors, the response is `[]`
- `level` is derived as follows:
  - `Critical` when `wqi_score < 30` or `contamination_risk == "Critical"`
  - `Warning` when `wqi_score < 50` or `contamination_risk == "High Risk"`
  - `Info` otherwise

### PUT `/api/v1/alerts/{alert_id}/read`

Marks an alert as read.

Response `200`

```json
{
  "message": "Alert marked as read"
}
```

Alternative successful response `200`

```json
{
  "message": "Alert was already marked as read"
}
```

Possible errors:

- `400` if the alert has no associated sensor
- `403` if the alert belongs to a sensor not owned by the current user
- `404` if the alert does not exist

### GET `/api/v1/alerts/settings/email`

Returns the current user's email notification preference.

Response `200`

```json
{
  "enabled": true
}
```

### PUT `/api/v1/alerts/settings/email`

Updates the current user's email notification preference.

Request body:

```json
{
  "enabled": false
}
```

Response `200`

```json
{
  "message": "Email alert settings updated successfully",
  "enabled": false
}
```

Possible errors:

- `400` if `enabled` is missing
- `404` if the current user does not exist

## 10. Known Implementation Gaps

These are important if this contract is used by frontend, QA, or integration partners:

1. `GET /prediction/test-db` is declared, but the backing service method does not exist yet.
2. `POST /prediction/train` is declared, but the backing service methods do not exist yet.
3. Sensor management validation only accepts `ONLINE` and `OFFLINE`, but background health monitoring may still store `ERROR` on sensor records.
4. The API uses mixed route prefixes: `/auth`, `/api/sensors`, `/api/v1/sensors`, `/api/analytics`, `/prediction`, and `/api/v1/alerts`.

## 11. Suggested Client Defaults

If you are building a frontend or integration against this backend, these defaults are safe:

1. Always send `Content-Type: application/json` except for file upload routes.
2. Always send `Authorization: Bearer <token>` for every protected route.
3. Treat every non-2xx response as a JSON object with an `error` field.
4. Expect both `id` and `_id` on user responses, but only `_id` on sensor responses.
5. Treat prediction and sensor timestamps as strings and parse them client-side.
