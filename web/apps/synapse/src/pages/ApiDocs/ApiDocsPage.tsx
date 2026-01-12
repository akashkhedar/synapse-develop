import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import type { Page } from "../types/Page";
import "./ApiDocsPage.css";

// API Category data structure
interface Endpoint {
  method: "GET" | "POST" | "PUT" | "PATCH" | "DELETE";
  path: string;
  description: string;
  auth?: boolean;
}

interface ApiCategory {
  id: string;
  name: string;
  description: string;
  icon: React.ReactNode;
  endpoints: Endpoint[];
}

// SVG Icons
const AuthIcon = () => (
  <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <rect x="3" y="11" width="18" height="11" rx="2" ry="2"/>
    <path d="M7 11V7a5 5 0 0 1 10 0v4"/>
  </svg>
);

const ProjectIcon = () => (
  <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z"/>
  </svg>
);

const TaskIcon = () => (
  <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <path d="M9 11l3 3L22 4"/>
    <path d="M21 12v7a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11"/>
  </svg>
);

const AnnotationIcon = () => (
  <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <path d="M12 20h9"/>
    <path d="M16.5 3.5a2.121 2.121 0 0 1 3 3L7 19l-4 1 1-4L16.5 3.5z"/>
  </svg>
);

const ExportIcon = () => (
  <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>
    <polyline points="17,8 12,3 7,8"/>
    <line x1="12" y1="3" x2="12" y2="15"/>
  </svg>
);

const WebhookIcon = () => (
  <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <path d="M18 16.98h-5.99c-1.1 0-1.95.94-2.48 1.9A4 4 0 0 1 2 17c.01-.7.2-1.4.57-2"/>
    <path d="M6 17a4 4 0 0 1 1.67-3.25c.43-.32.96-.44 1.5-.35.54.1 1.04.4 1.4.84.56.67.85 1.5.85 2.37 0 .87-.3 1.7-.85 2.39"/>
    <circle cx="12" cy="6" r="4"/>
    <path d="M12 10v8"/>
  </svg>
);

const UserIcon = () => (
  <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/>
    <circle cx="12" cy="7" r="4"/>
  </svg>
);

const OrganizationIcon = () => (
  <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/>
    <circle cx="9" cy="7" r="4"/>
    <path d="M23 21v-2a4 4 0 0 0-3-3.87"/>
    <path d="M16 3.13a4 4 0 0 1 0 7.75"/>
  </svg>
);

const AnnotatorIcon = () => (
  <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <circle cx="12" cy="12" r="10"/>
    <path d="M12 16v-4"/>
    <path d="M12 8h.01"/>
  </svg>
);

const StorageIcon = () => (
  <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <ellipse cx="12" cy="5" rx="9" ry="3"/>
    <path d="M21 12c0 1.66-4 3-9 3s-9-1.34-9-3"/>
    <path d="M3 5v14c0 1.66 4 3 9 3s9-1.34 9-3V5"/>
  </svg>
);

// API Categories Data
const apiCategories: ApiCategory[] = [
  {
    id: "authentication",
    name: "Authentication",
    description: "Authenticate users and manage API tokens for secure access",
    icon: <AuthIcon />,
    endpoints: [
      { method: "POST", path: "/api/current-user/token", description: "Get API token for authenticated user", auth: true },
      { method: "POST", path: "/api/current-user/reset-token/", description: "Reset and regenerate API token", auth: true },
      { method: "GET", path: "/api/current-user/whoami", description: "Get current authenticated user info", auth: true },
    ],
  },
  {
    id: "projects",
    name: "Projects",
    description: "Create, manage, and configure annotation projects",
    icon: <ProjectIcon />,
    endpoints: [
      { method: "GET", path: "/api/projects/", description: "List all projects", auth: true },
      { method: "POST", path: "/api/projects/", description: "Create a new project", auth: true },
      { method: "GET", path: "/api/projects/{id}/", description: "Get project details", auth: true },
      { method: "PATCH", path: "/api/projects/{id}/", description: "Update project settings", auth: true },
      { method: "DELETE", path: "/api/projects/{id}/", description: "Delete a project", auth: true },
      { method: "POST", path: "/api/projects/{id}/import", description: "Import tasks to project", auth: true },
      { method: "GET", path: "/api/projects/{id}/summary", description: "Get project statistics", auth: true },
    ],
  },
  {
    id: "tasks",
    name: "Tasks",
    description: "Manage annotation tasks and their lifecycle",
    icon: <TaskIcon />,
    endpoints: [
      { method: "GET", path: "/api/tasks/", description: "List tasks with filtering", auth: true },
      { method: "POST", path: "/api/tasks/", description: "Create a new task", auth: true },
      { method: "GET", path: "/api/tasks/{id}/", description: "Get task details", auth: true },
      { method: "PATCH", path: "/api/tasks/{id}/", description: "Update task data", auth: true },
      { method: "DELETE", path: "/api/tasks/{id}/", description: "Delete a task", auth: true },
      { method: "GET", path: "/api/tasks/{id}/annotations/", description: "Get task annotations", auth: true },
      { method: "GET", path: "/api/tasks/{id}/drafts", description: "Get annotation drafts", auth: true },
    ],
  },
  {
    id: "annotations",
    name: "Annotations",
    description: "Create, update, and manage annotation data",
    icon: <AnnotationIcon />,
    endpoints: [
      { method: "GET", path: "/api/annotations/{id}/", description: "Get annotation by ID", auth: true },
      { method: "PATCH", path: "/api/annotations/{id}/", description: "Update annotation", auth: true },
      { method: "DELETE", path: "/api/annotations/{id}/", description: "Delete annotation", auth: true },
      { method: "POST", path: "/api/annotations/{id}/convert-to-draft", description: "Convert to draft", auth: true },
      { method: "GET", path: "/api/drafts/{id}/", description: "Get draft by ID", auth: true },
      { method: "PATCH", path: "/api/drafts/{id}/", description: "Update draft", auth: true },
      { method: "DELETE", path: "/api/drafts/{id}/", description: "Delete draft", auth: true },
    ],
  },
  {
    id: "export",
    name: "Data Export",
    description: "Export annotation data in various formats",
    icon: <ExportIcon />,
    endpoints: [
      { method: "POST", path: "/api/projects/{id}/export", description: "Trigger data export", auth: true },
      { method: "GET", path: "/api/projects/{id}/export/formats", description: "List available formats", auth: true },
      { method: "GET", path: "/api/projects/{id}/exports/", description: "List project exports", auth: true },
      { method: "GET", path: "/api/projects/{id}/exports/{export_id}", description: "Get export details", auth: true },
      { method: "GET", path: "/api/projects/{id}/exports/{export_id}/download", description: "Download export file", auth: true },
    ],
  },
  {
    id: "webhooks",
    name: "Webhooks",
    description: "Configure event-driven integrations",
    icon: <WebhookIcon />,
    endpoints: [
      { method: "GET", path: "/api/webhooks/", description: "List all webhooks", auth: true },
      { method: "POST", path: "/api/webhooks/", description: "Create a webhook", auth: true },
      { method: "GET", path: "/api/webhooks/{id}/", description: "Get webhook details", auth: true },
      { method: "PATCH", path: "/api/webhooks/{id}/", description: "Update webhook", auth: true },
      { method: "DELETE", path: "/api/webhooks/{id}/", description: "Delete webhook", auth: true },
      { method: "GET", path: "/api/webhooks/info/", description: "Get webhook event types", auth: true },
    ],
  },
  {
    id: "users",
    name: "Users",
    description: "Manage user accounts and permissions",
    icon: <UserIcon />,
    endpoints: [
      { method: "GET", path: "/api/users/", description: "List all users", auth: true },
      { method: "GET", path: "/api/users/{id}/", description: "Get user details", auth: true },
      { method: "PATCH", path: "/api/users/{id}/", description: "Update user profile", auth: true },
      { method: "DELETE", path: "/api/users/{id}/", description: "Delete user account", auth: true },
    ],
  },
  {
    id: "organizations",
    name: "Organizations",
    description: "Manage organizations and team memberships",
    icon: <OrganizationIcon />,
    endpoints: [
      { method: "GET", path: "/api/organizations/", description: "List organizations", auth: true },
      { method: "GET", path: "/api/organizations/{id}/", description: "Get organization details", auth: true },
      { method: "PATCH", path: "/api/organizations/{id}/", description: "Update organization", auth: true },
      { method: "GET", path: "/api/organizations/{id}/memberships/", description: "List members", auth: true },
      { method: "POST", path: "/api/organizations/{id}/memberships/{user_id}/promote", description: "Promote member", auth: true },
      { method: "POST", path: "/api/organizations/{id}/memberships/{user_id}/demote", description: "Demote member", auth: true },
    ],
  },
  {
    id: "annotators",
    name: "Annotators",
    description: "Manage annotator profiles, assignments, and performance",
    icon: <AnnotatorIcon />,
    endpoints: [
      { method: "GET", path: "/api/annotators/profile/", description: "Get annotator profile", auth: true },
      { method: "PATCH", path: "/api/annotators/profile/", description: "Update profile", auth: true },
      { method: "GET", path: "/api/annotators/assignments/", description: "Get task assignments", auth: true },
      { method: "POST", path: "/api/annotators/assignments/{id}/submit/", description: "Submit annotation", auth: true },
      { method: "GET", path: "/api/annotators/earnings/", description: "Get earnings summary", auth: true },
      { method: "GET", path: "/api/annotators/performance/", description: "Get performance stats", auth: true },
      { method: "GET", path: "/api/annotators/leaderboard/", description: "Get leaderboard", auth: true },
    ],
  },
  {
    id: "storage",
    name: "Cloud Storage",
    description: "Connect external cloud storage for data import/export",
    icon: <StorageIcon />,
    endpoints: [
      { method: "GET", path: "/api/storages/s3/", description: "List S3 connections", auth: true },
      { method: "POST", path: "/api/storages/s3/", description: "Create S3 connection", auth: true },
      { method: "GET", path: "/api/storages/gcs/", description: "List GCS connections", auth: true },
      { method: "POST", path: "/api/storages/gcs/", description: "Create GCS connection", auth: true },
      { method: "GET", path: "/api/storages/azure/", description: "List Azure connections", auth: true },
      { method: "POST", path: "/api/storages/azure/", description: "Create Azure connection", auth: true },
    ],
  },
];

// Method color helper
const getMethodColor = (method: string) => {
  switch (method) {
    case "GET": return "method-get";
    case "POST": return "method-post";
    case "PUT": return "method-put";
    case "PATCH": return "method-patch";
    case "DELETE": return "method-delete";
    default: return "";
  }
};

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
    <button 
      onClick={handleCopy}
      className="copy-button"
      title="Copy to clipboard"
    >
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

// Sidebar navigation component
const Sidebar = ({ 
  categories, 
  activeCategory, 
  onCategorySelect 
}: { 
  categories: ApiCategory[]; 
  activeCategory: string; 
  onCategorySelect: (id: string) => void;
}) => (
  <aside className="api-sidebar">
    <div className="sidebar-header">
      <span className="sidebar-label">API Reference</span>
    </div>
    <nav className="sidebar-nav">
      {categories.map((category) => (
        <button
          key={category.id}
          onClick={() => onCategorySelect(category.id)}
          className={`sidebar-item ${activeCategory === category.id ? 'active' : ''}`}
        >
          <span className="sidebar-icon">{category.icon}</span>
          <span>{category.name}</span>
          <span className="endpoint-count">{category.endpoints.length}</span>
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
        Swagger UI
      </a>
      <a href="/docs/api/schema/redoc/" className="redoc-link" target="_blank" rel="noopener noreferrer">
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
          <path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20"/>
          <path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z"/>
        </svg>
        ReDoc
      </a>
    </div>
  </aside>
);

// Endpoint item component
const EndpointItem = ({ endpoint }: { endpoint: Endpoint }) => (
  <div className="endpoint-item">
    <div className="endpoint-main">
      <span className={`method-badge ${getMethodColor(endpoint.method)}`}>
        {endpoint.method}
      </span>
      <code className="endpoint-path">{endpoint.path}</code>
      <CopyButton text={endpoint.path} />
    </div>
    <p className="endpoint-description">{endpoint.description}</p>
  </div>
);

// Category detail component
const CategoryDetail = ({ category }: { category: ApiCategory }) => (
  <motion.div
    initial={{ opacity: 0, y: 20 }}
    animate={{ opacity: 1, y: 0 }}
    exit={{ opacity: 0, y: -20 }}
    transition={{ duration: 0.3 }}
    className="category-detail"
  >
    <div className="category-header">
      <div className="category-icon">{category.icon}</div>
      <div>
        <h2 className="category-title">{category.name}</h2>
        <p className="category-description">{category.description}</p>
      </div>
    </div>
    
    <div className="endpoints-list">
      {category.endpoints.map((endpoint, index) => (
        <EndpointItem key={index} endpoint={endpoint} />
      ))}
    </div>
  </motion.div>
);

// Quick start code example
const QuickStartCode = () => {
  const code = `# Authentication with API Token
curl -X GET "https://api.synapse.ai/api/projects/" \\
  -H "Authorization: Token YOUR_API_TOKEN" \\
  -H "Content-Type: application/json"

# Create a new project
curl -X POST "https://api.synapse.ai/api/projects/" \\
  -H "Authorization: Token YOUR_API_TOKEN" \\
  -H "Content-Type: application/json" \\
  -d '{"title": "My Project", "description": "Image classification"}'

# Import tasks
curl -X POST "https://api.synapse.ai/api/projects/1/import" \\
  -H "Authorization: Token YOUR_API_TOKEN" \\
  -H "Content-Type: application/json" \\
  -d '[{"image": "https://example.com/image1.jpg"}]'`;

  return (
    <div className="quickstart-section">
      <div className="quickstart-header">
        <span className="quickstart-label">Quick Start</span>
        <h3 className="quickstart-title">Get started in minutes</h3>
      </div>
      <div className="code-block">
        <div className="code-header">
          <span className="code-language">bash</span>
          <CopyButton text={code} />
        </div>
        <pre className="code-content">{code}</pre>
      </div>
    </div>
  );
};

export const ApiDocsPage: Page = () => {
  const [activeCategory, setActiveCategory] = useState("authentication");
  const currentCategory = apiCategories.find((c) => c.id === activeCategory) || apiCategories[0];

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
            API-First Platform
          </motion.span>
          <motion.h1
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, delay: 0.1 }}
            className="hero-title"
          >
            Synapse API
            <span className="hero-version">v1.0</span>
          </motion.h1>
          <motion.p
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, delay: 0.2 }}
            className="hero-description"
          >
            Integrate Synapse directly into your systems with our comprehensive REST API.
            Build powerful annotation workflows, manage projects, and export data programmatically.
          </motion.p>
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, delay: 0.3 }}
            className="hero-actions"
          >
            <a href="/docs/api/schema/json/" className="btn-primary" target="_blank" rel="noopener noreferrer">
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
                <polyline points="14,2 14,8 20,8"/>
                <line x1="16" y1="13" x2="8" y2="13"/>
                <line x1="16" y1="17" x2="8" y2="17"/>
                <polyline points="10,9 9,9 8,9"/>
              </svg>
              OpenAPI Schema
            </a>
            <a href="#quickstart" className="btn-secondary">
              Quick Start Guide
            </a>
          </motion.div>
        </div>
      </section>

      {/* Main Content */}
      <main className="api-main">
        <div className="api-container">
          {/* Sidebar */}
          <Sidebar 
            categories={apiCategories}
            activeCategory={activeCategory}
            onCategorySelect={setActiveCategory}
          />

          {/* Content Area */}
          <div className="api-content">
            <AnimatePresence mode="wait">
              <CategoryDetail key={currentCategory.id} category={currentCategory} />
            </AnimatePresence>

            {/* Quick Start Section */}
            <div id="quickstart">
              <QuickStartCode />
            </div>

            {/* Authentication Info */}
            <section className="auth-section">
              <div className="auth-header">
                <AuthIcon />
                <h3>Authentication</h3>
              </div>
              <div className="auth-content">
                <p>
                  All API requests require authentication using an API token. Include your token
                  in the <code>Authorization</code> header:
                </p>
                <div className="auth-example">
                  <code>Authorization: Token YOUR_API_TOKEN</code>
                  <CopyButton text="Authorization: Token YOUR_API_TOKEN" />
                </div>
                <p className="auth-note">
                  You can generate or reset your API token from the 
                  <a href="/user/account/"> Account Settings</a> page.
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

