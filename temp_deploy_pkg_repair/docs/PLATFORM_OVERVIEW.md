# Synapse Platform Overview

> Last Updated: January 13, 2026

## Executive Summary

**Synapse** is an enterprise-grade data annotation platform designed for machine learning teams. It provides comprehensive tools for labeling various types of data including images, text, audio, video, and time-series data. The platform combines a powerful annotation interface with a managed workforce of trained annotators, quality assurance mechanisms, and seamless ML pipeline integration.

---

## Table of Contents

1. [Platform Architecture](#platform-architecture)
2. [Core Features](#core-features)
3. [User Roles](#user-roles)
4. [Technology Stack](#technology-stack)
5. [Key Modules](#key-modules)
6. [Data Flow](#data-flow)
7. [Integration Capabilities](#integration-capabilities)
8. [Deployment Options](#deployment-options)

---

## Platform Architecture

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              SYNAPSE PLATFORM                                │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐          │
│  │   Client Portal  │  │ Annotator Portal │  │   Expert Portal  │          │
│  │   (React/NX)     │  │   (React/NX)     │  │   (React/NX)     │          │
│  └────────┬─────────┘  └────────┬─────────┘  └────────┬─────────┘          │
│           │                     │                     │                      │
│           └─────────────────────┴─────────────────────┘                      │
│                                 │                                            │
│                    ┌────────────▼────────────┐                               │
│                    │      REST API Layer     │                               │
│                    │   (Django REST Framework)│                               │
│                    └────────────┬────────────┘                               │
│                                 │                                            │
│  ┌──────────────────────────────┴──────────────────────────────────────┐    │
│  │                         CORE SERVICES                                │    │
│  ├──────────┬──────────┬──────────┬──────────┬──────────┬─────────────┤    │
│  │ Projects │  Tasks   │Annotators│ Billing  │   ML     │  Webhooks   │    │
│  │ Service  │ Service  │ Service  │ Service  │ Backend  │  Service    │    │
│  └──────────┴──────────┴──────────┴──────────┴──────────┴─────────────┘    │
│                                 │                                            │
│           ┌─────────────────────┼─────────────────────┐                     │
│           │                     │                     │                     │
│  ┌────────▼─────────┐  ┌───────▼────────┐  ┌────────▼─────────┐           │
│  │   PostgreSQL     │  │     Redis      │  │   File Storage   │           │
│  │   (Primary DB)   │  │  (Cache/Queue) │  │   (S3/GCS/Local) │           │
│  └──────────────────┘  └────────────────┘  └──────────────────┘           │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Monorepo Structure

```
synapse-develop/
├── synapse/              # Django Backend (Core Platform)
│   ├── annotators/       # Annotator management & workforce
│   ├── billing/          # Credits, subscriptions, payments
│   ├── core/             # Core utilities, settings, middleware
│   ├── data_export/      # Export functionality
│   ├── data_import/      # Import functionality
│   ├── fsm/              # Finite State Machine framework
│   ├── ml/               # ML Backend integration
│   ├── organizations/    # Multi-tenancy & org management
│   ├── projects/         # Project management
│   ├── tasks/            # Task & annotation management
│   ├── users/            # User authentication & management
│   └── webhooks/         # Event notifications
│
├── web/                  # Frontend Monorepo (NX)
│   ├── apps/
│   │   └── synapse/      # Main React application
│   └── libs/
│       ├── editor/       # Annotation interface (Synapse Frontend)
│       ├── datamanager/  # Data exploration & management
│       └── ui/           # Shared UI components
│
├── synapse-sdk/          # Python SDK for API integration
│
└── docs/                 # API & platform documentation
```

---

## Core Features

### 1. Multi-Modal Annotation

| Data Type | Supported Annotations |
|-----------|----------------------|
| **Images** | Classification, Bounding Box, Polygon, Segmentation, Keypoints |
| **Text** | NER, Classification, Sentiment Analysis, Q&A, Relations |
| **Audio** | Transcription, Speaker Identification, Emotion Detection |
| **Video** | Object Tracking, Action Recognition, Temporal Annotation |
| **Time Series** | Event Detection, Pattern Labeling, Anomaly Marking |
| **Documents** | OCR, Layout Analysis, Table Extraction |

### 2. Annotation Editor (Synapse Frontend)

- **XML-Based Configuration**: Flexible labeling interface definition
- **Real-Time Preview**: Live annotation preview
- **Keyboard Shortcuts**: Customizable hotkeys for efficiency
- **Multi-Tool Support**: Switch between tools seamlessly
- **Undo/Redo**: Full history management
- **Collaborative Features**: Comments, annotations review

### 3. Quality Assurance System

```
                    ┌─────────────────────────────────────────────┐
                    │          QUALITY ASSURANCE PIPELINE          │
                    ├─────────────────────────────────────────────┤
                    │                                             │
  Annotator 1 ─────▶│  ┌─────────┐    ┌───────────┐    ┌──────┐ │
  Annotator 2 ─────▶│  │Consensus│───▶│  Conflict │───▶│Expert│ │
  Annotator 3 ─────▶│  │ Engine  │    │ Detection │    │Review│ │
                    │  └─────────┘    └───────────┘    └──────┘ │
                    │        │                              │    │
                    │        ▼                              ▼    │
                    │  ┌─────────────────────────────────────┐  │
                    │  │      GROUND TRUTH ANNOTATION         │  │
                    │  └─────────────────────────────────────┘  │
                    └─────────────────────────────────────────────┘
```

- **Multi-Annotator Consensus**: 3+ annotators per task (configurable)
- **Honeypot Tasks**: Hidden test tasks for quality monitoring
- **Expert Review**: Senior reviewers for conflict resolution
- **Accuracy Scoring**: Per-annotator accuracy tracking

### 4. Project Management

- **Project Creation Wizard**: Guided setup with template selection
- **Label Configuration**: XML-based flexible label interface
- **Task Assignment**: Automatic intelligent distribution
- **Progress Tracking**: Real-time dashboard
- **Version Control**: Track configuration changes

### 5. Data Management

- **Bulk Import**: CSV, JSON, direct uploads, cloud storage sync
- **Cloud Storage Integration**: AWS S3, Google Cloud Storage, Azure Blob
- **Data Filtering**: Advanced filtering and search
- **Bulk Operations**: Mass updates, deletions, exports
- **Export Formats**: JSON, CSV, COCO, Pascal VOC, YOLO, and more

### 6. ML Integration

- **Pre-Annotations**: Import model predictions
- **Active Learning**: Smart task prioritization
- **ML Backend Connection**: Real-time model predictions
- **Model Evaluation**: Compare model vs human annotations

---

## User Roles

### 1. Clients (Organizations)

| Role | Description | Capabilities |
|------|-------------|--------------|
| **Owner** | Organization creator | Full access, billing, team management |
| **Admin** | Organization administrator | Project management, team management |
| **Member** | Regular team member | Project access, annotation review |

### 2. Annotators (Workforce)

| Status | Description | Capabilities |
|--------|-------------|--------------|
| **Pending Verification** | Email not verified | Cannot access tasks |
| **Pending Test** | Awaiting skill test | Can take qualification test |
| **Under Review** | Test submitted | Awaiting admin review |
| **Approved** | Active annotator | Full annotation access |
| **Expert** | Senior annotator | Review & conflict resolution |
| **Suspended** | Account suspended | No access |

### 3. Trust Levels (Annotators)

| Level | Requirements | Multiplier |
|-------|-------------|------------|
| **New** | Starting level | 0.8x |
| **Junior** | 50 tasks, 70% accuracy | 1.0x |
| **Regular** | 200 tasks, 80% accuracy | 1.1x |
| **Senior** | 500 tasks, 90% accuracy | 1.3x |
| **Expert** | 1000 tasks, 95% accuracy | 1.5x |

---

## Technology Stack

### Backend

| Component | Technology | Version |
|-----------|-----------|---------|
| Framework | Django | 5.1.8 |
| API | Django REST Framework | 3.15.2 |
| Database | PostgreSQL | 14+ |
| Cache/Queue | Redis | 5.2+ |
| Task Queue | RQ (Redis Queue) | 2.6 |
| State Machine | Custom FSM (UUID7) | - |

### Frontend

| Component | Technology | Version |
|-----------|-----------|---------|
| Framework | React | 18.x |
| State Management | MobX State Tree | 5.x |
| Monorepo | NX | Latest |
| Styling | Tailwind CSS + SCSS | 3.x |
| Build | Webpack | 5.x |

### Infrastructure

| Component | Technology |
|-----------|-----------|
| Storage | AWS S3 / GCS / Azure Blob |
| Payment | Razorpay |
| Monitoring | Sentry |
| Feature Flags | LaunchDarkly |

---

## Key Modules

### Backend Modules (`synapse/`)

| Module | Description |
|--------|-------------|
| `annotators` | Workforce management, assignments, payments, gamification |
| `billing` | Credits, subscriptions, pricing, payment processing |
| `core` | Settings, utilities, middleware, feature flags |
| `data_export` | Export annotations in various formats |
| `data_import` | Import data from various sources |
| `data_manager` | Data filtering, views, bulk operations |
| `fsm` | Finite State Machine for entity state tracking |
| `io_storages` | Cloud storage integrations |
| `jwt_auth` | JWT-based API authentication |
| `ml` | ML backend integration and predictions |
| `organizations` | Multi-tenancy and organization management |
| `projects` | Project configuration and management |
| `tasks` | Task and annotation models |
| `users` | User authentication and profiles |
| `webhooks` | Real-time event notifications |

### Frontend Libraries (`web/libs/`)

| Library | Description |
|---------|-------------|
| `editor` | Main annotation interface (Synapse Frontend) |
| `datamanager` | Data exploration and task management |
| `ui` | Shared React components and design system |
| `core` | Shared utilities and helpers |
| `app-common` | Common application logic and API clients |

---

## Data Flow

### Annotation Workflow

```
1. CLIENT CREATES PROJECT
   │
   ├─► Define label config (XML)
   ├─► Set quality settings (overlap, consensus threshold)
   ├─► Upload data or connect storage
   └─► Pay security deposit
         │
         ▼
2. TASKS DISTRIBUTED TO ANNOTATORS
   │
   ├─► Intelligent assignment engine
   ├─► Match skills to task complexity
   ├─► Respect trust levels
   └─► Insert honeypot tasks
         │
         ▼
3. ANNOTATIONS CREATED
   │
   ├─► Multiple annotators per task
   ├─► Time tracking & quality scoring
   ├─► Immediate payment release (40%)
   └─► Progress updates via webhooks
         │
         ▼
4. CONSENSUS CALCULATION
   │
   ├─► Compare annotator results
   ├─► Calculate agreement scores
   ├─► Identify conflicts
   └─► Consensus payment release (40%)
         │
         ▼
5. EXPERT REVIEW (if needed)
   │
   ├─► High-disagreement tasks flagged
   ├─► Expert reviews and corrects
   ├─► Final ground truth established
   └─► Review payment release (20%)
         │
         ▼
6. CLIENT EXPORTS DATA
   │
   ├─► Multiple format options
   ├─► Webhook notification
   └─► Download or sync to storage
```

---

## Integration Capabilities

### Python SDK

```python
from synapse_sdk import Synapse

client = Synapse(api_key="sk_live_xxx")

# Create project
project = client.projects.create(
    name="Image Classification",
    annotation_type="classification",
    labels=["dog", "cat", "bird"]
)

# Upload data
project.upload_tasks([
    {"image": "https://cdn.example.com/img1.jpg"},
    {"image": "https://cdn.example.com/img2.jpg"}
])

# Monitor and export
annotations = project.export(format="json")
```

### REST API

- Full RESTful API with OpenAPI/Swagger documentation
- JWT and API Key authentication
- Rate limiting per organization
- Comprehensive error handling

### Webhooks

Supported events:
- `project.created`, `project.completed`
- `task.created`, `task.completed`
- `annotation.created`, `annotation.updated`
- `export.ready`

### Cloud Storage Sync

- **Import**: S3, GCS, Azure Blob, HTTP endpoints
- **Export**: Direct sync to cloud storage
- **Automatic sync**: Scheduled polling for new data

---

## Deployment Options

### Self-Hosted (Open Source)

```bash
pip install synapse
synapse start
```

### Docker

```bash
docker-compose -f docker-compose.dev.yml up
```

### Enterprise Cloud

- Managed hosting
- SLA guarantees
- Dedicated support
- Custom integrations

---

## Security & Compliance

### Data Security

- **Encryption**: TLS in transit, AES-256 at rest
- **Access Control**: Role-based access control (RBAC)
- **Audit Logs**: Complete activity tracking
- **Data Isolation**: Multi-tenant architecture

### Compliance

- GDPR-ready data handling
- HIPAA-ready for medical data (Enterprise)
- SOC 2 Type II (Enterprise)
- Data residency options

---

## Performance Characteristics

| Metric | Specification |
|--------|--------------|
| **Annotations/Month** | 10M+ (Enterprise) |
| **Concurrent Annotators** | 10,000+ |
| **API Latency** | < 100ms (p95) |
| **Uptime SLA** | 99.9% (Enterprise) |
| **Data Export** | Streaming for large datasets |

---

## Getting Started

### For Clients

1. Sign up at `https://app.synapse.io`
2. Create your organization
3. Add credits to your account
4. Create your first project
5. Upload data and start annotating

### For Developers

1. Install the SDK: `pip install synapse-sdk`
2. Get API key from Settings → API & Webhooks
3. Follow the [API Getting Started Guide](./api/getting-started.md)

### For Annotators

1. Apply at `https://app.synapse.io/annotators/signup`
2. Verify email
3. Complete qualification test
4. Start earning on approved tasks

---

## Next Steps

- [Backend Architecture →](./BACKEND_ARCHITECTURE.md)
- [Frontend Architecture →](./FRONTEND_ARCHITECTURE.md)
- [Business Model →](./BUSINESS_MODEL.md)
- [API Reference →](./api/README.md)
