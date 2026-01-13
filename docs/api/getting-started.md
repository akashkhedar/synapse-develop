# Getting Started with Synapse API

This guide walks you through setting up the Synapse Python SDK and creating your first annotation project.

## Table of Contents

1. [Installation](#installation)
2. [Authentication](#authentication)
3. [Quick Start](#quick-start)
4. [Understanding the Workflow](#understanding-the-workflow)
5. [Next Steps](#next-steps)

---

## Installation

### Requirements

- Python 3.8 or higher
- pip or poetry

### Install via pip

```bash
pip install synapse-sdk
```

### Install via poetry

```bash
poetry add synapse-sdk
```

### Install from source (development)

```bash
git clone https://github.com/synapse/synapse-sdk.git
cd synapse-sdk
pip install -e .
```

---

## Authentication

### Getting Your API Key

1. Log in to your Synapse dashboard at `https://app.synapse.io`
2. Navigate to **Settings** → **API & Webhooks**
3. Click **Generate API Key**
4. Copy your API key (format: `sk_live_xxxxxxxxxxxx`)

> ⚠️ **Security Note**: Keep your API key secret. Never commit it to version control. Use environment variables in production.

### Setting Up the Client

```python
import synapse

# Option 1: Pass API key directly
client = synapse.Client(api_key="sk_live_your_api_key_here")

# Option 2: Use environment variable (recommended)
import os
os.environ["SYNAPSE_API_KEY"] = "sk_live_your_api_key_here"
client = synapse.Client()  # Automatically reads from env

# Option 3: Use a config file
client = synapse.Client.from_config("~/.synapse/config.json")
```

### Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `SYNAPSE_API_KEY` | Your API key | Yes |
| `SYNAPSE_BASE_URL` | API base URL (default: `https://api.synapse.io`) | No |
| `SYNAPSE_TIMEOUT` | Request timeout in seconds (default: 30) | No |

---

## Quick Start

### Complete Example: Image Classification

```python
import synapse
import time

# 1. Initialize client
client = synapse.Client(api_key="sk_live_xxxx")

# 2. Create a project
project = client.projects.create(
    name="Product Image Classification",
    annotation_type="classification",
    labels=["Electronics", "Clothing", "Home & Garden", "Sports", "Other"],
    instructions="Classify each product image into the most appropriate category.",
    quality_settings={
        "min_annotators": 3,           # Each image labeled by 3 annotators
        "consensus_threshold": 0.66,   # 2/3 agreement required
        "enable_expert_review": True   # Expert reviews disputed items
    }
)

print(f"✓ Project created: {project.id}")

# 3. Upload your data
tasks = [
    {"image_url": "https://your-cdn.com/products/item1.jpg", "product_id": "SKU001"},
    {"image_url": "https://your-cdn.com/products/item2.jpg", "product_id": "SKU002"},
    {"image_url": "https://your-cdn.com/products/item3.jpg", "product_id": "SKU003"},
]

upload_result = project.upload_tasks(tasks)
print(f"✓ Uploaded {upload_result.task_count} tasks")

# 4. Pay security deposit and start project
deposit = project.calculate_deposit()
print(f"Security deposit required: ₹{deposit.amount}")

project.pay_deposit(payment_method="razorpay")  # or use stored payment method
project.start()
print("✓ Project started!")

# 5. Monitor progress
while True:
    status = project.get_status()
    print(f"Progress: {status.progress}% ({status.completed}/{status.total} tasks)")
    
    if status.is_complete:
        break
    
    time.sleep(3600)  # Check hourly

# 6. Download results
annotations = project.export(format="json")
print(f"✓ Downloaded {len(annotations)} annotations")

# 7. Use in your ML pipeline
for annotation in annotations:
    image_url = annotation["data"]["image_url"]
    label = annotation["annotations"][0]["result"]["value"]
    product_id = annotation["data"]["product_id"]
    
    print(f"{product_id}: {label}")
```

### Output

```
✓ Project created: proj_abc123xyz
✓ Uploaded 3 tasks
Security deposit required: ₹150.00
✓ Project started!
Progress: 0% (0/3 tasks)
Progress: 33% (1/3 tasks)
Progress: 100% (3/3 tasks)
✓ Downloaded 3 annotations
SKU001: Electronics
SKU002: Clothing
SKU003: Home & Garden
```

---

## Understanding the Workflow

### The Synapse Annotation Pipeline

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         YOUR ML PIPELINE                                │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  1. CREATE PROJECT        2. UPLOAD DATA       3. PAY DEPOSIT          │
│     ┌─────────┐            ┌─────────┐          ┌─────────┐            │
│     │ Define  │───────────▶│ Upload  │─────────▶│   Pay   │            │
│     │ config  │            │  tasks  │          │ deposit │            │
│     └─────────┘            └─────────┘          └─────────┘            │
│                                                       │                 │
└───────────────────────────────────────────────────────┼─────────────────┘
                                                        │
                                                        ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                       SYNAPSE ANNOTATION PLATFORM                       │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│     4. ANNOTATION         5. CONSENSUS         6. EXPERT REVIEW        │
│     ┌─────────┐          ┌─────────┐          ┌─────────┐              │
│     │Multiple │─────────▶│ Compare │─────────▶│ Expert  │              │
│     │annotators│         │ results │          │ review  │              │
│     └─────────┘          └─────────┘          └─────────┘              │
│          │                    │                    │                    │
│          │                    │                    │                    │
│          ▼                    ▼                    ▼                    │
│     ┌─────────────────────────────────────────────────┐                │
│     │            QUALITY-ASSURED ANNOTATIONS           │                │
│     └─────────────────────────────────────────────────┘                │
│                               │                                         │
└───────────────────────────────┼─────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                         YOUR ML PIPELINE                                │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│     7. DOWNLOAD RESULTS       8. TRAIN MODEL                           │
│     ┌─────────┐              ┌─────────┐                               │
│     │ Export  │─────────────▶│  Train  │                               │
│     │  data   │              │  model  │                               │
│     └─────────┘              └─────────┘                               │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

### Project States

| State | Description |
|-------|-------------|
| `draft` | Project created but not started |
| `pending_deposit` | Awaiting security deposit payment |
| `active` | Project is being annotated |
| `paused` | Project temporarily paused |
| `review` | In expert review phase |
| `completed` | All annotations finished |
| `cancelled` | Project was cancelled |

### Payment Flow

1. **Security Deposit**: Refundable deposit based on project size (released after completion)
2. **Annotation Credits**: Charged per task based on complexity
3. **Final Payment**: Released to annotators when you download results

---

## Next Steps

- 📖 **[SDK Reference](./sdk-reference.md)** - Complete API documentation
- 🔧 **[Configuration Options](./configuration.md)** - Advanced project settings
- 📊 **[Annotation Types](./annotation-types.md)** - Supported annotation formats
- 🔔 **[Webhooks](./webhooks.md)** - Real-time notifications
- 💡 **[Examples](./examples/)** - More code examples

---

## Common Issues

### Authentication Failed

```python
synapse.errors.AuthenticationError: Invalid API key
```

**Solution**: Verify your API key is correct and not expired. Generate a new key from the dashboard.

### Insufficient Credits

```python
synapse.errors.InsufficientCreditsError: Not enough credits for this operation
```

**Solution**: Add credits to your account via the billing dashboard.

### Rate Limited

```python
synapse.errors.RateLimitError: Rate limit exceeded. Retry after 60 seconds.
```

**Solution**: The SDK handles rate limiting automatically with exponential backoff. For high-volume operations, use batch endpoints.
