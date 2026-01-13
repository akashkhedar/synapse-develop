# Synapse Python SDK Reference

Complete reference documentation for the Synapse Python SDK.

## Table of Contents

- [Client](#client)
- [Projects](#projects)
- [Tasks](#tasks)
- [Exports](#exports)
- [Webhooks](#webhooks)
- [Billing](#billing)
- [Error Handling](#error-handling)
- [Types & Models](#types--models)

---

## Client

The `Client` class is your entry point to the Synapse API.

### Constructor

```python
synapse.Client(
    api_key: str = None,
    base_url: str = "https://api.synapse.io",
    timeout: int = 30,
    max_retries: int = 3
)
```

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `api_key` | `str` | `None` | Your API key. If not provided, reads from `SYNAPSE_API_KEY` env var |
| `base_url` | `str` | `https://api.synapse.io` | API base URL |
| `timeout` | `int` | `30` | Request timeout in seconds |
| `max_retries` | `int` | `3` | Max retries for failed requests |

### Example

```python
import synapse

# Basic initialization
client = synapse.Client(api_key="sk_live_xxxx")

# With custom settings
client = synapse.Client(
    api_key="sk_live_xxxx",
    timeout=60,
    max_retries=5
)

# Access your account info
me = client.whoami()
print(f"Logged in as: {me.email}")
print(f"Organization: {me.organization.name}")
```

### Properties

| Property | Type | Description |
|----------|------|-------------|
| `projects` | `ProjectsClient` | Project management |
| `tasks` | `TasksClient` | Task management |
| `exports` | `ExportsClient` | Export management |
| `webhooks` | `WebhooksClient` | Webhook management |
| `billing` | `BillingClient` | Billing & credits |

### Methods

#### `whoami()`

Get information about the authenticated user.

```python
user = client.whoami()
```

**Returns**: `User` object

```python
User(
    id=123,
    email="user@company.com",
    first_name="John",
    last_name="Doe",
    organization=Organization(id=1, name="Acme Corp"),
    credits_balance=5000.00
)
```

---

## Projects

### projects.create()

Create a new annotation project.

```python
project = client.projects.create(
    name: str,
    annotation_type: str | list[str],
    labels: list[str] = None,
    description: str = None,
    instructions: str = None,
    data_type: str = "image",
    quality_settings: dict = None,
    pricing_tier: str = "standard",
    priority: str = "normal"
)
```

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `name` | `str` | ✅ | Project name |
| `annotation_type` | `str` or `list` | ✅ | Type of annotation (see [Annotation Types](#annotation-types)) |
| `labels` | `list[str]` | ❌ | Labels for classification/tagging |
| `description` | `str` | ❌ | Project description |
| `instructions` | `str` | ❌ | Instructions for annotators |
| `data_type` | `str` | ❌ | Data type: `image`, `text`, `audio`, `video`, `document` |
| `quality_settings` | `dict` | ❌ | Quality control configuration |
| `pricing_tier` | `str` | ❌ | `economy`, `standard`, `premium` |
| `priority` | `str` | ❌ | `low`, `normal`, `high`, `urgent` |

#### Annotation Types

| Type | Description | Data Types |
|------|-------------|------------|
| `classification` | Single-label classification | image, text, audio, video |
| `multi_classification` | Multi-label classification | image, text, audio, video |
| `bounding_box` | Rectangular bounding boxes | image, video |
| `polygon` | Polygon segmentation | image |
| `segmentation` | Pixel-level segmentation | image |
| `keypoint` | Keypoint detection | image, video |
| `ner` | Named entity recognition | text |
| `text_classification` | Text classification | text |
| `sentiment` | Sentiment analysis | text |
| `transcription` | Audio/video transcription | audio, video |
| `qa` | Question answering | text, document |

#### Quality Settings

```python
quality_settings = {
    "min_annotators": 3,           # Min annotators per task (1-5)
    "consensus_threshold": 0.66,   # Agreement threshold (0.5-1.0)
    "enable_expert_review": True,  # Expert review for disputes
    "honeypot_percentage": 5,      # % of honeypot tasks (0-20)
    "auto_approve_threshold": 0.9  # Auto-approve if agreement > threshold
}
```

#### Example

```python
# Simple classification project
project = client.projects.create(
    name="Product Categorization",
    annotation_type="classification",
    labels=["Electronics", "Clothing", "Food", "Other"]
)

# Complex multi-task project
project = client.projects.create(
    name="Medical Imaging Analysis",
    annotation_type=["classification", "bounding_box", "segmentation"],
    data_type="image",
    labels={
        "classification": ["Normal", "Abnormal"],
        "bounding_box": ["Lesion", "Nodule", "Mass"],
        "segmentation": ["Tumor", "Organ"]
    },
    instructions="""
    1. First classify the image as Normal or Abnormal
    2. If Abnormal, draw bounding boxes around all findings
    3. For confirmed masses, create segmentation masks
    """,
    quality_settings={
        "min_annotators": 5,
        "consensus_threshold": 0.8,
        "enable_expert_review": True
    },
    pricing_tier="premium",
    priority="high"
)
```

**Returns**: `Project` object

---

### projects.get()

Get a project by ID.

```python
project = client.projects.get(project_id: str | int)
```

**Returns**: `Project` object

---

### projects.list()

List all projects.

```python
projects = client.projects.list(
    status: str = None,      # Filter by status
    page: int = 1,
    page_size: int = 20
)
```

**Returns**: `PaginatedList[Project]`

```python
# Iterate through all projects
for project in client.projects.list():
    print(f"{project.name}: {project.progress}%")

# Filter by status
active_projects = client.projects.list(status="active")
```

---

### projects.delete()

Delete a project.

```python
client.projects.delete(project_id: str | int)
```

> ⚠️ **Warning**: This permanently deletes the project and all associated data.

---

## Project Object

The `Project` object represents an annotation project.

### Properties

| Property | Type | Description |
|----------|------|-------------|
| `id` | `str` | Project ID |
| `name` | `str` | Project name |
| `status` | `str` | Current status |
| `progress` | `float` | Completion percentage (0-100) |
| `total_tasks` | `int` | Total number of tasks |
| `completed_tasks` | `int` | Number of completed tasks |
| `created_at` | `datetime` | Creation timestamp |
| `updated_at` | `datetime` | Last update timestamp |
| `estimated_completion` | `datetime` | Estimated completion time |

### Methods

#### project.upload_tasks()

Upload tasks to the project.

```python
result = project.upload_tasks(
    tasks: list[dict],
    batch_size: int = 100
)
```

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `tasks` | `list[dict]` | ✅ | List of task data objects |
| `batch_size` | `int` | ❌ | Upload batch size (default: 100) |

```python
# Upload image URLs
tasks = [
    {"image_url": "https://cdn.example.com/img1.jpg", "id": "001"},
    {"image_url": "https://cdn.example.com/img2.jpg", "id": "002"},
]
result = project.upload_tasks(tasks)
print(f"Uploaded {result.task_count} tasks")

# Upload with metadata
tasks = [
    {
        "image_url": "https://cdn.example.com/img1.jpg",
        "metadata": {
            "source": "production",
            "category": "electronics",
            "priority": 1
        }
    }
]
```

**Returns**: `UploadResult`

```python
UploadResult(
    task_count=100,
    success_count=100,
    error_count=0,
    errors=[]
)
```

---

#### project.upload_from_s3()

Upload tasks directly from an S3 bucket.

```python
result = project.upload_from_s3(
    bucket: str,
    prefix: str = "",
    file_types: list[str] = ["jpg", "png", "jpeg"],
    aws_access_key: str = None,
    aws_secret_key: str = None,
    aws_region: str = "us-east-1"
)
```

```python
# Upload all images from S3 bucket
result = project.upload_from_s3(
    bucket="my-company-data",
    prefix="images/products/2025/",
    file_types=["jpg", "png"]
)

# With explicit credentials
result = project.upload_from_s3(
    bucket="my-company-data",
    prefix="images/",
    aws_access_key="AKIAXXXXXXXX",
    aws_secret_key="secret",
    aws_region="ap-south-1"
)
```

**Returns**: `UploadResult`

---

#### project.upload_from_gcs()

Upload tasks from Google Cloud Storage.

```python
result = project.upload_from_gcs(
    bucket: str,
    prefix: str = "",
    file_types: list[str] = ["jpg", "png"],
    credentials_json: str = None
)
```

---

#### project.upload_from_azure()

Upload tasks from Azure Blob Storage.

```python
result = project.upload_from_azure(
    container: str,
    prefix: str = "",
    file_types: list[str] = ["jpg", "png"],
    connection_string: str = None
)
```

---

#### project.calculate_deposit()

Calculate the required security deposit.

```python
deposit = project.calculate_deposit()
```

**Returns**: `DepositEstimate`

```python
DepositEstimate(
    amount=1500.00,
    currency="INR",
    task_count=100,
    rate_per_task=15.00,
    breakdown={
        "annotation_cost": 1200.00,
        "quality_assurance": 200.00,
        "platform_fee": 100.00
    }
)
```

---

#### project.pay_deposit()

Pay the security deposit to start the project.

```python
payment = project.pay_deposit(
    payment_method: str = "razorpay",  # or "credits", "saved_card"
    auto_start: bool = True
)
```

```python
# Pay with Razorpay (opens payment page)
payment = project.pay_deposit(payment_method="razorpay")
print(f"Payment URL: {payment.checkout_url}")

# Pay with account credits
payment = project.pay_deposit(payment_method="credits")

# Pay but don't auto-start
payment = project.pay_deposit(auto_start=False)
project.start()  # Start manually later
```

**Returns**: `Payment`

---

#### project.start()

Start the project (after deposit is paid).

```python
project.start()
```

---

#### project.pause()

Pause an active project.

```python
project.pause(reason: str = None)
```

---

#### project.resume()

Resume a paused project.

```python
project.resume()
```

---

#### project.cancel()

Cancel the project.

```python
result = project.cancel(reason: str = None)
```

**Returns**: `CancellationResult`

```python
CancellationResult(
    refund_amount=1200.00,
    refund_status="processing",
    completed_tasks=25,
    cancelled_tasks=75
)
```

---

#### project.get_status()

Get detailed project status.

```python
status = project.get_status()
```

**Returns**: `ProjectStatus`

```python
ProjectStatus(
    status="active",
    progress=45.5,
    total_tasks=1000,
    completed_tasks=455,
    pending_tasks=545,
    in_progress_tasks=23,
    in_review_tasks=12,
    is_complete=False,
    estimated_completion=datetime(2025, 1, 20, 14, 30),
    quality_metrics={
        "average_agreement": 0.87,
        "expert_review_rate": 0.05,
        "rejection_rate": 0.02
    }
)
```

---

#### project.get_progress()

Get simple progress percentage.

```python
progress = project.get_progress()  # Returns float: 0.0 - 100.0
```

---

#### project.is_complete()

Check if project is complete.

```python
if project.is_complete():
    annotations = project.export()
```

---

#### project.wait_for_completion()

Block until project is complete.

```python
project.wait_for_completion(
    poll_interval: int = 60,      # Check every N seconds
    timeout: int = None,          # Max wait time (None = infinite)
    callback: callable = None     # Called on each poll
)
```

```python
# Simple wait
project.wait_for_completion()

# With progress callback
def on_progress(status):
    print(f"Progress: {status.progress}%")

project.wait_for_completion(
    poll_interval=300,  # Check every 5 minutes
    callback=on_progress
)

# With timeout
try:
    project.wait_for_completion(timeout=86400)  # 24 hour timeout
except synapse.errors.TimeoutError:
    print("Project not completed within timeout")
```

---

#### project.export()

Export project annotations.

```python
annotations = project.export(
    format: str = "json",
    include_predictions: bool = False,
    include_metadata: bool = True,
    only_completed: bool = True
)
```

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `format` | `str` | `"json"` | Export format |
| `include_predictions` | `bool` | `False` | Include ML predictions |
| `include_metadata` | `bool` | `True` | Include task metadata |
| `only_completed` | `bool` | `True` | Only export completed tasks |

#### Export Formats

| Format | Description | Use Case |
|--------|-------------|----------|
| `json` | Synapse JSON format | General purpose |
| `coco` | COCO format | Object detection, segmentation |
| `yolo` | YOLO format | YOLO model training |
| `pascal_voc` | Pascal VOC XML | Object detection |
| `csv` | CSV format | Tabular data, classification |
| `jsonl` | JSON Lines | Streaming, large datasets |
| `spacy` | spaCy format | NLP/NER models |
| `conll` | CoNLL format | NER models |

```python
# Export as JSON
annotations = project.export(format="json")

# Export as COCO for object detection
coco_data = project.export(format="coco")
with open("annotations.json", "w") as f:
    json.dump(coco_data, f)

# Export as YOLO
yolo_data = project.export(format="yolo")
# Returns dict with images and labels directories

# Stream large exports
for batch in project.export_stream(format="jsonl", batch_size=1000):
    process_batch(batch)
```

**Returns**: Depends on format (dict, list, or file path)

---

#### project.export_to_s3()

Export annotations directly to S3.

```python
result = project.export_to_s3(
    bucket: str,
    key: str,
    format: str = "json",
    aws_access_key: str = None,
    aws_secret_key: str = None
)
```

```python
result = project.export_to_s3(
    bucket="my-ml-data",
    key="annotations/project_123/annotations.json",
    format="coco"
)
print(f"Exported to: s3://{result.bucket}/{result.key}")
```

---

#### project.get_tasks()

Get tasks from the project.

```python
tasks = project.get_tasks(
    status: str = None,     # Filter: "pending", "completed", "in_progress"
    page: int = 1,
    page_size: int = 100
)
```

**Returns**: `PaginatedList[Task]`

---

#### project.get_task()

Get a specific task.

```python
task = project.get_task(task_id: str | int)
```

**Returns**: `Task` object

---

#### project.add_labels()

Add labels to the project.

```python
project.add_labels(["New Label 1", "New Label 2"])
```

---

#### project.update()

Update project settings.

```python
project.update(
    name: str = None,
    instructions: str = None,
    priority: str = None
)
```

---

## Tasks

### Task Object

| Property | Type | Description |
|----------|------|-------------|
| `id` | `str` | Task ID |
| `data` | `dict` | Task data |
| `status` | `str` | Task status |
| `annotations` | `list[Annotation]` | Completed annotations |
| `created_at` | `datetime` | Creation time |
| `completed_at` | `datetime` | Completion time |

### Methods

#### task.get_annotations()

Get all annotations for a task.

```python
annotations = task.get_annotations()
```

#### task.get_consensus()

Get the consensus annotation.

```python
consensus = task.get_consensus()
```

---

## Exports

### client.exports.list()

List all exports.

```python
exports = client.exports.list(project_id: str = None)
```

### client.exports.get()

Get export by ID.

```python
export = client.exports.get(export_id: str)
```

### client.exports.download()

Download an export.

```python
data = client.exports.download(export_id: str)
```

---

## Webhooks

Register webhooks to receive real-time notifications.

### client.webhooks.create()

```python
webhook = client.webhooks.create(
    url: str,
    events: list[str],
    project_id: str = None,  # None = all projects
    secret: str = None       # For signature verification
)
```

#### Webhook Events

| Event | Description |
|-------|-------------|
| `project.started` | Project annotation started |
| `project.completed` | All tasks completed |
| `project.paused` | Project was paused |
| `task.completed` | Individual task completed |
| `task.reviewed` | Task passed expert review |
| `export.ready` | Export file is ready |
| `payment.received` | Payment received |
| `payment.refunded` | Refund processed |

```python
# Create webhook for project completion
webhook = client.webhooks.create(
    url="https://api.yourapp.com/webhooks/synapse",
    events=["project.completed", "export.ready"],
    secret="whsec_xxxxxxxxxxxx"
)

# Project-specific webhook
webhook = client.webhooks.create(
    url="https://api.yourapp.com/webhooks/synapse",
    events=["task.completed"],
    project_id="proj_abc123"
)
```

### Webhook Payload

```python
{
    "id": "evt_abc123",
    "type": "project.completed",
    "created_at": "2025-01-13T14:30:00Z",
    "data": {
        "project_id": "proj_abc123",
        "project_name": "Image Classification",
        "total_tasks": 1000,
        "completed_tasks": 1000
    }
}
```

### Verifying Webhook Signatures

```python
import synapse

def handle_webhook(request):
    payload = request.body
    signature = request.headers.get("X-Synapse-Signature")
    
    try:
        event = synapse.webhooks.verify_signature(
            payload=payload,
            signature=signature,
            secret="whsec_xxxxxxxxxxxx"
        )
        
        if event.type == "project.completed":
            project_id = event.data["project_id"]
            # Download annotations
            
    except synapse.errors.WebhookSignatureError:
        return Response(status=400)
```

---

## Billing

### client.billing.get_balance()

Get current credit balance.

```python
balance = client.billing.get_balance()
```

**Returns**: `Balance`

```python
Balance(
    available=5000.00,
    pending=500.00,
    currency="INR"
)
```

### client.billing.get_usage()

Get usage history.

```python
usage = client.billing.get_usage(
    start_date: datetime = None,
    end_date: datetime = None
)
```

### client.billing.add_credits()

Add credits to account.

```python
payment = client.billing.add_credits(
    amount: float,
    payment_method: str = "razorpay"
)
```

---

## Error Handling

### Exception Types

```python
import synapse

try:
    project = client.projects.create(name="Test")
except synapse.errors.AuthenticationError as e:
    # Invalid or expired API key
    print(f"Auth failed: {e}")
    
except synapse.errors.PermissionError as e:
    # Insufficient permissions
    print(f"Permission denied: {e}")
    
except synapse.errors.ValidationError as e:
    # Invalid request parameters
    print(f"Validation error: {e.errors}")
    
except synapse.errors.NotFoundError as e:
    # Resource not found
    print(f"Not found: {e}")
    
except synapse.errors.RateLimitError as e:
    # Rate limit exceeded
    print(f"Rate limited. Retry after {e.retry_after} seconds")
    
except synapse.errors.InsufficientCreditsError as e:
    # Not enough credits
    print(f"Need {e.required} credits, have {e.available}")
    
except synapse.errors.SynapseError as e:
    # Generic Synapse error
    print(f"Error: {e}")
```

### Retry Logic

The SDK automatically retries failed requests with exponential backoff:

```python
# Default retry configuration
client = synapse.Client(
    api_key="sk_live_xxxx",
    max_retries=3,  # Retry up to 3 times
    retry_on=[429, 500, 502, 503, 504]  # HTTP codes to retry
)
```

---

## Types & Models

### Project

```python
@dataclass
class Project:
    id: str
    name: str
    description: str
    status: str
    annotation_type: Union[str, List[str]]
    labels: List[str]
    data_type: str
    total_tasks: int
    completed_tasks: int
    progress: float
    created_at: datetime
    updated_at: datetime
    estimated_completion: Optional[datetime]
    quality_settings: QualitySettings
    pricing_tier: str
    priority: str
```

### Task

```python
@dataclass
class Task:
    id: str
    project_id: str
    data: Dict[str, Any]
    status: str
    annotations: List[Annotation]
    created_at: datetime
    completed_at: Optional[datetime]
```

### Annotation

```python
@dataclass
class Annotation:
    id: str
    task_id: str
    result: Dict[str, Any]
    annotator_id: str
    created_at: datetime
    is_consensus: bool
    confidence: float
```

### User

```python
@dataclass
class User:
    id: int
    email: str
    first_name: str
    last_name: str
    organization: Organization
    credits_balance: float
```

---

## Rate Limits

| Endpoint | Rate Limit |
|----------|-----------|
| Project operations | 100/minute |
| Task upload | 1000/minute |
| Export | 10/minute |
| Webhooks | 100/minute |

Rate limit headers are included in all responses:

```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1673612400
```
