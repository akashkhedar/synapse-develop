# Synapse API Documentation

> Last Updated: February 7, 2026

Welcome to the Synapse API documentation. This guide is designed for **enterprise clients** who want to integrate Synapse's data annotation capabilities directly into their ML pipelines.

## Quick Links

| Document | Description |
|----------|-------------|
| [Getting Started](./getting-started.md) | Installation, authentication, and your first project |
| [Python SDK Reference](./sdk-reference.md) | Complete SDK documentation |
| [REST API Reference](./rest-api.md) | Direct HTTP API endpoints |
| [Annotation Types](./annotation-types.md) | Supported annotation formats & output schemas |
| [Webhooks](./webhooks.md) | Real-time event notifications |
| [Configuration](./configuration.md) | Advanced settings & customization |
| [Complete Workflow Examples](./examples/complete-workflow.md) | End-to-end ML pipeline examples |

## What is Synapse?

Synapse is an enterprise-grade data annotation platform that provides:

- **High-quality annotations** from trained, verified annotators
- **Multiple annotation types** (classification, bounding boxes, segmentation, NER, etc.)
- **Quality assurance** through consensus mechanisms and expert review
- **Seamless integration** with your existing ML pipelines

## Integration Overview

```python
from synapse_sdk import Synapse

# Initialize client
client = Synapse(api_key="sk_live_xxxx")

# Create project → Upload data → Wait for completion → Download results
project = client.projects.create(name="My Project", annotation_type="classification")
project.upload_data([{"image": "s3://bucket/img1.jpg"}, ...])

# Monitor progress
while project.progress < 100:
    time.sleep(3600)

# Download annotations
annotations = project.export(format="coco")
```

## Support

- **Email**: api-support@synapse.io
- **Documentation Issues**: [GitHub Issues](https://github.com/synapse/docs/issues)
- **Enterprise Support**: Contact your account manager
