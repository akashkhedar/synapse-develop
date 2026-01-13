import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import type { Page } from "../types/Page";
import "./ApiDocsPage.css";

// SDK Documentation Types
interface CodeExample {
  language: string;
  code: string;
}

interface SDKMethod {
  name: string;
  signature: string;
  description: string;
  parameters?: { name: string; type: string; required: boolean; description: string }[];
  returns?: string;
  example: CodeExample;
}

interface SDKSection {
  id: string;
  name: string;
  description: string;
  icon: React.ReactNode;
  methods: SDKMethod[];
}

// SVG Icons
const InstallIcon = () => (
  <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
    <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>
    <polyline points="7,10 12,15 17,10"/>
    <line x1="12" y1="15" x2="12" y2="3"/>
  </svg>
);

const ClientIcon = () => (
  <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
    <rect x="3" y="11" width="18" height="11" rx="2" ry="2"/>
    <path d="M7 11V7a5 5 0 0 1 10 0v4"/>
  </svg>
);

const ProjectIcon = () => (
  <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
    <path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z"/>
  </svg>
);

const UploadIcon = () => (
  <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
    <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>
    <polyline points="17,8 12,3 7,8"/>
    <line x1="12" y1="3" x2="12" y2="15"/>
  </svg>
);

const ExportIcon = () => (
  <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
    <path d="M4 14.899A7 7 0 1 1 15.71 8h1.79a4.5 4.5 0 0 1 2.5 8.242"/>
    <path d="M12 12v9"/>
    <path d="m8 17 4 4 4-4"/>
  </svg>
);

const WebhookIcon = () => (
  <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
    <circle cx="12" cy="12" r="10"/>
    <path d="M12 16v-4"/>
    <path d="M12 8h.01"/>
  </svg>
);

const BillingIcon = () => (
  <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
    <rect x="1" y="4" width="22" height="16" rx="2" ry="2"/>
    <line x1="1" y1="10" x2="23" y2="10"/>
  </svg>
);

// SDK Sections Data
const sdkSections: SDKSection[] = [
  {
    id: "installation",
    name: "Installation",
    description: "Install the Synapse Python SDK to get started",
    icon: <InstallIcon />,
    methods: [
      {
        name: "pip install",
        signature: "pip install synapse-sdk",
        description: "Install the Synapse SDK using pip package manager.",
        example: {
          language: "bash",
          code: `# Install with pip
pip install synapse-sdk

# Or with poetry
poetry add synapse-sdk

# Verify installation
python -c "from synapse_sdk import Synapse; print('SDK installed!')"`
        }
      }
    ]
  },
  {
    id: "client",
    name: "Client",
    description: "Initialize the Synapse client with your API key",
    icon: <ClientIcon />,
    methods: [
      {
        name: "Synapse",
        signature: "Synapse(api_key: str, base_url: str = None)",
        description: "Create a new Synapse client instance. The API key can be obtained from Settings > API Keys.",
        parameters: [
          { name: "api_key", type: "str", required: true, description: "Your Synapse API key" },
          { name: "base_url", type: "str", required: false, description: "API base URL (default: https://app.synapse.io)" },
          { name: "timeout", type: "float", required: false, description: "Request timeout in seconds (default: 60)" },
        ],
        returns: "Synapse client instance",
        example: {
          language: "python",
          code: `from synapse_sdk import Synapse

# Initialize with API key
client = Synapse(api_key="your-api-key")

# Check available clients
# client.projects - Project management
# client.tasks - Task operations  
# client.billing - Billing & deposits
# client.import_storage - Cloud storage imports`
        }
      }
    ]
  },
  {
    id: "projects",
    name: "Projects",
    description: "Create and manage annotation projects",
    icon: <ProjectIcon />,
    methods: [
      {
        name: "projects.create",
        signature: "client.projects.create(title: str, label_config: str, ...)",
        description: "Create a new annotation project with the specified label configuration.",
        parameters: [
          { name: "title", type: "str", required: false, description: "Project title/name" },
          { name: "description", type: "str", required: false, description: "Project description" },
          { name: "label_config", type: "str", required: false, description: "XML label configuration (Label Studio format)" },
          { name: "expert_instruction", type: "str", required: false, description: "Instructions for annotators" },
          { name: "color", type: "str", required: false, description: "Project color (hex code)" },
        ],
        returns: "LseProjectCreate object",
        example: {
          language: "python",
          code: `# Create an image classification project
project = client.projects.create(
    title="Product Classification",
    label_config='''
    <View>
      <Image name="image" value="$image"/>
      <Choices name="category" toName="image">
        <Choice value="Electronics"/>
        <Choice value="Clothing"/>
        <Choice value="Food"/>
      </Choices>
    </View>
    ''',
    expert_instruction="Classify each product image"
)

print(f"Project ID: {project.id}")`
        }
      },
      {
        name: "projects.list",
        signature: "client.projects.list(state: str = None, search: str = None)",
        description: "List all projects accessible to the authenticated user. Returns a paginated iterator.",
        parameters: [
          { name: "state", type: "str", required: false, description: "Filter by state: draft, active, completed" },
          { name: "search", type: "str", required: false, description: "Search by title or description" },
          { name: "page_size", type: "int", required: false, description: "Results per page (default: 50)" },
        ],
        returns: "SyncPager[AllRolesProjectList]",
        example: {
          language: "python",
          code: `# List all projects
for project in client.projects.list():
    print(f"{project.title}: {project.task_number} tasks")

# Iterate by page
for page in client.projects.list().iter_pages():
    for project in page:
        print(project.title)`
        }
      },
      {
        name: "projects.get",
        signature: "client.projects.get(id: int)",
        description: "Retrieve a specific project by ID. Returns extended project with synapse interface access.",
        parameters: [
          { name: "id", type: "int", required: true, description: "The project ID" },
        ],
        returns: "ProjectExt object",
        example: {
          language: "python",
          code: `project = client.projects.get(id=123)

print(f"Title: {project.title}")
print(f"Tasks: {project.task_number}")

# Access label interface
interface = project.get_synapse_interface()
print(f"Labels: {interface.labels}")`
        }
      }
    ]
  },
  {
    id: "upload",
    name: "Upload Data",
    description: "Import data from cloud storage into your projects",
    icon: <UploadIcon />,
    methods: [
      {
        name: "import_storage.s3.import_from_bucket",
        signature: "client.import_storage.s3.import_from_bucket(project_id, bucket, prefix, ...)",
        description: "Import data from an S3 bucket into a project. Creates storage connection and syncs tasks in one call.",
        parameters: [
          { name: "project_id", type: "int", required: true, description: "Target project ID" },
          { name: "bucket", type: "str", required: true, description: "S3 bucket name" },
          { name: "prefix", type: "str", required: false, description: "S3 key prefix to filter files" },
          { name: "region", type: "str", required: false, description: "AWS region (e.g., us-east-1)" },
          { name: "aws_access_key_id", type: "str", required: false, description: "AWS access key (or use IAM role)" },
          { name: "aws_secret_access_key", type: "str", required: false, description: "AWS secret key" },
          { name: "regex_filter", type: "str", required: false, description: "Regex pattern to filter objects" },
          { name: "recursive", type: "bool", required: false, description: "Scan bucket recursively (default: True)" },
        ],
        returns: "StorageImportResult with storage_id, tasks_imported, status",
        example: {
          language: "python",
          code: `# Import images from S3 bucket
result = client.import_storage.s3.import_from_bucket(
    project_id=123,
    bucket="my-training-data",
    prefix="images/products/2025/",
    region="us-east-1",
    aws_access_key_id="AKIA...",
    aws_secret_access_key="your-secret-key",
    regex_filter=r".*\\.(jpg|png|webp)$"
)

print(f"Imported {result['tasks_imported']} tasks")`
        }
      },
      {
        name: "import_storage.s3.create",
        signature: "client.import_storage.s3.create(project, bucket, ...)",
        description: "Create an S3 storage connection for a project. Use with sync() for manual control.",
        parameters: [
          { name: "project", type: "int", required: true, description: "Project ID" },
          { name: "bucket", type: "str", required: true, description: "S3 bucket name" },
          { name: "prefix", type: "str", required: false, description: "S3 prefix/folder" },
          { name: "region_name", type: "str", required: false, description: "AWS region" },
          { name: "use_blob_urls", type: "bool", required: false, description: "Generate presigned URLs" },
        ],
        returns: "S3ImportStorage object",
        example: {
          language: "python",
          code: `# Create storage connection
storage = client.import_storage.s3.create(
    project=123,
    bucket="my-bucket",
    prefix="data/",
    region_name="us-west-2"
)

# Sync tasks from storage
synced = client.import_storage.s3.sync(id=storage.id)
print(f"Storage ID: {storage.id}")`
        }
      }
    ]
  },
  {
    id: "billing",
    name: "Billing & Deposits",
    description: "Manage security deposits and billing for annotation projects",
    icon: <BillingIcon />,
    methods: [
      {
        name: "billing.calculate_deposit",
        signature: "client.billing.calculate_deposit(project_id, estimated_tasks, ...)",
        description: "Calculate the required security deposit based on project configuration and task count.",
        parameters: [
          { name: "project_id", type: "int", required: false, description: "Existing project ID" },
          { name: "label_config", type: "str", required: false, description: "Label config for new projects" },
          { name: "estimated_tasks", type: "int", required: false, description: "Estimated number of tasks" },
          { name: "estimated_storage_gb", type: "float", required: false, description: "Estimated storage in GB" },
        ],
        returns: "DepositCalculation with deposit_amount, breakdown",
        example: {
          language: "python",
          code: `# Calculate deposit for existing project
deposit = client.billing.calculate_deposit(project_id=123)

print(f"Total deposit: {deposit['deposit_amount']} credits")
print(f"Annotation cost: {deposit['estimated_annotation_cost']}")
print(f"Storage cost: {deposit['estimated_storage_cost']}")`
        }
      },
      {
        name: "billing.pay_deposit",
        signature: "client.billing.pay_deposit(project_id, deposit_amount, ...)",
        description: "Collect security deposit from organization credits to activate the project.",
        parameters: [
          { name: "project_id", type: "int", required: true, description: "Project ID to pay deposit for" },
          { name: "deposit_amount", type: "float", required: false, description: "Pre-calculated deposit amount" },
          { name: "estimated_tasks", type: "int", required: false, description: "Task count for calculation" },
        ],
        returns: "Result with deposit_collected, state, project_id",
        example: {
          language: "python",
          code: `# Calculate and pay deposit
deposit = client.billing.calculate_deposit(project_id=123)
result = client.billing.pay_deposit(
    project_id=123,
    deposit_amount=deposit['deposit_amount']
)

print(f"Collected: {result['deposit_collected']} credits")
print(f"Project state: {result['state']}")`
        }
      },
      {
        name: "billing.get_balance",
        signature: "client.billing.get_balance()",
        description: "Get the current credit balance for your organization.",
        returns: "Balance dict with credit_balance and other billing info",
        example: {
          language: "python",
          code: `balance = client.billing.get_balance()
print(f"Available credits: {balance.get('credit_balance', 0)}")`
        }
      },
      {
        name: "billing.get_project_status",
        signature: "client.billing.get_project_status(project_id)",
        description: "Get detailed billing status for a project including deposit, costs, and lifecycle state.",
        parameters: [
          { name: "project_id", type: "int", required: true, description: "Project ID" },
        ],
        returns: "ProjectBillingStatus with security_deposit, costs, lifecycle",
        example: {
          language: "python",
          code: `status = client.billing.get_project_status(project_id=123)

print(f"Deposit paid: {status['security_deposit']['paid']}")
print(f"Credits consumed: {status['costs']['credits_consumed']}")
print(f"Lifecycle state: {status['lifecycle']['state']}")`
        }
      },
      {
        name: "billing.get_dashboard",
        signature: "client.billing.get_dashboard()",
        description: "Get complete billing dashboard with balance, recent transactions, and payments.",
        returns: "BillingDashboard with billing, recent_transactions, recent_payments",
        example: {
          language: "python",
          code: `dashboard = client.billing.get_dashboard()

print(f"Credit balance: {dashboard['billing']['credit_balance']}")
print("Recent transactions:")
for txn in dashboard['recent_transactions'][:5]:
    print(f"  {txn['description']}: {txn['amount']}")`
        }
      }
    ]
  },
  {
    id: "monitoring",
    name: "Tasks & Monitoring",
    description: "List tasks and monitor project progress",
    icon: <WebhookIcon />,
    methods: [
      {
        name: "tasks.list",
        signature: "client.tasks.list(project, fields='all')",
        description: "List tasks for a project with full annotation details. Returns paginated results.",
        parameters: [
          { name: "project", type: "int", required: false, description: "Filter by project ID" },
          { name: "fields", type: "str", required: false, description: "'all' for full data or 'task_only'" },
          { name: "only_annotated", type: "bool", required: false, description: "Only return annotated tasks" },
          { name: "page_size", type: "int", required: false, description: "Results per page" },
        ],
        returns: "SyncPagerExt[RoleBasedTask]",
        example: {
          language: "python",
          code: `# List all tasks for a project
for task in client.tasks.list(project=123):
    print(f"Task {task.id}: {len(task.annotations or [])} annotations")

# Count completed tasks
completed = sum(
    1 for t in client.tasks.list(project=123) 
    if t.annotations
)`
        }
      },
      {
        name: "tasks.get",
        signature: "client.tasks.get(id)",
        description: "Get a specific task by ID with all annotations and predictions.",
        parameters: [
          { name: "id", type: "int", required: true, description: "Task ID" },
        ],
        returns: "LseTask object",
        example: {
          language: "python",
          code: `task = client.tasks.get(id=456)

print(f"Task data: {task.data}")
print(f"Annotations: {len(task.annotations or [])}")
for ann in task.annotations or []:
    print(f"  - By {ann.completed_by}: {ann.result}")`
        }
      },
      {
        name: "projects.stats.get",
        signature: "client.projects.stats.get(id)",
        description: "Get aggregated statistics for a project including completion rates and quality metrics.",
        parameters: [
          { name: "id", type: "int", required: true, description: "Project ID" },
        ],
        returns: "Project statistics object",
        example: {
          language: "python",
          code: `stats = client.projects.stats.get(id=123)

print(f"Total tasks: {stats.get('task_count', 0)}")
print(f"Annotated: {stats.get('annotated_count', 0)}")
print(f"Completion: {stats.get('completion_percent', 0)}%")`
        }
      }
    ]
  },
  {
    id: "export",
    name: "Export Data",
    description: "Export annotations in various ML-ready formats",
    icon: <ExportIcon />,
    methods: [
      {
        name: "projects.exports.as_json",
        signature: "client.projects.exports.as_json(project_id, timeout=60)",
        description: "Export project annotations as a JSON object. Handles both sync and async exports automatically.",
        parameters: [
          { name: "project_id", type: "int", required: true, description: "Project ID to export" },
          { name: "timeout", type: "int", required: false, description: "Max wait time for export (default: 60s)" },
        ],
        returns: "Dict with annotations data",
        example: {
          language: "python",
          code: `# Export as JSON
annotations = client.projects.exports.as_json(project_id=123)

# Process annotations
for task in annotations:
    print(f"Task {task['id']}: {len(task['annotations'])} annotations")
    for ann in task['annotations']:
        print(f"  Result: {ann['result']}")`
        }
      },
      {
        name: "projects.exports.as_pandas",
        signature: "client.projects.exports.as_pandas(project_id, timeout=60)",
        description: "Export project annotations as a pandas DataFrame. Useful for data analysis.",
        parameters: [
          { name: "project_id", type: "int", required: true, description: "Project ID to export" },
          { name: "timeout", type: "int", required: false, description: "Max wait time (default: 60s)" },
        ],
        returns: "pandas.DataFrame",
        example: {
          language: "python",
          code: `import pandas as pd

# Export to pandas DataFrame
df = client.projects.exports.as_pandas(project_id=123)

print(f"Total rows: {len(df)}")
print(df.head())

# Save to CSV
df.to_csv("annotations.csv", index=False)`
        }
      },
      {
        name: "projects.exports.as_file",
        signature: "client.projects.exports.as_file(project_id, export_type='JSON', timeout=60)",
        description: "Export annotations as a file-like object in the specified format.",
        parameters: [
          { name: "project_id", type: "int", required: true, description: "Project ID to export" },
          { name: "export_type", type: "str", required: false, description: "Format: JSON, CSV, COCO, YOLO, etc." },
          { name: "timeout", type: "int", required: false, description: "Max wait time (default: 60s)" },
        ],
        returns: "File-like BinaryIO object",
        example: {
          language: "python",
          code: `# Export as COCO format
fileobj = client.projects.exports.as_file(
    project_id=123,
    export_type="COCO"
)

# Save to disk
with open("annotations_coco.json", "wb") as f:
    f.write(fileobj.read())`
        }
      },
      {
        name: "projects.exports.list_formats",
        signature: "client.projects.exports.list_formats(id)",
        description: "Get available export formats for a project based on its label configuration.",
        parameters: [
          { name: "id", type: "int", required: true, description: "Project ID" },
        ],
        returns: "List of available format strings",
        example: {
          language: "python",
          code: `# List available formats
formats = client.projects.exports.list_formats(id=123)
print(f"Available formats: {formats}")
# ['JSON', 'CSV', 'TSV', 'COCO', 'YOLO', ...]`
        }
      },
      {
        name: "projects.exports.download_sync",
        signature: "client.projects.exports.download_sync(id, export_type='JSON', ...)",
        description: "Download annotations directly as a byte stream. Lower-level API for custom handling.",
        parameters: [
          { name: "id", type: "int", required: true, description: "Project ID" },
          { name: "export_type", type: "str", required: false, description: "Export format (default: JSON)" },
          { name: "download_all_tasks", type: "bool", required: false, description: "Include unannotated tasks" },
          { name: "download_resources", type: "bool", required: false, description: "Include media files" },
        ],
        returns: "Iterator[bytes]",
        example: {
          language: "python",
          code: `# Stream export data
for chunk in client.projects.exports.download_sync(
    id=123,
    export_type="JSON",
    download_all_tasks=True
):
    process_chunk(chunk)`
        }
      }
    ]
  }
];

// Annotation types reference
const annotationTypes = [
  { type: "classification", description: "Single-label image/text classification", dataTypes: "Image, Text, Audio" },
  { type: "multi_classification", description: "Multi-label classification", dataTypes: "Image, Text, Audio" },
  { type: "bounding_box", description: "Rectangular bounding boxes for object detection", dataTypes: "Image, Video" },
  { type: "polygon", description: "Polygon outlines for precise object shapes", dataTypes: "Image" },
  { type: "segmentation", description: "Pixel-level semantic segmentation", dataTypes: "Image" },
  { type: "keypoint", description: "Keypoint/skeleton detection", dataTypes: "Image, Video" },
  { type: "ner", description: "Named entity recognition in text", dataTypes: "Text" },
  { type: "sentiment", description: "Sentiment analysis", dataTypes: "Text" },
  { type: "transcription", description: "Audio/video transcription", dataTypes: "Audio, Video" },
];

// Copy to clipboard component
const CopyButton = ({ text }: { text: string }) => {
  const [copied, setCopied] = useState(false);

  const handleCopy = async (e: React.MouseEvent) => {
    e.stopPropagation();
    await navigator.clipboard.writeText(text);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <button onClick={handleCopy} className="copy-button" title="Copy to clipboard">
      {copied ? (
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
          <polyline points="20,6 9,17 4,12"/>
        </svg>
      ) : (
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
          <rect x="9" y="9" width="13" height="13" rx="2" ry="2"/>
          <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"/>
        </svg>
      )}
    </button>
  );
};

// Sidebar navigation
const Sidebar = ({ sections, activeSection, onSelect }: { 
  sections: SDKSection[]; 
  activeSection: string; 
  onSelect: (id: string) => void;
}) => (
  <aside className="api-sidebar">
    <div className="sidebar-header">
      <span className="sidebar-label">Python SDK</span>
    </div>
    <nav className="sidebar-nav">
      {sections.map((section) => (
        <button
          key={section.id}
          onClick={() => onSelect(section.id)}
          className={`sidebar-item ${activeSection === section.id ? 'active' : ''}`}
        >
          <span className="sidebar-icon">{section.icon}</span>
          <span>{section.name}</span>
          <span className="endpoint-count">{section.methods.length}</span>
        </button>
      ))}
    </nav>
    
    <div className="sidebar-footer">
      <a href="/docs/api/schema/swagger-ui/" className="swagger-link" target="_blank" rel="noopener noreferrer">
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
          <path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"/>
          <polyline points="15,3 21,3 21,9"/>
          <line x1="10" y1="14" x2="21" y2="3"/>
        </svg>
        REST API (Swagger)
      </a>
    </div>
  </aside>
);

// Method card component
const MethodCard = ({ method }: { method: SDKMethod }) => (
  <div className="method-card">
    <div className="method-header">
      <code className="method-name">{method.name}</code>
      <CopyButton text={method.example.code} />
    </div>
    <code className="method-signature">{method.signature}</code>
    <p className="method-description">{method.description}</p>
    
    {method.parameters && method.parameters.length > 0 && (
      <div className="method-params">
        <h4>Parameters</h4>
        <table className="params-table">
          <thead>
            <tr>
              <th>Name</th>
              <th>Type</th>
              <th>Required</th>
              <th>Description</th>
            </tr>
          </thead>
          <tbody>
            {method.parameters.map((param, idx) => (
              <tr key={idx}>
                <td><code>{param.name}</code></td>
                <td><code>{param.type}</code></td>
                <td>{param.required ? "✓" : ""}</td>
                <td>{param.description}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    )}
    
    {method.returns && (
      <div className="method-returns">
        <strong>Returns:</strong> <code>{method.returns}</code>
      </div>
    )}
    
    <div className="code-block">
      <div className="code-header">
        <span className="code-language">{method.example.language}</span>
        <CopyButton text={method.example.code} />
      </div>
      <pre className="code-content">{method.example.code}</pre>
    </div>
  </div>
);

// Section detail component
const SectionDetail = ({ section }: { section: SDKSection }) => (
  <motion.div
    initial={{ opacity: 0, y: 20 }}
    animate={{ opacity: 1, y: 0 }}
    exit={{ opacity: 0, y: -20 }}
    transition={{ duration: 0.3 }}
    className="category-detail"
  >
    <div className="category-header">
      <div className="category-icon">{section.icon}</div>
      <div>
        <h2 className="category-title">{section.name}</h2>
        <p className="category-description">{section.description}</p>
      </div>
    </div>
    
    <div className="methods-list">
      {section.methods.map((method, index) => (
        <MethodCard key={index} method={method} />
      ))}
    </div>
  </motion.div>
);

// Quick start workflow
const QuickStartWorkflow = () => {
  const workflowCode = `import synapse

# 1. Initialize client
client = synapse.Client(api_key="sk_live_xxxx")

# 2. Create annotation project
project = client.projects.create(
    name="Product Classification",
    annotation_type="classification",
    labels=["Electronics", "Clothing", "Food", "Other"]
)

# 3. Upload data from S3
project.upload_from_s3(
    bucket="my-training-data",
    prefix="images/products/"
)

# 4. Pay deposit and start
project.pay_deposit(payment_method="credits")

# 5. Wait for completion
project.wait_for_completion()

# 6. Export annotations
annotations = project.export(format="coco")

print(f"✅ Got {len(annotations)} annotations!")`;

  return (
    <div className="quickstart-section" id="quickstart">
      <div className="quickstart-header">
        <span className="quickstart-label">Complete Workflow</span>
        <h3 className="quickstart-title">From data to annotations in 6 steps</h3>
      </div>
      <div className="code-block">
        <div className="code-header">
          <span className="code-language">python</span>
          <CopyButton text={workflowCode} />
        </div>
        <pre className="code-content">{workflowCode}</pre>
      </div>
    </div>
  );
};

// Annotation types table
const AnnotationTypesSection = () => (
  <section className="annotation-types-section">
    <h3>Supported Annotation Types</h3>
    <div className="types-table-wrapper">
      <table className="types-table">
        <thead>
          <tr>
            <th>Type</th>
            <th>Description</th>
            <th>Data Types</th>
          </tr>
        </thead>
        <tbody>
          {annotationTypes.map((at, idx) => (
            <tr key={idx}>
              <td><code>{at.type}</code></td>
              <td>{at.description}</td>
              <td>{at.dataTypes}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  </section>
);

// Export formats section
const ExportFormatsSection = () => {
  const formats = [
    { format: "json", description: "Synapse JSON format", useCase: "General purpose" },
    { format: "coco", description: "COCO format", useCase: "Object detection, segmentation" },
    { format: "yolo", description: "YOLO format", useCase: "YOLO model training" },
    { format: "pascal_voc", description: "Pascal VOC XML", useCase: "Object detection" },
    { format: "csv", description: "CSV format", useCase: "Classification, tabular data" },
    { format: "spacy", description: "spaCy format", useCase: "NLP/NER models" },
  ];

  return (
    <section className="export-formats-section">
      <h3>Export Formats</h3>
      <div className="formats-grid">
        {formats.map((f, idx) => (
          <div key={idx} className="format-card">
            <code className="format-name">{f.format}</code>
            <p className="format-description">{f.description}</p>
            <span className="format-usecase">{f.useCase}</span>
          </div>
        ))}
      </div>
    </section>
  );
};

// Main page component
export const ApiDocsPage: Page = () => {
  const [activeSection, setActiveSection] = useState("installation");
  const currentSection = sdkSections.find((s) => s.id === activeSection) || sdkSections[0];

  return (
    <div className="api-docs-page">
      
      {/* Hero Section */}
      <section className="api-hero">
        <div className="hero-background">
          <div className="hero-grid" />
          <div className="hero-glow" />
        </div>
        <div className="hero-content">
          <motion.span
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5 }}
            className="hero-label"
          >
            Python SDK
          </motion.span>
          <motion.h1
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, delay: 0.1 }}
            className="hero-title"
          >
            Synapse SDK
            <span className="hero-version">v1.0</span>
          </motion.h1>
          <motion.p
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, delay: 0.2 }}
            className="hero-description"
          >
            Integrate Synapse annotations directly into your ML training pipelines.
            Create projects, upload data, and export annotations programmatically.
          </motion.p>
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, delay: 0.3 }}
            className="hero-actions"
          >
            <a href="#quickstart" className="btn-primary">
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <polygon points="5,3 19,12 5,21"/>
              </svg>
              Quick Start
            </a>
            <a href="/docs/api/schema/swagger-ui/" className="btn-secondary" target="_blank" rel="noopener noreferrer">
              REST API Reference
            </a>
          </motion.div>
        </div>
      </section>

      {/* Main Content */}
      <main className="api-main">
        <div className="api-container">
          {/* Sidebar */}
          <Sidebar 
            sections={sdkSections}
            activeSection={activeSection}
            onSelect={setActiveSection}
          />

          {/* Content Area */}
          <div className="api-content">
            <AnimatePresence mode="wait">
              <SectionDetail key={currentSection.id} section={currentSection} />
            </AnimatePresence>

            {/* Quick Start Workflow */}
            <QuickStartWorkflow />

            {/* Annotation Types */}
            <AnnotationTypesSection />

            {/* Export Formats */}
            <ExportFormatsSection />

            {/* Authentication Info */}
            <section className="auth-section">
              <div className="auth-header">
                <ClientIcon />
                <h3>Authentication</h3>
              </div>
              <div className="auth-content">
                <p>
                  All API requests require authentication using an API key. You can pass it directly
                  to the client or set it as an environment variable:
                </p>
                <div className="auth-example">
                  <code>export SYNAPSE_API_KEY=sk_live_xxxx</code>
                  <CopyButton text="export SYNAPSE_API_KEY=sk_live_xxxx" />
                </div>
                <p className="auth-note">
                  Get your API key from <a href="/user/account/">Account Settings</a>.
                  Keys starting with <code>sk_live_</code> are for production,
                  <code>sk_test_</code> for sandbox.
                </p>
              </div>
            </section>

            {/* Rate Limits */}
            <section className="rate-limits-section">
              <h3>Rate Limits</h3>
              <div className="rate-limits-grid">
                <div className="rate-limit-card">
                  <span className="rate-value">1,000</span>
                  <span className="rate-label">requests/minute</span>
                  <span className="rate-tier">Standard</span>
                </div>
                <div className="rate-limit-card">
                  <span className="rate-value">10,000</span>
                  <span className="rate-label">requests/minute</span>
                  <span className="rate-tier">Enterprise</span>
                </div>
              </div>
            </section>
          </div>
        </div>
      </main>
    </div>
  );
};

ApiDocsPage.title = "API Documentation";
ApiDocsPage.path = "/docs";
ApiDocsPage.exact = true;
