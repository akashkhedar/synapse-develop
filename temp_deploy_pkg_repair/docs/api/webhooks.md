# Webhooks

Receive real-time notifications when events occur in your Synapse projects.

## Overview

Webhooks allow you to receive HTTP POST requests when specific events happen, enabling you to:

- Get notified when projects complete
- Track real-time progress
- Trigger ML training pipelines automatically
- Sync annotation data to your systems
- Build custom dashboards

---

## Quick Start

```python
import synapse

client = synapse.Client(api_key="sk_live_xxxx")

# Create a webhook
webhook = client.webhooks.create(
    url="https://api.yourapp.com/webhooks/synapse",
    events=["project.completed", "export.ready"],
    secret="whsec_your_secret_key"
)

print(f"Webhook ID: {webhook.id}")
print(f"Webhook URL: {webhook.url}")
```

---

## Creating Webhooks

### client.webhooks.create()

```python
webhook = client.webhooks.create(
    url: str,                    # Your endpoint URL
    events: list[str],           # Events to subscribe to
    project_id: str = None,      # Specific project (optional)
    secret: str = None,          # Signing secret (optional)
    description: str = None,     # Description
    enabled: bool = True         # Enable/disable
)
```

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `url` | `str` | ✅ | HTTPS endpoint to receive webhooks |
| `events` | `list[str]` | ✅ | List of events to subscribe to |
| `project_id` | `str` | ❌ | Limit to specific project |
| `secret` | `str` | ❌ | Secret for signature verification |
| `description` | `str` | ❌ | Human-readable description |
| `enabled` | `bool` | ❌ | Whether webhook is active |

### Examples

```python
# Subscribe to all project events
webhook = client.webhooks.create(
    url="https://api.yourapp.com/webhooks/synapse",
    events=["project.*"],
    secret="whsec_xxxxxxxxxxxx"
)

# Subscribe to specific project only
webhook = client.webhooks.create(
    url="https://api.yourapp.com/webhooks/synapse",
    events=["task.completed", "project.completed"],
    project_id="proj_abc123"
)

# Multiple endpoints for different events
client.webhooks.create(
    url="https://slack.yourapp.com/notify",
    events=["project.completed"]
)

client.webhooks.create(
    url="https://ml.yourapp.com/trigger",
    events=["export.ready"]
)
```

---

## Webhook Events

### Project Events

| Event | Description | Payload |
|-------|-------------|---------|
| `project.created` | New project created | Project details |
| `project.started` | Project annotation started | Project details |
| `project.completed` | All tasks completed | Final stats |
| `project.paused` | Project paused | Reason, stats |
| `project.resumed` | Project resumed | Stats |
| `project.cancelled` | Project cancelled | Refund info |

### Task Events

| Event | Description | Payload |
|-------|-------------|---------|
| `task.completed` | Single task completed | Task result |
| `task.reviewed` | Task passed expert review | Review details |
| `task.disputed` | Task flagged for review | Dispute reason |

### Export Events

| Event | Description | Payload |
|-------|-------------|---------|
| `export.ready` | Export file ready | Download URL |
| `export.failed` | Export failed | Error details |

### Billing Events

| Event | Description | Payload |
|-------|-------------|---------|
| `payment.received` | Payment successful | Amount, method |
| `payment.failed` | Payment failed | Error |
| `payment.refunded` | Refund processed | Amount, reason |
| `credits.low` | Low credit balance | Balance |

### Wildcard Events

```python
# Subscribe to all events of a type
events=["project.*"]    # All project events
events=["task.*"]       # All task events
events=["*"]            # All events (not recommended)
```

---

## Webhook Payload

All webhooks are sent as HTTP POST requests with JSON body.

### Headers

```http
POST /webhooks/synapse HTTP/1.1
Host: api.yourapp.com
Content-Type: application/json
X-Synapse-Signature: sha256=abc123...
X-Synapse-Event: project.completed
X-Synapse-Delivery: evt_abc123
X-Synapse-Timestamp: 1673612400
User-Agent: Synapse-Webhook/1.0
```

### Body Structure

```json
{
  "id": "evt_abc123def456",
  "type": "project.completed",
  "created_at": "2025-01-13T14:30:00Z",
  "api_version": "2025-01-01",
  "data": {
    // Event-specific data
  }
}
```

### Event Payloads

#### project.completed

```json
{
  "id": "evt_abc123",
  "type": "project.completed",
  "created_at": "2025-01-13T14:30:00Z",
  "data": {
    "project_id": "proj_abc123",
    "project_name": "Image Classification",
    "total_tasks": 1000,
    "completed_tasks": 1000,
    "quality_metrics": {
      "average_agreement": 0.89,
      "expert_review_rate": 0.05
    },
    "started_at": "2025-01-10T10:00:00Z",
    "completed_at": "2025-01-13T14:30:00Z",
    "turnaround_hours": 76.5
  }
}
```

#### task.completed

```json
{
  "id": "evt_def456",
  "type": "task.completed",
  "created_at": "2025-01-13T14:25:00Z",
  "data": {
    "project_id": "proj_abc123",
    "task_id": "task_xyz789",
    "result": {
      "classification": {
        "label": "dog",
        "confidence": 0.95
      }
    },
    "annotator_count": 3,
    "agreement_score": 1.0,
    "completed_count": 950,
    "total_count": 1000,
    "progress_percentage": 95.0
  }
}
```

#### export.ready

```json
{
  "id": "evt_ghi789",
  "type": "export.ready",
  "created_at": "2025-01-13T14:35:00Z",
  "data": {
    "project_id": "proj_abc123",
    "export_id": "exp_xyz123",
    "format": "coco",
    "download_url": "https://synapse.io/exports/exp_xyz123/download",
    "expires_at": "2025-01-20T14:35:00Z",
    "file_size_bytes": 15234567,
    "task_count": 1000
  }
}
```

#### payment.received

```json
{
  "id": "evt_pay123",
  "type": "payment.received",
  "created_at": "2025-01-10T10:00:00Z",
  "data": {
    "payment_id": "pay_abc123",
    "project_id": "proj_abc123",
    "amount": 1500.00,
    "currency": "INR",
    "payment_method": "razorpay",
    "type": "deposit"
  }
}
```

---

## Verifying Signatures

Always verify webhook signatures to ensure requests are from Synapse.

### Python

```python
import hmac
import hashlib
from flask import Flask, request, jsonify

WEBHOOK_SECRET = "whsec_xxxxxxxxxxxx"

app = Flask(__name__)

@app.route("/webhooks/synapse", methods=["POST"])
def handle_webhook():
    # Get signature from header
    signature = request.headers.get("X-Synapse-Signature", "")
    timestamp = request.headers.get("X-Synapse-Timestamp", "")
    payload = request.get_data()
    
    # Compute expected signature
    signed_payload = f"{timestamp}.{payload.decode()}"
    expected_sig = "sha256=" + hmac.new(
        WEBHOOK_SECRET.encode(),
        signed_payload.encode(),
        hashlib.sha256
    ).hexdigest()
    
    # Verify (use constant-time comparison)
    if not hmac.compare_digest(signature, expected_sig):
        return jsonify({"error": "Invalid signature"}), 401
    
    # Verify timestamp (prevent replay attacks)
    import time
    if abs(time.time() - int(timestamp)) > 300:  # 5 minute tolerance
        return jsonify({"error": "Timestamp too old"}), 401
    
    # Process the event
    event = request.json
    handle_event(event)
    
    return jsonify({"received": True}), 200

def handle_event(event):
    event_type = event["type"]
    data = event["data"]
    
    if event_type == "project.completed":
        trigger_ml_pipeline(data["project_id"])
    elif event_type == "task.completed":
        update_progress_dashboard(data)
    elif event_type == "export.ready":
        download_annotations(data["download_url"])
```

### Using SDK Helper

```python
import synapse

@app.route("/webhooks/synapse", methods=["POST"])
def handle_webhook():
    payload = request.get_data()
    signature = request.headers.get("X-Synapse-Signature")
    timestamp = request.headers.get("X-Synapse-Timestamp")
    
    try:
        event = synapse.webhooks.verify(
            payload=payload,
            signature=signature,
            timestamp=timestamp,
            secret="whsec_xxxxxxxxxxxx"
        )
        
        # Event is verified and parsed
        handle_event(event)
        return jsonify({"received": True})
        
    except synapse.errors.WebhookSignatureError:
        return jsonify({"error": "Invalid signature"}), 401
    except synapse.errors.WebhookTimestampError:
        return jsonify({"error": "Timestamp expired"}), 401
```

---

## Managing Webhooks

### List Webhooks

```python
webhooks = client.webhooks.list()

for webhook in webhooks:
    print(f"{webhook.id}: {webhook.url}")
    print(f"  Events: {webhook.events}")
    print(f"  Enabled: {webhook.enabled}")
```

### Get Webhook

```python
webhook = client.webhooks.get("whk_abc123")
```

### Update Webhook

```python
webhook.update(
    events=["project.completed"],  # Change subscribed events
    enabled=True
)

# Or directly
client.webhooks.update("whk_abc123", enabled=False)
```

### Delete Webhook

```python
client.webhooks.delete("whk_abc123")
```

### Test Webhook

Send a test event to verify your endpoint.

```python
result = client.webhooks.test("whk_abc123")
print(f"Test result: {result.status}")  # success or failed
print(f"Response code: {result.response_code}")
print(f"Response time: {result.response_time_ms}ms")
```

---

## Webhook Logs

View delivery history for a webhook.

```python
logs = client.webhooks.logs(
    webhook_id="whk_abc123",
    limit=100,
    status="failed"  # Filter: "success", "failed", or None for all
)

for log in logs:
    print(f"{log.event_type} at {log.created_at}")
    print(f"  Status: {log.status}")
    print(f"  Response: {log.response_code}")
    print(f"  Duration: {log.duration_ms}ms")
    
    if log.status == "failed":
        print(f"  Error: {log.error}")
```

---

## Retry Policy

Synapse retries failed webhook deliveries with exponential backoff:

| Attempt | Delay |
|---------|-------|
| 1 | Immediate |
| 2 | 1 minute |
| 3 | 5 minutes |
| 4 | 30 minutes |
| 5 | 2 hours |
| 6 | 8 hours |
| 7 | 24 hours |

After 7 failed attempts, the webhook is marked as failed and won't be retried.

### Success Criteria

A webhook delivery is considered successful if:
- Response status code is 2xx (200-299)
- Response is received within 30 seconds

---

## Best Practices

### 1. Respond Quickly

Return a 200 response immediately and process asynchronously.

```python
from threading import Thread

@app.route("/webhooks/synapse", methods=["POST"])
def handle_webhook():
    event = request.json
    
    # Respond immediately
    Thread(target=process_event, args=(event,)).start()
    
    return jsonify({"received": True}), 200

def process_event(event):
    # Heavy processing happens here
    if event["type"] == "project.completed":
        download_and_train(event["data"]["project_id"])
```

### 2. Handle Duplicates

Webhook deliveries may be duplicated. Use the event ID for idempotency.

```python
import redis

redis_client = redis.Redis()

def handle_webhook():
    event = request.json
    event_id = event["id"]
    
    # Check if already processed
    if redis_client.get(f"webhook:{event_id}"):
        return jsonify({"received": True})  # Already processed
    
    # Mark as processing
    redis_client.setex(f"webhook:{event_id}", 86400, "processing")
    
    # Process event
    process_event(event)
    
    return jsonify({"received": True})
```

### 3. Verify Signatures

Always verify webhook signatures in production.

### 4. Use HTTPS

Webhook endpoints must use HTTPS in production.

### 5. Handle All Event Types

Include a default handler for unknown events.

```python
def handle_event(event):
    handlers = {
        "project.completed": handle_project_completed,
        "task.completed": handle_task_completed,
        "export.ready": handle_export_ready,
    }
    
    handler = handlers.get(event["type"], handle_unknown_event)
    handler(event["data"])

def handle_unknown_event(data):
    logging.warning(f"Received unknown event type")
```

### 6. Queue for Processing

Use a message queue for reliable processing.

```python
from celery import Celery

celery = Celery('tasks', broker='redis://localhost:6379')

@app.route("/webhooks/synapse", methods=["POST"])
def handle_webhook():
    event = request.json
    
    # Queue for async processing
    process_webhook_event.delay(event)
    
    return jsonify({"received": True})

@celery.task
def process_webhook_event(event):
    # Process with retries, error handling, etc.
    pass
```

---

## Example Integrations

### Slack Notification

```python
import requests

def notify_slack(project_name, stats):
    webhook_url = "https://hooks.slack.com/services/xxx/xxx/xxx"
    
    message = {
        "blocks": [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": f"✅ Project Complete: {project_name}"
                }
            },
            {
                "type": "section",
                "fields": [
                    {"type": "mrkdwn", "text": f"*Tasks:* {stats['total_tasks']}"},
                    {"type": "mrkdwn", "text": f"*Quality:* {stats['quality']:.1%}"}
                ]
            }
        ]
    }
    
    requests.post(webhook_url, json=message)
```

### Trigger ML Training

```python
def trigger_training_pipeline(project_id):
    import boto3
    
    # Get annotations
    project = client.projects.get(project_id)
    export_result = project.export_to_s3(
        bucket="ml-training-data",
        key=f"datasets/{project_id}/annotations.json",
        format="coco"
    )
    
    # Trigger SageMaker training job
    sagemaker = boto3.client('sagemaker')
    sagemaker.create_training_job(
        TrainingJobName=f"train-{project_id}",
        AlgorithmSpecification={...},
        InputDataConfig=[{
            "ChannelName": "annotations",
            "DataSource": {
                "S3DataSource": {
                    "S3Uri": f"s3://ml-training-data/datasets/{project_id}/"
                }
            }
        }],
        ...
    )
```

---

## Troubleshooting

### Webhook Not Receiving Events

1. Check webhook is enabled: `webhook.enabled == True`
2. Verify URL is accessible from internet
3. Check firewall allows Synapse IPs
4. Verify SSL certificate is valid
5. Check webhook logs for errors

### Signature Verification Failing

1. Ensure you're using the correct secret
2. Verify timestamp is being included in signature
3. Check payload is raw bytes (not parsed JSON)
4. Ensure constant-time comparison

### Events Arriving Late

1. Check your endpoint response time (<30s required)
2. Events may be queued during high load
3. Use `created_at` timestamp, not delivery time

### Missing Events

1. Check if webhook was disabled after failures
2. Verify event type is subscribed
3. Check project_id filter if applicable
