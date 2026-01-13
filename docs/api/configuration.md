# Configuration & Advanced Settings

Advanced configuration options for the Synapse SDK and API.

## SDK Configuration

### Client Options

```python
import synapse

client = synapse.Client(
    # Required
    api_key="sk_live_xxxx",
    
    # Optional settings
    base_url="https://api.synapse.io",     # API endpoint
    timeout=30,                             # Request timeout (seconds)
    max_retries=3,                          # Retry attempts
    retry_on=[429, 500, 502, 503, 504],    # HTTP codes to retry
    
    # Logging
    log_level="INFO",                       # DEBUG, INFO, WARNING, ERROR
    log_requests=False,                     # Log all requests
    
    # Proxy settings
    proxy="http://proxy.company.com:8080",  # HTTP proxy
    verify_ssl=True                         # SSL verification
)
```

### Environment Variables

The SDK reads configuration from environment variables:

| Variable | Description | Default |
|----------|-------------|---------|
| `SYNAPSE_API_KEY` | API key for authentication | - |
| `SYNAPSE_BASE_URL` | API base URL | `https://api.synapse.io` |
| `SYNAPSE_TIMEOUT` | Request timeout in seconds | `30` |
| `SYNAPSE_MAX_RETRIES` | Max retry attempts | `3` |
| `SYNAPSE_LOG_LEVEL` | Logging level | `INFO` |
| `SYNAPSE_VERIFY_SSL` | Verify SSL certificates | `true` |
| `HTTP_PROXY` / `HTTPS_PROXY` | Proxy settings | - |

```bash
# Set in shell
export SYNAPSE_API_KEY=sk_live_xxxx
export SYNAPSE_TIMEOUT=60

# Or in .env file
SYNAPSE_API_KEY=sk_live_xxxx
SYNAPSE_LOG_LEVEL=DEBUG
```

```python
# SDK auto-reads from environment
client = synapse.Client()  # Uses SYNAPSE_API_KEY
```

---

## Project Quality Settings

### Consensus Settings

Control how multiple annotations are combined:

```python
project = client.projects.create(
    name="Quality Example",
    annotation_type="classification",
    labels=["A", "B", "C"],
    quality_settings={
        # Annotators per task
        "min_annotators": 3,          # Minimum (1-5)
        "max_annotators": 5,          # Maximum (optional)
        
        # Consensus threshold
        "consensus_threshold": 0.66,  # Agreement required (0.5-1.0)
        
        # Auto-approval
        "auto_approve_threshold": 0.9,  # Skip review if agreement > this
        
        # Expert review
        "enable_expert_review": True,   # Send disputes to experts
        "expert_review_threshold": 0.5, # Send if agreement < this
        
        # Honeypot tasks
        "honeypot_percentage": 5,       # % of tasks are honeypots (0-20)
        "honeypot_fail_threshold": 0.3  # Remove annotators below this
    }
)
```

### Quality Settings by Annotation Type

#### Bounding Box / Polygon

```python
quality_settings = {
    "min_annotators": 2,
    "consensus_threshold": 0.7,
    "enable_expert_review": True,
    
    # Spatial settings
    "iou_threshold": 0.5,           # IoU for box matching
    "nms_threshold": 0.4,           # Non-max suppression
    "min_box_area": 100,            # Minimum box size (pixels)
    "max_boxes_per_image": 100      # Limit boxes per image
}
```

#### Segmentation

```python
quality_settings = {
    "min_annotators": 2,
    "consensus_threshold": 0.8,
    "enable_expert_review": True,
    
    # Segmentation settings
    "iou_threshold": 0.7,           # Higher IoU for masks
    "dice_threshold": 0.75,         # DICE coefficient threshold
    "min_mask_area": 50             # Minimum mask size
}
```

#### Keypoints

```python
quality_settings = {
    "min_annotators": 3,
    "consensus_threshold": 0.7,
    
    # Keypoint settings
    "distance_threshold": 10,       # Max pixel distance for matching
    "pck_threshold": 0.2,           # PCK threshold (% of bbox)
    "min_visible_keypoints": 5      # Minimum visible keypoints
}
```

#### NER

```python
quality_settings = {
    "min_annotators": 2,
    "consensus_threshold": 0.8,
    
    # NER settings
    "token_overlap_threshold": 0.8, # Token-level overlap
    "exact_match": False,           # Require exact span match
    "label_match": True             # Require same label
}
```

---

## Priority Levels

Control annotation speed and pricing:

| Priority | Turnaround | Cost Multiplier | Use Case |
|----------|------------|-----------------|----------|
| `low` | 7+ days | 0.8x | Non-urgent, large batches |
| `normal` | 3-5 days | 1.0x | Standard projects |
| `high` | 1-2 days | 1.5x | Time-sensitive |
| `urgent` | <24 hours | 2.5x | Critical deadlines |

```python
project = client.projects.create(
    name="Urgent Project",
    annotation_type="classification",
    labels=["A", "B"],
    priority="urgent"
)
```

---

## Pricing Tiers

| Tier | Quality | Annotator Pool | Cost |
|------|---------|----------------|------|
| `economy` | Good | General pool | $ |
| `standard` | High | Verified annotators | $$ |
| `premium` | Highest | Expert annotators + review | $$$ |

```python
# Premium tier for medical imaging
project = client.projects.create(
    name="Medical Imaging",
    annotation_type="segmentation",
    pricing_tier="premium"
)
```

---

## Custom Label Schemas

### Hierarchical Labels

```python
project = client.projects.create(
    name="Hierarchical Classification",
    annotation_type="classification",
    labels={
        "type": "hierarchical",
        "categories": [
            {
                "name": "Electronics",
                "children": [
                    {"name": "Phones"},
                    {"name": "Laptops"},
                    {"name": "Tablets"}
                ]
            },
            {
                "name": "Clothing",
                "children": [
                    {"name": "Shirts"},
                    {"name": "Pants"},
                    {"name": "Shoes"}
                ]
            }
        ]
    }
)
```

### Labels with Attributes

```python
project = client.projects.create(
    name="Detailed Classification",
    annotation_type="bounding_box",
    labels=[
        {
            "name": "Vehicle",
            "attributes": [
                {"name": "color", "type": "select", "options": ["red", "blue", "white", "black"]},
                {"name": "occluded", "type": "boolean"},
                {"name": "truncated", "type": "boolean"},
                {"name": "difficulty", "type": "number", "min": 1, "max": 5}
            ]
        },
        {
            "name": "Pedestrian",
            "attributes": [
                {"name": "pose", "type": "select", "options": ["standing", "walking", "sitting"]},
                {"name": "age_group", "type": "select", "options": ["child", "adult", "elderly"]}
            ]
        }
    ]
)
```

---

## Storage Integration

### S3 Configuration

```python
# Project-level S3 configuration
project = client.projects.create(
    name="S3 Integration",
    annotation_type="classification",
    storage_config={
        "type": "s3",
        "bucket": "my-bucket",
        "prefix": "annotations/",
        "aws_access_key": "AKIAXXXXXXXX",
        "aws_secret_key": "...",
        "aws_region": "us-east-1"
    }
)

# Uploads will automatically use this bucket
project.upload_from_s3(prefix="images/batch1/")

# Exports automatically go to S3
project.export(format="coco")  # Auto-exports to configured bucket
```

### GCS Configuration

```python
project = client.projects.create(
    name="GCS Integration",
    storage_config={
        "type": "gcs",
        "bucket": "my-bucket",
        "prefix": "annotations/",
        "credentials_json": "{...}"
    }
)
```

### Azure Blob Configuration

```python
project = client.projects.create(
    name="Azure Integration",
    storage_config={
        "type": "azure",
        "container": "my-container",
        "prefix": "annotations/",
        "connection_string": "DefaultEndpointsProtocol=https;..."
    }
)
```

---

## Batch Processing

### Large Dataset Upload

```python
# Upload large datasets efficiently
project.upload_from_s3(
    bucket="my-bucket",
    prefix="images/",
    batch_size=500,        # Upload in batches of 500
    parallel=True,         # Parallel upload
    max_workers=4,         # Number of parallel workers
    skip_duplicates=True   # Skip already uploaded files
)
```

### Streaming Export

For large exports that don't fit in memory:

```python
# Stream export to file
with open("annotations.jsonl", "w") as f:
    for batch in project.export_stream(format="jsonl", batch_size=1000):
        for item in batch:
            f.write(json.dumps(item) + "\n")
```

---

## Retry Configuration

```python
from synapse import RetryConfig

# Custom retry settings
retry_config = RetryConfig(
    max_retries=5,
    initial_delay=1.0,      # First retry after 1 second
    max_delay=60.0,         # Max delay between retries
    exponential_base=2.0,   # Delay multiplier
    jitter=True             # Add random jitter
)

client = synapse.Client(
    api_key="sk_live_xxxx",
    retry_config=retry_config
)
```

---

## Logging

```python
import logging

# Enable debug logging
logging.basicConfig(level=logging.DEBUG)
synapse.set_log_level("DEBUG")

# Log to file
handler = logging.FileHandler("synapse.log")
synapse.add_log_handler(handler)

# Request logging
client = synapse.Client(
    api_key="sk_live_xxxx",
    log_requests=True  # Log all API requests
)
```

---

## Async/Await Support

The SDK supports async operations:

```python
import asyncio
import synapse

async def main():
    client = synapse.AsyncClient(api_key="sk_live_xxxx")
    
    # Async project creation
    project = await client.projects.create(
        name="Async Project",
        annotation_type="classification",
        labels=["A", "B"]
    )
    
    # Async upload
    await project.upload_tasks(tasks)
    
    # Async wait for completion
    await project.wait_for_completion()
    
    # Async export
    annotations = await project.export(format="json")
    
    await client.close()

asyncio.run(main())
```

---

## Custom HTTP Client

Use your own HTTP client:

```python
import httpx
import synapse

# Custom httpx client with specific settings
http_client = httpx.Client(
    timeout=60.0,
    limits=httpx.Limits(max_connections=50),
    transport=httpx.HTTPTransport(retries=3)
)

client = synapse.Client(
    api_key="sk_live_xxxx",
    http_client=http_client
)
```

---

## Rate Limit Handling

```python
from synapse import RateLimitConfig

rate_config = RateLimitConfig(
    auto_retry=True,           # Auto-retry on 429
    max_wait_time=300,         # Max wait time (seconds)
    respect_retry_after=True   # Use Retry-After header
)

client = synapse.Client(
    api_key="sk_live_xxxx",
    rate_limit_config=rate_config
)
```

---

## Testing & Development

### Sandbox Environment

```python
# Use sandbox for testing (no charges)
client = synapse.Client(
    api_key="sk_test_xxxx",  # Test API key
    base_url="https://sandbox-api.synapse.io"
)
```

### Mock Client

```python
from synapse.testing import MockClient

# Use mock client for unit tests
mock_client = MockClient()

# Configure mock responses
mock_client.projects.create.return_value = MockProject(
    id="proj_test",
    name="Test Project"
)

# Use in tests
project = mock_client.projects.create(name="Test")
assert project.id == "proj_test"
```

---

## Metadata & Tags

Add custom metadata to projects and tasks:

```python
# Project metadata
project = client.projects.create(
    name="My Project",
    annotation_type="classification",
    labels=["A", "B"],
    metadata={
        "environment": "production",
        "team": "ml-core",
        "model_version": "v2.3.1"
    },
    tags=["urgent", "medical", "hipaa"]
)

# Task metadata
project.upload_tasks([
    {
        "image_url": "...",
        "metadata": {
            "source": "user_upload",
            "timestamp": "2025-01-13T10:00:00Z",
            "device": "iphone_15"
        }
    }
])

# Filter by tags
projects = client.projects.list(tags=["medical"])
```
