# Synapse Frontend Structure Guide

This document explains the organization and purpose of files in the `/web` directory, which contains the entire frontend codebase for Synapse.

## 📁 Directory Overview

Synapse uses **Nx** (a monorepo tool) to manage multiple applications and shared libraries. The frontend is organized into:

- **Apps**: Standalone applications (main Synapse UI)
- **Libs**: Reusable shared libraries (editor, datamanager, UI components)

---

## 🗂️ Root Configuration Files

### Build & Package Management

| File                   | Purpose                                                 | When to Edit                                |
| ---------------------- | ------------------------------------------------------- | ------------------------------------------- |
| **package.json**       | Defines all npm dependencies and scripts                | Adding new packages or scripts              |
| **yarn.lock**          | Locked versions of dependencies                         | Auto-generated, don't edit manually         |
| **nx.json**            | Nx monorepo configuration (build caching, task runners) | Configuring build optimization              |
| **tsconfig.base.json** | Base TypeScript configuration for all projects          | Setting up path aliases or compiler options |
| **tsconfig.json**      | Root TypeScript configuration                           | Rarely - extends base config                |

### Bundling & Building

| File                   | Purpose                                      | When to Edit                                |
| ---------------------- | -------------------------------------------- | ------------------------------------------- |
| **webpack.config.js**  | Webpack configuration for building apps      | Customizing build process, loaders, plugins |
| **babel.config.json**  | Babel transpiler configuration (ES6+ → ES5)  | Adding new JS transformations               |
| **postcss.config.js**  | PostCSS configuration for CSS processing     | Adding CSS transformations                  |
| **tailwind.config.js** | Tailwind CSS utility framework configuration | Customizing design system, colors, spacing  |

### Code Quality & Testing

| File                  | Purpose                                     | When to Edit                          |
| --------------------- | ------------------------------------------- | ------------------------------------- |
| **jest.config.ts**    | Jest testing framework configuration        | Configuring test setup, coverage      |
| **jest.preset.js**    | Shared Jest presets for all projects        | Setting up common test configurations |
| **biome.json**        | Biome linter/formatter configuration        | Code style rules, linting preferences |
| **.stylelintrc.json** | CSS/SCSS linting rules                      | Enforcing CSS code quality            |
| **.stylelintignore**  | Files to exclude from CSS linting           | Excluding third-party CSS             |
| **.editorconfig**     | Editor settings (indentation, line endings) | Team-wide editor consistency          |

### UI Design System

| File                   | Purpose                                            | When to Edit                     |
| ---------------------- | -------------------------------------------------- | -------------------------------- |
| **components.json**    | Shadcn UI components configuration                 | Adding/configuring UI components |
| **design-tokens.json** | Design system tokens (colors, typography, spacing) | Updating brand/theme design      |

### Other

| File           | Purpose                            | When to Edit                |
| -------------- | ---------------------------------- | --------------------------- |
| **release.js** | Release automation script          | Modifying release workflow  |
| **README.md**  | Frontend development documentation | Updating setup instructions |

---

## 📦 Main Applications (`apps/`)

### `apps/Synapse/` ⭐

**The main Synapse application** - This is what users interact with.

**What it contains:**

- Main React application code
- Integration of all libraries (editor, datamanager, UI components)
- Django template integration
- Project management, user settings, organization features

**Key files you'll edit:**

- `src/` - Main application source code
- `webpack.config.js` - App-specific webpack config
- `project.json` - Nx project configuration

**Common tasks:**

```bash
# Development with Hot Module Reload
yarn ls:dev

# Build for production
yarn ls:build

# Watch mode (auto-rebuild on changes)
yarn ls:watch
```

### `apps/Synapse-e2e/`

End-to-end tests for the main Synapse app (using Playwright/Cypress).

### `apps/playground/`

Development playground for testing components in isolation.

---

## 📚 Shared Libraries (`libs/`)

### `libs/editor/` 🎨

**Synapse Frontend (SF)** - The annotation interface library.

**What it does:**

- Handles all annotation tools (bounding boxes, polygons, text, audio, video)
- Manages annotation state with MobX State Tree
- Provides the labeling UI shown to annotators
- Standalone library that can be used outside Synapse

**When to modify:**

- Adding new annotation tools
- Changing annotation behavior
- Customizing labeling interface

**Common tasks:**

```bash
# Development mode
yarn sf:serve

# Watch mode
yarn sf:watch

# Run tests
yarn sf:unit
yarn sf:e2e
```

### `libs/datamanager/` 📊

**Data Manager** - Data exploration and management interface.

**What it does:**

- Browse and filter tasks/annotations
- Bulk operations on data
- Data statistics and insights
- Task assignment and workflow management

**When to modify:**

- Customizing data views
- Adding filters or bulk actions
- Changing task list behavior

**Common tasks:**

```bash
# Watch mode
yarn dm:watch

# Run tests
yarn dm:unit
```

### `libs/ui/` 🎨

**Shared UI Components** - Reusable React components.

**What it contains:**

- Buttons, inputs, modals, dropdowns
- Common UI patterns used across apps
- Design system implementation

**When to modify:**

- Creating new reusable components
- Updating component library

### `libs/core/` 🔧

**Core Utilities** - Shared utility functions and helpers.

**What it contains:**

- Common functions used across projects
- Type definitions
- Constants

### `libs/app-common/` 🛠️

**Common Application Logic** - Shared business logic.

**What it contains:**

- API clients
- Authentication logic
- Shared state management
- Hooks and utilities used by apps

### `libs/storybook/` 📖

**Storybook Configuration** - Component documentation and testing.

**What it does:**

- Visual component development
- Component documentation
- Design system showcase

**Common tasks:**

```bash
# Start Storybook
yarn ui:serve
```

### `libs/frontend-test/` 🧪

**Testing Utilities** - Shared test helpers and fixtures.

---

## 🚀 Common Development Commands

### Development Workflow

```bash
# Install dependencies (run first!)
yarn install --frozen-lockfile

# Start main app with hot reload (RECOMMENDED for development)
yarn ls:dev

# Start annotation editor standalone
yarn sf:serve

# Watch and rebuild on changes
yarn ls:watch      # Main app
yarn sf:watch     # Editor
yarn dm:watch      # Data manager
```

### Testing

```bash
# Unit tests
yarn ls:unit       # Main app
yarn sf:unit      # Editor
yarn dm:unit       # Data manager

# E2E tests
yarn ls:e2e        # Main app
yarn sf:e2e       # Editor
```

### Building

```bash
# Production build (this is what Django serves)
yarn ls:build

# The built files go to: dist/apps/Synapse/
```

### Code Quality

```bash
# Lint and format code
yarn lint

# Lint SCSS files
yarn lint-scss
```

---

## 🔄 How Frontend Connects to Backend

1. **Built Assets**: When you run `yarn ls:build`, static files are created in `dist/apps/Synapse/`
2. **Django Integration**: Django's `collectstatic` copies these to `synapse/core/static_build/react-app/`
3. **Templates**: Django serves the main HTML template with React app loaded
4. **API Calls**: React app makes REST API calls to Django backend at `/api/`

---

## 🎯 Where to Start Development

### For UI Changes:

1. **Main App UI**: `apps/Synapse/src/`
2. **Reusable Components**: `libs/ui/src/`
3. **Styling**: Look for `.scss` files, or `tailwind.config.js` for theme

### For Annotation Features:

1. **Annotation Tools**: `libs/editor/src/`
2. **Tool Configuration**: `libs/editor/src/tools/`

### For Data Management:

1. **Task Lists/Filters**: `libs/datamanager/src/`
2. **Bulk Actions**: `libs/datamanager/src/components/`

### For API Integration:

1. **API Clients**: `libs/app-common/src/api/`
2. **State Management**: `libs/app-common/src/stores/`

---

## 💡 Development Tips

### Hot Module Reload (HMR)

To enable live code updates without page refresh:

1. Make sure your `.env.dev` has:

   ```
   FRONTEND_HMR=false
   FRONTEND_HOSTNAME=http://localhost:8080
   ```

   (We disabled HMR because built files work better for development)

2. For live development, run:
   ```bash
   yarn ls:watch
   ```
   This rebuilds automatically when you save files.

### Understanding Nx

- Nx manages multiple projects in one repository
- Each app/lib has a `project.json` with build configurations
- `nx.json` defines how projects depend on each other
- Nx caches builds for speed

### TypeScript Paths

- `tsconfig.base.json` defines path aliases like `@/libs/ui` → `libs/ui/src`
- This allows clean imports: `import { Button } from '@/libs/ui'`

### Component Development

- Use Storybook (`yarn ui:serve`) to develop components in isolation
- Faster than running the full app for UI work

---

## 🐛 Common Issues

**Issue**: Changes not appearing after build

- **Solution**: Run Django's `collectstatic` again, or restart the Django server

**Issue**: TypeScript errors about missing types

- **Solution**: Run `yarn install` and restart your editor

**Issue**: Build fails with webpack errors

- **Solution**: Clear cache: `rm -rf node_modules/.cache` then rebuild

**Issue**: Styles not applying

- **Solution**: Check if PostCSS/Tailwind configs are correct, clear build cache

---

## 📖 Additional Resources

- **Nx Documentation**: https://nx.dev
- **React Documentation**: https://react.dev
- **Synapse Docs**: https://synapse.io/guide

---

## 🎓 Quick Start for New Developers

1. **Install dependencies**: `yarn install --frozen-lockfile`
2. **Start development**: `yarn ls:watch` (in one terminal)
3. **Run Django**: `.\setup_dev_environment.bat` (from root directory)
4. **Access**: http://localhost:8080
5. **Make changes**: Edit files in `apps/Synapse/src/` or `libs/`
6. **See changes**: Files rebuild automatically, refresh browser

**That's it!** You're ready to develop. Start exploring the code in `apps/` and `libs/` directories.
