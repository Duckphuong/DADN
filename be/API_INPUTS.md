# API Input Documentation

Base URL local mac dinh:

```text
http://127.0.0.1:5000
```

Protected endpoints can header:

```http
Authorization: Bearer <access_token>
```

Token lay tu `POST /auth/login`.

## System

### GET /

Input: none.

### GET /health

Input: none.

## Auth

### POST /auth/register

Auth: none.

Content-Type:

```http
Content-Type: application/json
```

Body:

```json
{
  "fullName": "Nguyen Van A",
  "email": "user@example.com",
  "password": "secret",
  "urlAvatar": "https://example.com/avatar.png",
  "phoneNumber": "0900000000",
  "role": "MANAGER"
}
```

Fields:

| Field | Required | Type | Notes |
| --- | --- | --- | --- |
| `fullName` | yes | string | Must not be empty. |
| `email` | yes | string | Normalized to lowercase. |
| `password` | yes | string | Must not be empty. |
| `urlAvatar` | no | string | Defaults to empty string. |
| `phoneNumber` | no | string | Defaults to empty string. |
| `role` | no | string | `ADMIN`, `MANAGER`, or `USER`. Defaults to `MANAGER`. |

### POST /auth/login

Auth: none.

Content-Type:

```http
Content-Type: application/json
```

Body:

```json
{
  "email": "user@example.com",
  "password": "secret"
}
```

Fields:

| Field | Required | Type |
| --- | --- | --- |
| `email` | yes | string |
| `password` | yes | string |

### POST /auth/logout

Auth: required.

Input: none.

### GET /auth/me

Auth: required.

Input: none.

### PATCH /auth/password

Auth: required.

Content-Type:

```http
Content-Type: application/json
```

Body:

```json
{
  "currentPassword": "secret",
  "newPassword": "new-secret"
}
```

Fields:

| Field | Required | Type | Notes |
| --- | --- | --- | --- |
| `currentPassword` | yes | string | Must match the current password of the authenticated user. |
| `newPassword` | yes | string | Must not be empty. |

Notes:

- `userId` is taken from JWT.
- Do not pass `userId` in body or query params.

### GET /auth/users

Auth: required, admin only.

Input: none.

### GET /auth/users/<user_id>

Auth: required, admin only.

Path params:

| Param | Required | Type |
| --- | --- | --- |
| `user_id` | yes | string |

### PATCH /auth/users/<user_id>

Auth: required, admin only.

Path params:

| Param | Required | Type |
| --- | --- | --- |
| `user_id` | yes | string |

Content-Type:

```http
Content-Type: application/json
```

Body:

```json
{
  "fullName": "Nguyen Van A",
  "phoneNumber": "0900000000",
  "urlAvatar": "https://example.com/avatar.png",
  "role": "USER",
  "status": "ACTIVE"
}
```

Fields:

| Field | Required | Type | Notes |
| --- | --- | --- | --- |
| `fullName` | no | string | Must not be empty if provided. |
| `phoneNumber` | no | string | |
| `urlAvatar` | no | string | |
| `role` | no | string | `ADMIN`, `MANAGER`, or `USER`. |
| `status` | no | string | `ACTIVE` or `INACTIVE`. |

Forbidden body fields: `_id`, `id`, `email`, `password`, `passwordHash`, `createdAt`.

### DELETE /auth/users/<user_id>

Auth: required, admin only.

Path params:

| Param | Required | Type |
| --- | --- | --- |
| `user_id` | yes | string |

Body: none.

## Sensor Stations

### POST /api/sensors

Auth: required.

Content-Type:

```http
Content-Type: application/json
```

Body:

```json
{
  "sensorName": "Site A",
  "location": {
    "longitude": 106.700981,
    "latitude": 10.776889
  },
  "status": "ONLINE"
}
```

Fields:

| Field | Required | Type | Notes |
| --- | --- | --- | --- |
| `sensorName` | yes | string | Must not be empty. |
| `location` | yes | object | Required object. |
| `location.longitude` | yes | number | Must be between `-180` and `180`. |
| `location.latitude` | yes | number | Must be between `-90` and `90`. |
| `status` | no | string | `ONLINE` or `OFFLINE`. Defaults to `OFFLINE`. |

Forbidden body field: `userId`. Owner is always taken from JWT.

### GET /api/sensors

Auth: required.

Query params:

| Param | Required | Type | Default | Notes |
| --- | --- | --- | --- | --- |
| `page` | no | positive integer | `1` | |
| `limit` | no | positive integer | `10` | Max applied by use case: `100`. |
| `status` | no | string | none | `ONLINE` or `OFFLINE`. |

### GET /api/sensors/<sensor_id>

Auth: required.

Path params:

| Param | Required | Type |
| --- | --- | --- |
| `sensor_id` | yes | string |

Body: none.

### PATCH /api/sensors/<sensor_id>

Auth: required.

Path params:

| Param | Required | Type |
| --- | --- | --- |
| `sensor_id` | yes | string |

Content-Type:

```http
Content-Type: application/json
```

Body:

```json
{
  "sensorName": "Site A Updated",
  "location": {
    "longitude": 106.700981,
    "latitude": 10.776889
  },
  "status": "ONLINE"
}
```

Fields:

| Field | Required | Type | Notes |
| --- | --- | --- | --- |
| `sensorName` | no | string | Must not be empty if provided. |
| `location` | no | object | If provided, must be an object. |
| `location.longitude` | no | number | Used only when `location` is provided. |
| `location.latitude` | no | number | Used only when `location` is provided. |
| `status` | no | string | `ONLINE` or `OFFLINE`. |

At least one valid field is required.

Forbidden body field: `userId`. Owner is always taken from JWT.

### DELETE /api/sensors/<sensor_id>

Auth: required.

Path params:

| Param | Required | Type |
| --- | --- | --- |
| `sensor_id` | yes | string |

Body: none.

## Sensor Data

### GET /api/v1/sensors/latest

Auth: none in current route.

Query params:

| Param | Required | Type | Notes |
| --- | --- | --- | --- |
| `sensor_id` | no | string | If omitted, returns latest measurement globally. |

### GET /api/v1/sensors/classification

Auth: none in current route.

Query params:

| Param | Required | Type | Notes |
| --- | --- | --- | --- |
| `sensor_id` | no | string | If omitted, classifies latest measurement globally. |

## Analytics

### GET /api/analytics/trends?date=YYYY-MM-DD

Auth: required.

Query params:

| Param | Required | Type | Default | Notes |
| --- | --- | --- | --- | --- |
| `date` | no | string | yesterday | Date to fetch analytics for, format `YYYY-MM-DD`. |

Notes:

- `userId` is taken from the JWT token.
- Do not pass `userId` in query params.
- If `date` is omitted, backend keeps the current behavior and returns data for yesterday.
- Date range is calculated in application/server timezone unless `ANALYTICS_TIMEZONE` is configured.
- Analytics includes all non-deleted sensors of the authenticated user, regardless of `ONLINE` or `OFFLINE` status.

## Alerts

### GET /api/v1/alerts

Auth: required.

Query params:

| Param | Required | Type | Default | Notes |
| --- | --- | --- | --- | --- |
| `status` | no | string | `unread` | Current code filters only when value is exactly `unread`; other values return all matching alerts. |

### PUT /api/v1/alerts/<alert_id>/read

Auth: required.

Path params:

| Param | Required | Type |
| --- | --- | --- |
| `alert_id` | yes | string ObjectId |

Body: none.

### GET /api/v1/alerts/settings/email

Auth: required.

Input: none.

Response:
Returns the current email notification setting for the authenticated user.
```json
{
  "enabled": true
}
```

### PUT /api/v1/alerts/settings/email

Auth: required.

Content-Type:

```http
Content-Type: application/json
```

Body:

```json
{
  "enabled": false
}
```

Fields:

| Field | Required | Type | Notes |
| --- | --- | --- | --- |
| `enabled` | yes | boolean | True to enable email alerts, False to disable. |

## Prediction / AI

### GET /prediction/test-db

Auth: none in current route.

Input: none.

Implementation note: current route calls `AIModelService.test_db()`, but that method is not present in the current `AIModelService` code.

### POST /prediction/train

Auth: none in current route.

Input option 1: no body.

Input option 2: multipart form upload.

```http
Content-Type: multipart/form-data
```

Form fields:

| Field | Required | Type | Notes |
| --- | --- | --- | --- |
| `file` | no | file | If provided, filename must not be empty. |

Implementation note: current route calls `AIModelService.train_model_from_db()` when no file is provided and `AIModelService.train_model_from_file(file)` when file is provided. These methods are not present in the current `AIModelService` code.

### POST /prediction/predict

Auth: none in current route.

Content-Type:

```http
Content-Type: application/json
```

Body:

```json
{
  "sensorId": "sensor-id",
  "Temp": 25.1,
  "Turbidity": 2.5,
  "DO": 7.8,
  "BOD": 3.1,
  "CO2": 8.2,
  "pH": 7.2,
  "Alkalinity": 100,
  "Hardness": 180,
  "Calcium": 108,
  "Ammonia": 0.2,
  "Nitrite": 0.04,
  "Phosphorus": 1.2,
  "H2S": 0.01,
  "Plankton": 20
}
```

Fields:

| Field | Required | Type | Notes |
| --- | --- | --- | --- |
| `sensorId` | no | string | Used to update sensor health and create alert ownership link. |
| `idSensor` | no | string | Alternative sensor id input used only for sensor health check. |
| `Temp` | no | number | Defaults to `0` if omitted. |
| `Turbidity` | no | number | Defaults to `0` if omitted. |
| `DO` | no | number | Defaults to `0` if omitted. |
| `BOD` | no | number | Defaults to `0` if omitted. |
| `CO2` | no | number | Defaults to `0` if omitted. |
| `pH` | no | number | Defaults to `0` if omitted. |
| `Alkalinity` | no | number | Defaults to `0` if omitted. |
| `Hardness` | no | number | Defaults to `0` if omitted. |
| `Calcium` | no | number | Defaults to `0` if omitted. |
| `Ammonia` | no | number | Defaults to `0` if omitted. |
| `Nitrite` | no | number | Defaults to `0` if omitted. |
| `Phosphorus` | no | number | Defaults to `0` if omitted. |
| `H2S` | no | number | Defaults to `0` if omitted. |
| `Plankton` | no | number | Defaults to `0` if omitted. |

Route expects a JSON object. If `sensorId` or `idSensor` is provided and all sensor values are `0`, sensor health marks it as `ERROR` and the route returns `400`.

Server stores `created_at` using the current server time in UTC.
If `sensorId` or `idSensor` is a valid MongoDB ObjectId string, backend stores it in `predictions.idSensor` as an actual `ObjectId` and uses the same normalized reference for alerts.

### POST /prediction/predict-with-time

Auth: none in current route.

Content-Type:

```http
Content-Type: application/json
```

Body:

```json
{
  "sensorId": "sensor-id",
  "createdAt": "2026-04-24T08:30:00Z",
  "Temp": 25.1,
  "Turbidity": 2.5,
  "DO": 7.8,
  "BOD": 3.1,
  "CO2": 8.2,
  "pH": 7.2,
  "Alkalinity": 100,
  "Hardness": 180,
  "Calcium": 108,
  "Ammonia": 0.2,
  "Nitrite": 0.04,
  "Phosphorus": 1.2,
  "H2S": 0.01,
  "Plankton": 20
}
```

Fields:

| Field | Required | Type | Notes |
| --- | --- | --- | --- |
| `createdAt` | yes | string ISO 8601 | Timestamp to store into `predictions.created_at` and alert `created_at` / `updated_at`. |
| `created_at` | no | string ISO 8601 | Accepted alias of `createdAt`. |
| `timestamp` | no | string ISO 8601 | Accepted alias of `createdAt`. |
| `time` | no | string ISO 8601 | Accepted alias of `createdAt`. |
| `sensorId` | no | string | Used to update sensor health and create alert ownership link. |
| `idSensor` | no | string | Alternative sensor id input used only for sensor health check. |
| `Temp` | no | number | Defaults to `0` if omitted. |
| `Turbidity` | no | number | Defaults to `0` if omitted. |
| `DO` | no | number | Defaults to `0` if omitted. |
| `BOD` | no | number | Defaults to `0` if omitted. |
| `CO2` | no | number | Defaults to `0` if omitted. |
| `pH` | no | number | Defaults to `0` if omitted. |
| `Alkalinity` | no | number | Defaults to `0` if omitted. |
| `Hardness` | no | number | Defaults to `0` if omitted. |
| `Calcium` | no | number | Defaults to `0` if omitted. |
| `Ammonia` | no | number | Defaults to `0` if omitted. |
| `Nitrite` | no | number | Defaults to `0` if omitted. |
| `Phosphorus` | no | number | Defaults to `0` if omitted. |
| `H2S` | no | number | Defaults to `0` if omitted. |
| `Plankton` | no | number | Defaults to `0` if omitted. |

Notes:

- Route expects a JSON object.
- `createdAt` is the recommended field name. The other three names are accepted as aliases for compatibility.
- Datetime values are parsed as ISO 8601. If timezone is omitted, backend treats it as UTC.
- If `sensorId` or `idSensor` is a valid MongoDB ObjectId string, backend stores it in `predictions.idSensor` as an actual `ObjectId` and uses the same normalized reference for alerts.
- If `sensorId` or `idSensor` is provided and all sensor values are `0`, sensor health marks it as `ERROR` and the route returns `400`.

### GET /prediction/history

Auth: none in current route.

Input: none.
