# Synapse Frontend Architecture

> Last Updated: February 7, 2026

## Overview

The Synapse frontend is an **NX monorepo** containing multiple React applications and shared libraries. It uses React 18, MobX State Tree for state management, and Tailwind CSS for styling. The frontend is built with Webpack and integrates with the Django backend via REST APIs.

---

## Table of Contents

1. [Monorepo Structure](#monorepo-structure)
2. [Applications](#applications)
3. [Shared Libraries](#shared-libraries)
4. [Page Structure](#page-structure)
5. [Component Architecture](#component-architecture)
6. [State Management](#state-management)
7. [Styling System](#styling-system)
8. [Build & Development](#build--development)

---

## Monorepo Structure

```
web/
├── apps/                        # Standalone applications
│   ├── synapse/                 # Main application
│   ├── synapse-e2e/             # E2E tests
│   └── playground/              # Component playground
│
├── libs/                        # Shared libraries
│   ├── editor/                  # Annotation editor (Synapse Frontend)
│   ├── datamanager/             # Data exploration & management
│   ├── ui/                      # Shared UI components
│   ├── core/                    # Core utilities
│   ├── app-common/              # Common application logic
│   ├── audio-file-decoder/      # Audio processing
│   ├── storybook/               # Storybook configuration
│   └── frontend-test/           # Test utilities
│
├── tools/                       # Build tools & scripts
│
├── package.json                 # Root dependencies
├── nx.json                      # NX configuration
├── tsconfig.base.json           # TypeScript base config
├── tailwind.config.js           # Tailwind CSS config
├── webpack.config.js            # Webpack configuration
└── biome.json                   # Linter/formatter config
```

### Root Configuration Files

| File | Purpose |
|------|---------|
| `package.json` | NPM dependencies and scripts |
| `nx.json` | NX monorepo configuration, caching, task runners |
| `tsconfig.base.json` | Base TypeScript config with path aliases |
| `tsconfig.json` | Root TypeScript configuration |
| `webpack.config.js` | Webpack bundling configuration |
| `babel.config.json` | Babel transpiler settings |
| `tailwind.config.js` | Tailwind CSS theme customization |
| `postcss.config.js` | PostCSS plugins |
| `biome.json` | Biome linter/formatter rules |
| `design-tokens.json` | Design system tokens |
| `components.json` | Shadcn UI configuration |

---

## Applications

### 1. Main Application (`apps/synapse/`)

The primary Synapse application that users interact with.

```
apps/synapse/
├── src/
│   ├── main.tsx                 # Application entry point
│   ├── index.html               # HTML template
│   │
│   ├── app/                     # App-level components
│   │   ├── App.tsx              # Root component
│   │   └── ...
│   │
│   ├── pages/                   # Page components
│   │   ├── Landing/             # Public landing page
│   │   ├── Signup/              # User registration
│   │   ├── Projects/            # Project management
│   │   ├── Billing/             # Billing & credits
│   │   ├── Annotators/          # Annotator portal
│   │   ├── Expert/              # Expert review portal
│   │   ├── DataManager/         # Data management
│   │   ├── Settings/            # User/org settings
│   │   └── ...
│   │
│   ├── components/              # Shared page components
│   │   ├── Header/
│   │   ├── Footer/
│   │   ├── Sidebar/
│   │   ├── Features/
│   │   └── ...
│   │
│   ├── services/                # API services
│   │   ├── api.ts               # API client
│   │   └── ...
│   │
│   ├── hooks/                   # Custom React hooks
│   ├── providers/               # Context providers
│   ├── routes/                  # Route definitions
│   ├── config/                  # App configuration
│   ├── themes/                  # Theme configuration
│   ├── types/                   # TypeScript types
│   ├── utils/                   # Utility functions
│   └── assets/                  # Static assets
│
├── project.json                 # NX project config
└── webpack.config.js            # App-specific webpack
```

### 2. Playground (`apps/playground/`)

Development environment for testing components in isolation.

```
apps/playground/
├── src/
│   ├── main.tsx                 # Entry point
│   ├── index.html
│   ├── PlaygroundApp.tsx        # Main app component
│   ├── EditorPanel.tsx          # Code editor
│   └── PreviewPanel.tsx         # Live preview
│
└── project.json
```

**Features:**
- XML config editor
- Live annotation preview
- Sample task input
- Annotation output viewer

### 3. E2E Tests (`apps/synapse-e2e/`)

End-to-end tests using Playwright/Cypress.

```
apps/synapse-e2e/
├── src/
│   ├── e2e/
│   │   ├── auth.spec.ts
│   │   ├── projects.spec.ts
│   │   └── ...
│   └── fixtures/
└── project.json
```

---

## Shared Libraries

### 1. Editor Library (`libs/editor/`)

The core annotation interface - **Synapse Frontend (SF)**.

```
libs/editor/src/
├── index.js                     # Main export
├── Synapse.tsx                  # Main component
├── Component.jsx                # Base component
├── standalone.js                # Standalone build entry
│
├── components/                  # UI components
│   ├── App/                     # Main app wrapper
│   ├── AnnotationCanvas/        # Canvas for visual annotations
│   ├── Timeline/                # Video/audio timeline
│   ├── Toolbar/                 # Annotation tools
│   ├── SidePanel/               # Side panels
│   └── ...
│
├── tags/                        # Annotation tag components
│   ├── control/                 # Control tags (Choices, Labels, etc.)
│   ├── object/                  # Object tags (Image, Text, Audio, etc.)
│   └── visual/                  # Visual tags (View, Header, etc.)
│
├── tools/                       # Annotation tools
│   ├── Rectangle.js             # Bounding box tool
│   ├── Polygon.js               # Polygon tool
│   ├── Brush.js                 # Brush/segmentation tool
│   ├── Keypoint.js              # Keypoint tool
│   └── ...
│
├── regions/                     # Region types
│   ├── RectRegion/              # Rectangle regions
│   ├── PolygonRegion/           # Polygon regions
│   ├── BrushRegion/             # Brush regions
│   ├── KeyPointRegion/          # Keypoint regions
│   ├── TextRegion/              # Text/NER regions
│   └── ...
│
├── stores/                      # MobX State Tree stores
│   ├── AnnotationStore.js       # Annotation state
│   ├── TaskStore.js             # Task state
│   ├── AppStore.js              # App-level state
│   └── ...
│
├── mixins/                      # Reusable store mixins
├── hooks/                       # React hooks
├── utils/                       # Utilities
├── lib/                         # Third-party integrations
├── styles/                      # SCSS styles
├── assets/                      # Icons, images
└── core/                        # Core configuration
```

**Key Features:**
- XML-based label configuration parsing
- Multi-modal annotation (image, text, audio, video)
- Tool system (rectangle, polygon, brush, etc.)
- Region management
- Annotation history (undo/redo)
- Keyboard shortcuts

### 2. Data Manager Library (`libs/datamanager/`)

Data exploration and task management interface.

```
libs/datamanager/src/
├── index.js                     # Main export
├── DataManager.tsx              # Main component
│
├── components/                  # UI components
│   ├── DataGrid/                # Task data grid
│   ├── Filters/                 # Advanced filters
│   ├── Columns/                 # Column configuration
│   ├── Actions/                 # Bulk actions
│   ├── Pagination/              # Pagination
│   └── ...
│
├── stores/                      # State management
│   ├── DataStore.js
│   ├── FilterStore.js
│   ├── ViewStore.js
│   └── ...
│
├── api/                         # API integration
├── hooks/                       # Custom hooks
└── utils/                       # Utilities
```

**Key Features:**
- Task listing with virtual scrolling
- Advanced filtering (by label, status, date, etc.)
- Column customization
- Bulk operations (delete, update, export)
- View management (saved filter views)

### 3. UI Library (`libs/ui/`)

Shared React components and design system.

```
libs/ui/src/
├── index.ts                     # All exports
├── styles.scss                  # Global styles
├── tailwind.css                 # Tailwind imports
├── tailwind.config.js           # UI-specific Tailwind config
│
├── lib/                         # Core components
│   ├── button/
│   │   ├── Button.tsx
│   │   ├── Button.stories.tsx
│   │   └── index.ts
│   ├── input/
│   ├── modal/
│   ├── dropdown/
│   ├── card/
│   ├── table/
│   ├── tabs/
│   ├── tooltip/
│   ├── typography/
│   └── ...
│
├── shad/                        # Shadcn UI components
│   ├── button/
│   ├── dialog/
│   ├── select/
│   └── ...
│
├── tokens/                      # Design tokens
│   ├── colors.ts
│   ├── spacing.ts
│   ├── typography.ts
│   └── ...
│
├── hooks/                       # UI hooks
│   ├── useModal.ts
│   ├── useToast.ts
│   └── ...
│
├── utils/                       # UI utilities
└── assets/                      # Icons, fonts
```

**Component Categories:**

| Category | Components |
|----------|------------|
| **Layout** | Container, Grid, Flex, Spacer |
| **Navigation** | Navbar, Sidebar, Tabs, Breadcrumb |
| **Forms** | Input, Select, Checkbox, Radio, Switch |
| **Feedback** | Alert, Toast, Progress, Spinner |
| **Overlay** | Modal, Drawer, Popover, Tooltip |
| **Data Display** | Card, Table, List, Avatar, Badge |
| **Typography** | Heading, Text, Label, Code |

### 4. Core Library (`libs/core/`)

Shared utilities and type definitions.

```
libs/core/src/
├── index.ts
├── types/                       # TypeScript types
├── constants/                   # Constants
├── utils/                       # Utility functions
│   ├── format.ts
│   ├── validate.ts
│   ├── date.ts
│   └── ...
└── helpers/
```

### 5. App Common Library (`libs/app-common/`)

Common application logic shared across apps.

```
libs/app-common/src/
├── api/                         # API clients
│   ├── client.ts
│   ├── projects.ts
│   ├── tasks.ts
│   ├── annotations.ts
│   └── ...
│
├── stores/                      # Shared stores
├── hooks/                       # Common hooks
├── providers/                   # Context providers
└── utils/
```

---

## Page Structure

### Main Application Pages

```
pages/
├── Landing/                     # Public pages
│   ├── components/
│   │   ├── Navigation.tsx
│   │   ├── HeroSection.tsx
│   │   ├── FeaturesSection.tsx
│   │   ├── ProductsSection.tsx
│   │   ├── TrustSection.tsx
│   │   ├── CTASection.tsx
│   │   └── Footer.tsx
│   └── SynapseLanding.tsx
│
├── Signup/                      # Registration
│   ├── Signup.tsx
│   └── Signup.scss
│
├── Projects/                    # Project management
│   ├── Projects.jsx
│   ├── ProjectsList.jsx
│   └── Projects.scss
│
├── CreateProject/               # Project creation wizard
│   └── CreateProject.tsx
│
├── DataManager/                 # Data management
│   └── DataManager.tsx
│
├── DataViewer/                  # Individual task view
│   └── DataViewer.tsx
│
├── ExportPage/                  # Data export
│   └── ExportPage.tsx
│
├── Billing/                     # Billing pages
│   ├── BillingPage.tsx          # Credit dashboard
│   ├── PricingPage.tsx          # Pricing plans
│   ├── CreditDashboard.tsx      # Credit overview
│   ├── RazorpayCheckout.tsx     # Payment checkout
│   ├── BillingPage.css
│   └── PricingPage.css
│
├── Annotators/                  # Annotator portal
│   ├── AnnotatorSignup.tsx      # Annotator registration
│   ├── AnnotatorLogin.tsx       # Annotator login
│   ├── VerifyEmail.tsx          # Email verification
│   ├── VerificationSent.tsx     # Verification pending
│   ├── AnnotatorTest.tsx        # Qualification test
│   ├── AnnotatorSkillTest.tsx   # Skill assessment
│   ├── ExpertiseTest.tsx        # Expertise qualification test
│   ├── TestResult.tsx           # Test results
│   ├── EarningsDashboard.tsx    # Earnings overview with charts
│   ├── PayoutRequest.tsx        # Payout requests
│   └── components/
│       ├── TaskCard.tsx
│       ├── EarningsChart.tsx
│       ├── ExpertiseSection.tsx     # Expertise badges display
│       ├── ExpertiseIcons.tsx       # SVG icons for expertise
│       ├── TestResultsDisplay.tsx   # Test result component
│       ├── SpecialtySelection.tsx   # Specialty picker
│       └── ...
│
├── Expert/                      # Expert review portal
│   └── ExpertDashboard.tsx
│
├── Settings/                    # Settings pages
│   ├── AccountSettings.tsx
│   ├── OrganizationSettings.tsx
│   ├── APISettings.tsx
│   └── ...
│
├── Organization/                # Organization management
│   ├── OrganizationPage.tsx
│   └── MemberManagement.tsx
│
├── WebhookPage/                 # Webhook configuration
│   └── WebhookPage.tsx
│
├── ApiDocs/                     # API documentation
│   └── ApiDocs.tsx
│
├── Blog/                        # Blog pages
│   └── BlogPostPage.tsx
│
├── Services/                    # Services page
│   └── ServicesPage.tsx
│
├── Contact/                     # Contact page
│   └── ContactPage.tsx
│
├── About/                       # About page
│   └── AboutPage.tsx
│
├── Security/                    # Security page
│   └── SecurityPage.tsx
│
├── Resources/                   # Resources page
│   └── ResourcesPage.tsx
│
└── AcceptInvite/                # Invite acceptance
    └── AcceptInvite.tsx
```

### Page Component Pattern

Each page follows a consistent pattern:

```tsx
// pages/Billing/BillingPage.tsx

import { useState, useEffect } from 'react';
import { Typography, Card, Button } from '@synapse/ui';
import { useBilling } from '../../hooks/useBilling';
import './BillingPage.css';

interface BillingPageProps {
  // props
}

export const BillingPage: React.FC<BillingPageProps> = () => {
  const { credits, transactions, loading } = useBilling();
  
  return (
    <div className="billing-page">
      <header className="billing-header">
        <Typography variant="headline" size="large">
          Billing & Credits
        </Typography>
      </header>
      
      <section className="credit-overview">
        <Card>
          <Typography>Available Credits: {credits}</Typography>
        </Card>
      </section>
      
      <section className="transaction-history">
        {/* Transaction list */}
      </section>
    </div>
  );
};
```

---

## Component Architecture

### Component Hierarchy

```
App
├── Providers (Context, Theme, Auth)
│   └── Router
│       ├── PublicRoutes
│       │   ├── LandingPage
│       │   ├── LoginPage
│       │   └── SignupPage
│       │
│       ├── AuthenticatedRoutes
│       │   ├── Layout (Header, Sidebar, Content)
│       │   │   ├── ProjectsPage
│       │   │   ├── DataManagerPage
│       │   │   ├── BillingPage
│       │   │   └── SettingsPage
│       │   │
│       │   └── AnnotationView
│       │       └── SynapseEditor
│       │
│       └── AnnotatorRoutes
│           ├── AnnotatorDashboard
│           ├── AnnotationInterface
│           └── EarningsPage
```

### Component Types

#### 1. Page Components

Top-level components rendered by routes.

```tsx
// Full page component
export const ProjectsPage: Page = () => {
  return (
    <PageLayout>
      <PageHeader title="Projects" />
      <PageContent>
        <ProjectsList />
      </PageContent>
    </PageLayout>
  );
};
```

#### 2. Feature Components

Complex components with business logic.

```tsx
// Feature component with state and API calls
export const ProjectsList: React.FC = () => {
  const { projects, loading, fetchProjects } = useProjects();
  
  useEffect(() => {
    fetchProjects();
  }, []);
  
  return (
    <div className="projects-list">
      {projects.map(project => (
        <ProjectCard key={project.id} project={project} />
      ))}
    </div>
  );
};
```

#### 3. UI Components

Reusable presentational components.

```tsx
// Pure UI component from libs/ui
export const Button: React.FC<ButtonProps> = ({
  variant = 'primary',
  size = 'medium',
  children,
  ...props
}) => {
  return (
    <button 
      className={`btn btn-${variant} btn-${size}`}
      {...props}
    >
      {children}
    </button>
  );
};
```

---

## State Management

### MobX State Tree (Editor)

The annotation editor uses MobX State Tree for complex state:

```typescript
// stores/AnnotationStore.js
import { types, flow } from 'mobx-state-tree';

export const AnnotationStore = types
  .model('AnnotationStore', {
    annotations: types.array(Annotation),
    currentAnnotation: types.maybeNull(types.reference(Annotation)),
    history: types.optional(types.array(HistoryItem), []),
  })
  .views(self => ({
    get selectedAnnotation() {
      return self.currentAnnotation;
    },
    get annotationCount() {
      return self.annotations.length;
    },
  }))
  .actions(self => ({
    addAnnotation(data) {
      const annotation = Annotation.create(data);
      self.annotations.push(annotation);
      self.currentAnnotation = annotation;
    },
    deleteAnnotation(id) {
      const index = self.annotations.findIndex(a => a.id === id);
      if (index !== -1) {
        self.annotations.splice(index, 1);
      }
    },
    undo() {
      // Restore previous state
    },
    redo() {
      // Restore next state
    },
  }));
```

### React Context (App State)

Application-level state uses React Context:

```tsx
// providers/AuthProvider.tsx
export const AuthContext = createContext<AuthContextType>(null);

export const AuthProvider: React.FC<Props> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);
  
  const login = async (credentials: LoginCredentials) => {
    const response = await api.auth.login(credentials);
    setUser(response.user);
  };
  
  const logout = async () => {
    await api.auth.logout();
    setUser(null);
  };
  
  return (
    <AuthContext.Provider value={{ user, loading, login, logout }}>
      {children}
    </AuthContext.Provider>
  );
};
```

### Custom Hooks

```tsx
// hooks/useProjects.ts
export const useProjects = () => {
  const [projects, setProjects] = useState<Project[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<Error | null>(null);
  
  const fetchProjects = async () => {
    setLoading(true);
    try {
      const data = await api.projects.list();
      setProjects(data);
    } catch (err) {
      setError(err);
    } finally {
      setLoading(false);
    }
  };
  
  const createProject = async (data: CreateProjectData) => {
    const project = await api.projects.create(data);
    setProjects([...projects, project]);
    return project;
  };
  
  return { projects, loading, error, fetchProjects, createProject };
};
```

---

## Styling System

### Tailwind CSS

Primary styling approach using utility classes:

```tsx
<div className="flex items-center justify-between p-4 bg-white rounded-lg shadow-md">
  <Typography className="text-lg font-semibold text-gray-900">
    Project Title
  </Typography>
  <Button className="bg-blue-500 hover:bg-blue-600 text-white px-4 py-2">
    View
  </Button>
</div>
```

### Design Tokens

Centralized design tokens in `design-tokens.json`:

```json
{
  "colors": {
    "primary": {
      "50": "#fff7ed",
      "500": "#f97316",
      "900": "#7c2d12"
    },
    "neutral": {
      "50": "#fafafa",
      "500": "#737373",
      "900": "#171717"
    }
  },
  "spacing": {
    "0": "0",
    "1": "0.25rem",
    "2": "0.5rem",
    "4": "1rem",
    "8": "2rem"
  },
  "typography": {
    "fontFamily": {
      "sans": "Inter, system-ui, sans-serif",
      "mono": "JetBrains Mono, monospace"
    }
  }
}
```

### SCSS Modules

Component-specific styles using SCSS:

```scss
// pages/Billing/BillingPage.scss
.billing-page {
  padding: 2rem;
  
  .billing-header {
    margin-bottom: 1.5rem;
    
    h1 {
      font-size: 1.5rem;
      font-weight: 600;
    }
  }
  
  .credit-card {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    border-radius: 1rem;
    padding: 1.5rem;
    color: white;
  }
}
```

### Theme Configuration

Tailwind theme extends design tokens:

```javascript
// tailwind.config.js
module.exports = {
  theme: {
    extend: {
      colors: {
        'accent-orange': '#ff7557',
        'accent-peach': '#ff9c66',
        'accent-grape': '#667eea',
        'neutral-surface': '#fafafa',
        'neutral-surface-emphasis': '#f5f5f5',
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
        mono: ['JetBrains Mono', 'monospace'],
      },
    },
  },
  plugins: [
    require('@tailwindcss/forms'),
    require('@tailwindcss/typography'),
  ],
};
```

---

## Build & Development

### Development Commands

```bash
# Install dependencies
yarn install --frozen-lockfile

# Start main app with hot reload
yarn ls:dev

# Start annotation editor standalone
yarn sf:serve

# Watch and rebuild on changes
yarn ls:watch      # Main app
yarn sf:watch      # Editor
yarn dm:watch      # Data manager

# Start Storybook
yarn ui:serve
```

### Testing Commands

```bash
# Unit tests
yarn ls:unit       # Main app
yarn sf:unit       # Editor
yarn dm:unit       # Data manager

# E2E tests
yarn ls:e2e        # Main app
yarn sf:e2e        # Editor
```

### Build Commands

```bash
# Production build
yarn ls:build

# Build output location
# dist/apps/synapse/
```

### NX Commands

```bash
# Run target for specific project
nx run synapse:build
nx run editor:test

# Run affected (only changed)
nx affected:build
nx affected:test

# Dependency graph
nx graph
```

### Build Pipeline

```
Source Code
     │
     ▼
┌─────────────┐
│   Webpack   │
│   Bundler   │
└──────┬──────┘
       │
       ├──► Babel (JSX/TS → ES5)
       ├──► PostCSS (Tailwind → CSS)
       ├──► Asset loading
       └──► Code splitting
           │
           ▼
    ┌─────────────┐
    │ dist/apps/  │
    │  synapse/   │
    └─────────────┘
           │
           ▼
    Django collectstatic
           │
           ▼
    ┌─────────────────────┐
    │ synapse/core/       │
    │ static_build/       │
    │ react-app/          │
    └─────────────────────┘
```

### Environment Variables

```bash
# .env.dev
FRONTEND_HMR=false
FRONTEND_HOSTNAME=http://localhost:8080
API_BASE_URL=/api
SENTRY_DSN=
LAUNCHDARKLY_CLIENT_SDK_KEY=
```

---

## Feature Flags

Feature flags control frontend feature availability:

```typescript
// utils/feature-flags.ts

// LLM-assisted annotations
export const FF_LLM_EPIC = "fflag_feat_all_lsdv_e_294_llm_annotations_180723_long";

// Async taxonomy loading
export const FF_TAXONOMY_ASYNC = "fflag_feat_front_lsdv_5451_async_taxonomy_110823_short";

// Multi-image segmentation
export const FF_LSDV_4583 = "fflag_feat_front_lsdv_4583_multi_image_segmentation_short";

// Usage
import { isFeatureEnabled } from '@synapse/core';

if (isFeatureEnabled(FF_LLM_EPIC)) {
  // Show LLM assistance UI
}
```

---

## Integration with Backend

### API Client

```typescript
// services/api.ts
import axios from 'axios';

const api = axios.create({
  baseURL: '/api',
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor for auth
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token');
  if (token) {
    config.headers.Authorization = `Token ${token}`;
  }
  return config;
});

// Response interceptor for errors
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      // Redirect to login
    }
    return Promise.reject(error);
  }
);

export const projectsApi = {
  list: () => api.get('/projects/'),
  get: (id: number) => api.get(`/projects/${id}/`),
  create: (data: CreateProjectData) => api.post('/projects/', data),
  update: (id: number, data: UpdateProjectData) => api.patch(`/projects/${id}/`, data),
  delete: (id: number) => api.delete(`/projects/${id}/`),
};
```

### Django Template Integration

```html
<!-- synapse/core/templates/base.html -->
<!DOCTYPE html>
<html>
<head>
  <title>Synapse</title>
  {% load static %}
</head>
<body>
  <div id="root"></div>
  
  <!-- React app bundle -->
  <script src="{% static 'react-app/main.js' %}"></script>
</body>
</html>
```

---

## Directory Quick Reference

### What to Edit for Common Tasks

| Task | Location |
|------|----------|
| Add new page | `apps/synapse/src/pages/` |
| Update navigation | `apps/synapse/src/components/Header/` |
| Add reusable component | `libs/ui/src/lib/` |
| Modify annotation tools | `libs/editor/src/tools/` |
| Add annotation tag | `libs/editor/src/tags/` |
| Update API integration | `libs/app-common/src/api/` |
| Add filter option | `libs/datamanager/src/components/Filters/` |
| Modify theme | `tailwind.config.js`, `design-tokens.json` |

---

## Next Steps

- [Platform Overview →](./PLATFORM_OVERVIEW.md)
- [Backend Architecture →](./BACKEND_ARCHITECTURE.md)
- [Business Model →](./BUSINESS_MODEL.md)
- [API Reference →](./api/README.md)
