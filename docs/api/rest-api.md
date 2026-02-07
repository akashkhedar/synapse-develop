# REST API Reference

Direct REST API endpoints for clients who prefer HTTP calls over the SDK.

> Last Updated: February 7, 2026

> **Tip:** We recommend using the [Python SDK](sdk-reference.md) for easier integration. This reference is for clients who need direct HTTP access.

## Base URL

```
Production: https://api.synapse.io/v1
Staging:    https://staging-api.synapse.io/v1
```

## Authentication

All requests require authentication via API key.

```bash
# Header authentication (recommended)
curl -H "Authorization: Token sk_live_xxxx" \
     https://api.synapse.io/v1/projects

# Query parameter (not recommended)
curl https://api.synapse.io/v1/projects?api_key=sk_live_xxxx
```

## Request Format

- Content-Type: `application/json`
- Accept: `application/json`

```bash
curl -X POST https://api.synapse.io/v1/projects \
     -H "Authorization: Token sk_live_xxxx" \
     -H "Content-Type: application/json" \
     -d '{"name": "My Project", "annotation_type": "classification"}'
```

## Response Format

All responses are JSON with consistent structure.

### Success Response

```json
{
  "data": { ... },
  "meta": {
    "request_id": "req_abc123"
  }
}
```

### Paginated Response

```json
{
  "data": [ ... ],
  "meta": {
    "page": 1,
    "page_size": 20,
    "total": 150,
    "total_pages": 8,
    "request_id": "req_abc123"
  }
}
```

### Error Response

```json
{
  "error": {
    "code": "validation_error",
    "message": "Invalid request parameters",
    "details": {
      "name": ["This field is required"]
    }
  },
  "meta": {
    "request_id": "req_abc123"
  }
}
```

---

## Projects

### List Projects

```http
GET /v1/projects
```

**Query Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `status` | string | Filter by status: `draft`, `active`, `completed`, `cancelled` |
| `page` | integer | Page number (default: 1) |
| `page_size` | integer | Items per page (default: 20, max: 100) |

**Response:**

```json
{
  "data": [
    {
      "id": "proj_abc123",
      "name": "Image Classification",
      "status": "active",
      "annotation_type": "classification",
      "progress": 45.5,
      "total_tasks": 1000,
      "completed_tasks": 455,
      "created_at": "2025-01-10T10:00:00Z"
    }
  ],
  "meta": {
    "page": 1,
    "page_size": 20,
    "total": 5
  }
}
```

---

### Create Project

```http
POST /v1/projects
```

**Request Body:**

```json
{
  "name": "Product Classification",
  "annotation_type": "classification",
  "data_type": "image",
  "labels": ["Electronics", "Clothing", "Food", "Other"],
  "description": "Classify product images",
  "instructions": "Select the most appropriate category...",
  "quality_settings": {
    "min_annotators": 3,
    "consensus_threshold": 0.66
  },
  "pricing_tier": "standard",
  "priority": "normal"
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `name` | string | ✅ | Project name |
| `annotation_type` | string/array | ✅ | Annotation type(s) |
| `data_type` | string | ❌ | `image`, `text`, `audio`, `video` (default: `image`) |
| `labels` | array/object | ❌ | Labels for annotation |
| `description` | string | ❌ | Project description |
| `instructions` | string | ❌ | Annotator instructions |
| `quality_settings` | object | ❌ | Quality control config |
| `pricing_tier` | string | ❌ | `economy`, `standard`, `premium` |
| `priority` | string | ❌ | `low`, `normal`, `high`, `urgent` |

**Response:**

```json
{
  "data": {
    "id": "proj_abc123",
    "name": "Product Classification",
    "status": "draft",
    "annotation_type": "classification",
    "labels": ["Electronics", "Clothing", "Food", "Other"],
    "created_at": "2025-01-13T10:00:00Z"
  }
}
```

---

### Get Project

```http
GET /v1/projects/{project_id}
```

**Response:**

```json
{
  "data": {
    "id": "proj_abc123",
    "name": "Product Classification",
    "status": "active",
    "annotation_type": "classification",
    "data_type": "image",
    "labels": ["Electronics", "Clothing", "Food", "Other"],
    "description": "Classify product images",
    "instructions": "...",
    "quality_settings": {
      "min_annotators": 3,
      "consensus_threshold": 0.66
    },
    "total_tasks": 1000,
    "completed_tasks": 455,
    "progress": 45.5,
    "estimated_completion": "2025-01-15T18:00:00Z",
    "quality_metrics": {
      "average_agreement": 0.87,
      "expert_review_rate": 0.05
    },
    "created_at": "2025-01-10T10:00:00Z",
    "started_at": "2025-01-10T12:00:00Z"
  }
}
```

---

### Update Project

```http
PATCH /v1/projects/{project_id}
```

**Request Body:**

```json
{
  "name": "Updated Name",
  "instructions": "Updated instructions",
  "priority": "high"
}
```

---

### Delete Project

```http
DELETE /v1/projects/{project_id}
```

---

### Project Actions

#### Start Project

```http
POST /v1/projects/{project_id}/start
```

#### Pause Project

```http
POST /v1/projects/{project_id}/pause
```

**Request Body:**

```json
{
  "reason": "Waiting for more data"
}
```

#### Resume Project

```http
POST /v1/projects/{project_id}/resume
```

#### Cancel Project

```http
POST /v1/projects/{project_id}/cancel
```

**Response:**

```json
{
  "data": {
    "refund_amount": 1200.00,
    "refund_status": "processing",
    "completed_tasks": 25,
    "cancelled_tasks": 75
  }
}
```

---

## Tasks

### Upload Tasks

```http
POST /v1/projects/{project_id}/tasks
```

**Request Body:**

```json
{
  "tasks": [
    {
      "data": {
        "image_url": "https://cdn.example.com/img1.jpg"
      },
      "metadata": {
        "source": "production",
        "priority": 1
      }
    },
    {
      "data": {
        "image_url": "https://cdn.example.com/img2.jpg"
      }
    }
  ]
}
```

**Response:**

```json
{
  "data": {
    "task_count": 2,
    "success_count": 2,
    "error_count": 0,
    "errors": []
  }
}
```

---

### Upload from S3

```http
POST /v1/projects/{project_id}/tasks/import/s3
```

**Request Body:**

```json
{
  "bucket": "my-bucket",
  "prefix": "images/products/",
  "file_types": ["jpg", "png"],
  "aws_access_key": "AKIAXXXXXXXX",
  "aws_secret_key": "...",
  "aws_region": "us-east-1"
}
```

---

### Upload from GCS

```http
POST /v1/projects/{project_id}/tasks/import/gcs
```

**Request Body:**

```json
{
  "bucket": "my-bucket",
  "prefix": "images/",
  "file_types": ["jpg", "png"],
  "credentials_json": "..."
}
```

---

### Upload from Azure

```http
POST /v1/projects/{project_id}/tasks/import/azure
```

**Request Body:**

```json
{
  "container": "my-container",
  "prefix": "images/",
  "file_types": ["jpg", "png"],
  "connection_string": "..."
}
```

---

### List Tasks

```http
GET /v1/projects/{project_id}/tasks
```

**Query Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `status` | string | Filter: `pending`, `in_progress`, `completed` |
| `page` | integer | Page number |
| `page_size` | integer | Items per page |

---

### Get Task

```http
GET /v1/projects/{project_id}/tasks/{task_id}
```

**Response:**

```json
{
  "data": {
    "id": "task_xyz789",
    "project_id": "proj_abc123",
    "status": "completed",
    "data": {
      "image_url": "https://cdn.example.com/img1.jpg"
    },
    "annotations": [
      {
        "id": "ann_001",
        "result": {
          "classification": {
            "label": "Electronics",
            "confidence": 0.95
          }
        },
        "created_at": "2025-01-13T14:00:00Z"
      }
    ],
    "consensus": {
      "label": "Electronics",
      "confidence": 0.95,
      "agreement": 1.0
    },
    "created_at": "2025-01-10T10:00:00Z",
    "completed_at": "2025-01-13T14:30:00Z"
  }
}
```

---

## Exports

### Create Export

```http
POST /v1/projects/{project_id}/exports
```

**Request Body:**

```json
{
  "format": "coco",
  "include_metadata": true,
  "only_completed": true
}
```

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `format` | string | `json` | Export format |
| `include_metadata` | boolean | `true` | Include task metadata |
| `only_completed` | boolean | `true` | Only completed tasks |

**Response:**

```json
{
  "data": {
    "id": "exp_abc123",
    "status": "processing",
    "format": "coco",
    "created_at": "2025-01-13T15:00:00Z"
  }
}
```

---

### Get Export Status

```http
GET /v1/exports/{export_id}
```

**Response:**

```json
{
  "data": {
    "id": "exp_abc123",
    "status": "ready",
    "format": "coco",
    "download_url": "https://synapse.io/exports/exp_abc123/download",
    "expires_at": "2025-01-20T15:00:00Z",
    "file_size_bytes": 15234567,
    "task_count": 1000
  }
}
```

---

### Download Export

```http
GET /v1/exports/{export_id}/download
```

Returns the export file directly.

---

### Export to S3

```http
POST /v1/projects/{project_id}/exports/s3
```

**Request Body:**

```json
{
  "bucket": "my-bucket",
  "key": "annotations/project_123.json",
  "format": "coco",
  "aws_access_key": "AKIAXXXXXXXX",
  "aws_secret_key": "..."
}
```

---

## Billing

### Get Balance

```http
GET /v1/billing/balance
```

**Response:**

```json
{
  "data": {
    "available": 5000.00,
    "pending": 500.00,
    "currency": "INR"
  }
}
```

---

### Calculate Deposit

```http
POST /v1/projects/{project_id}/deposit/calculate
```

**Response:**

```json
{
  "data": {
    "amount": 1500.00,
    "currency": "INR",
    "task_count": 100,
    "rate_per_task": 15.00,
    "breakdown": {
      "annotation_cost": 1200.00,
      "quality_assurance": 200.00,
      "platform_fee": 100.00
    }
  }
}
```

---

### Pay Deposit

```http
POST /v1/projects/{project_id}/deposit/pay
```

**Request Body:**

```json
{
  "payment_method": "credits",
  "auto_start": true
}
```

| Field | Type | Description |
|-------|------|-------------|
| `payment_method` | string | `credits`, `razorpay` |
| `auto_start` | boolean | Start project after payment |

**Response (credits):**

```json
{
  "data": {
    "payment_id": "pay_abc123",
    "status": "completed",
    "amount": 1500.00,
    "new_balance": 3500.00
  }
}
```

**Response (razorpay):**

```json
{
  "data": {
    "payment_id": "pay_abc123",
    "status": "pending",
    "checkout_url": "https://synapse.io/checkout/pay_abc123",
    "amount": 1500.00
  }
}
```

---

### Get Usage

```http
GET /v1/billing/usage
```

**Query Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `start_date` | string | ISO 8601 date |
| `end_date` | string | ISO 8601 date |

---

### Add Credits

```http
POST /v1/billing/credits
```

**Request Body:**

```json
{
  "amount": 10000.00,
  "payment_method": "razorpay"
}
```

---

## Webhooks

### List Webhooks

```http
GET /v1/webhooks
```

---

### Create Webhook

```http
POST /v1/webhooks
```

**Request Body:**

```json
{
  "url": "https://api.yourapp.com/webhooks/synapse",
  "events": ["project.completed", "export.ready"],
  "secret": "whsec_xxxxxxxxxxxx",
  "project_id": "proj_abc123"
}
```

---

### Update Webhook

```http
PATCH /v1/webhooks/{webhook_id}
```

---

### Delete Webhook

```http
DELETE /v1/webhooks/{webhook_id}
```

---

### Test Webhook

```http
POST /v1/webhooks/{webhook_id}/test
```

---

## User

### Get Current User

```http
GET /v1/me
```

**Response:**

```json
{
  "data": {
    "id": 123,
    "email": "user@company.com",
    "first_name": "John",
    "last_name": "Doe",
    "organization": {
      "id": 1,
      "name": "Acme Corp"
    },
    "credits_balance": 5000.00
  }
}
```

---

## Error Codes

| Code | HTTP Status | Description |
|------|-------------|-------------|
| `authentication_error` | 401 | Invalid or missing API key |
| `permission_denied` | 403 | Insufficient permissions |
| `not_found` | 404 | Resource not found |
| `validation_error` | 400 | Invalid request parameters |
| `rate_limit_exceeded` | 429 | Too many requests |
| `insufficient_credits` | 402 | Not enough credits |
| `server_error` | 500 | Internal server error |

---

## Rate Limits

| Endpoint Category | Limit |
|-------------------|-------|
| Projects | 100/minute |
| Tasks (upload) | 1000/minute |
| Tasks (read) | 500/minute |
| Exports | 10/minute |
| Webhooks | 100/minute |

Headers returned with each response:

```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1673612400
```

---

## Pagination

List endpoints support pagination:

```http
GET /v1/projects?page=2&page_size=50
```

Response includes pagination metadata:

```json
{
  "data": [...],
  "meta": {
    "page": 2,
    "page_size": 50,
    "total": 150,
    "total_pages": 3
  }
}
```

---

## Changelog

### 2025-01-01

- Initial API version
- Projects, Tasks, Exports, Billing endpoints
- Webhook support
- S3/GCS/Azure import
