# DataManager Design System Update

## Overview
The DataManager component library has been updated to match the modern, premium aesthetic of the Synapse landing page. This includes new typography, color schemes, animations, and overall visual consistency.

---

## 🎨 Design Principles

### Typography
- **Display Font**: `Space Grotesk` - Used for headings, tabs, and primary UI elements
- **Body Font**: System font stack (`-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto`)
- **Monospace Font**: `ui-monospace, SF Mono, Cascadia Code, JetBrains Mono, Consolas` - Used for technical elements, tags, badges, and data values

### Color Palette
- **Primary Purple**: `#8b5cf6` - Main accent color
- **Purple Light**: `#a78bfa` - Lighter shade for hover states
- **Purple Lighter**: `#c4b5fd` - Text on dark backgrounds
- **Cream Accent**: `#e8e4d9` - Secondary accent (from landing page)

### Dark Theme Neutrals
- **Black**: `#000000` - Primary background
- **Gray 950**: `#0a0a0a` - Secondary backgrounds
- **Gray 900**: `#111827` - Card backgrounds
- **Gray 800**: `#1f2937` - Borders
- **Gray 700-300**: Various text and UI element colors

---

## 📦 Updated Components

### Tables (`Table.scss`)
- **Rows**: Smooth hover with purple tint and subtle transform
- **Selected rows**: Purple highlight with inset border
- **Typography**: System font for better readability
- **Transitions**: 150ms cubic-bezier for snappy feel

```scss
// Hover effect
&:hover {
  background-color: rgba(139, 92, 246, 0.08);
  transform: translateX(2px);
}
```

### Tabs (`Tabs.scss`)
- **Font**: Space Grotesk for modern look
- **Active tab**: Purple bottom border with gradient background
- **Uppercase labels**: 0.1em letter-spacing
- **Weight**: 600 for active, 500 for inactive

### Pagination (`Pagination.scss`)
- **Font**: Monospace for numbers (technical feel)
- **Buttons**: Scale transform on hover
- **Colors**: Purple accent throughout

### Tags & Badges
- **Tags**: Gradient background, monospace font, uppercase
- **Badges**: Gradient with shadow, hover lift effect
- **Letter spacing**: 0.08em for technical aesthetic

### Filters (`Filters.scss`, `FilterLine.scss`)
- **Container**: Dark gradient with purple border glow
- **Filter items**: Purple tinted backgrounds
- **Hover**: Elevated with shadow
- **Empty state**: Icon + subtle message

### Grid View (`GridView.scss`)
- **Cards**: Purple border on hover with shadow
- **Transform**: -2px translateY on hover (lift effect)
- **Headers**: Space Grotesk font
- **Transitions**: Smooth 200ms cubic-bezier

### Toolbar (`toolbar.scss`)
- **Primary buttons**: Gradient with uppercase text
- **Secondary buttons**: Purple tinted transparent
- **Icon buttons**: Subtle with purple hover
- **Font mixing**: Display font for primary, body for secondary

### Date Picker (`DataManager.scss`)
- **Month/Year**: Space Grotesk, uppercase, 600 weight
- **Day names**: Monospace, uppercase
- **Days**: Monospace with scale hover
- **Today indicator**: Purple dot below date

---

## 🎭 Animation & Transitions

### Timing Functions
- **Fast**: `150ms cubic-bezier(0.4, 0, 0.2, 1)` - Quick interactions
- **Base**: `200ms cubic-bezier(0.4, 0, 0.2, 1)` - Default transitions
- **Slow**: `300ms cubic-bezier(0.4, 0, 0.2, 1)` - Complex animations

### Common Animations
- **Hover lift**: `transform: translateY(-1px)` or `translateY(-2px)`
- **Scale**: `transform: scale(1.05)` for subtle emphasis
- **Glow**: Purple box-shadow on hover
- **Pulse**: Loader animations with opacity changes

---

## 🎯 Design Tokens

All design tokens are defined in `styles/global-theme.scss`:

```scss
// Colors
--dm-primary: #8b5cf6
--dm-primary-light: #a78bfa
--dm-primary-lighter: #c4b5fd

// Typography
--dm-font-display: 'Space Grotesk', ...
--dm-font-body: -apple-system, ...
--dm-font-mono: ui-monospace, ...

// Spacing
--dm-spacing-xs: 4px
--dm-spacing-sm: 8px
--dm-spacing-md: 12px
--dm-spacing-lg: 16px
--dm-spacing-xl: 24px

// Border Radius
--dm-radius-sm: 4px
--dm-radius-md: 6px
--dm-radius-lg: 8px
--dm-radius-xl: 12px

// Shadows
--dm-shadow-purple: 0 4px 12px rgba(139, 92, 246, 0.2)
--dm-shadow-purple-lg: 0 10px 25px rgba(139, 92, 246, 0.3)
```

---

## 🚀 Usage

### Importing Global Theme
The global theme is imported in `App.scss`:
```scss
@import '../../styles/global-theme.scss';
```

### Using Design Tokens
```scss
// In your SCSS files
.my-component {
  background: var(--dm-gray-950);
  border: 1px solid var(--dm-gray-800);
  border-radius: var(--dm-radius-lg);
  font-family: var(--dm-font-display);
  transition: all var(--dm-transition-base);
  
  &:hover {
    box-shadow: var(--dm-shadow-purple);
  }
}
```

### Typography Classes
```scss
// Headings - use Space Grotesk
.heading {
  font-family: var(--dm-font-display);
  font-weight: 600;
  letter-spacing: -0.02em;
}

// Technical/Data - use Monospace
.technical-value {
  font-family: var(--dm-font-mono);
  letter-spacing: 0.05em;
}
```

---

## ✨ Key Features

### 1. Consistent Purple Accent
All interactive elements use the purple color scheme for consistency with the landing page.

### 2. Smooth Animations
- Cubic-bezier easing for natural feel
- Transform-based animations for performance
- Purple glows on hover for premium feel

### 3. Typography Hierarchy
- **Space Grotesk** for important UI elements (tabs, headers)
- **Monospace** for data and technical values
- **System fonts** for body text and general UI

### 4. Depth & Elevation
- Box shadows on hover
- Transform lifts for interactive elements
- Gradient backgrounds for visual interest

### 5. Dark Theme First
- Pure black backgrounds (#000000)
- Carefully chosen gray scale
- High contrast for readability

---

## 🎨 Visual Examples

### Button Hierarchy
```scss
// Primary action - gradient background
.toolbar-button-primary {
  background: linear-gradient(135deg, rgba(139, 92, 246, 0.15), rgba(168, 85, 247, 0.1));
  font-family: var(--dm-font-display);
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

// Secondary action - subtle tint
.toolbar-button {
  background: rgba(139, 92, 246, 0.08);
  border: 1px solid rgba(139, 92, 246, 0.3);
}

// Icon only - minimal
.toolbar-button-icon {
  background: rgba(55, 65, 81, 0.5);
  padding: 8px;
  min-width: 36px;
}
```

### Card Styling
```scss
.grid-view__cell-content {
  background: #0a0a0a;
  border: 1px solid #1f2937;
  border-radius: 8px;
  transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
  
  &:hover {
    border-color: rgba(139, 92, 246, 0.6);
    box-shadow: 0 0 0 4px rgba(139, 92, 246, 0.15),
                0 8px 24px rgba(139, 92, 246, 0.2);
    transform: translateY(-2px);
  }
}
```

---

## 📋 Migration Checklist

When adding new components, ensure:

- ✅ Import global-theme.scss if needed
- ✅ Use Space Grotesk for headings/tabs
- ✅ Use monospace for technical values
- ✅ Apply purple accent color (#8b5cf6)
- ✅ Use cubic-bezier transitions
- ✅ Add hover states with transform/shadow
- ✅ Maintain dark theme consistency
- ✅ Use design token CSS variables

---

## 🔧 Performance Considerations

### CSS Performance
- Use `transform` instead of `top/left` for animations
- Apply `will-change: transform` sparingly
- Use `contain: layout style paint` for complex components

### Animation Optimization
- Use `requestAnimationFrame` for scroll-based animations
- Throttle resize handlers
- Lazy load images in grid view

### Accessibility
```scss
// Reduced motion support
@media (prefers-reduced-motion: reduce) {
  * {
    animation-duration: 0.01ms !important;
    transition-duration: 0.01ms !important;
  }
}

// Focus states
*:focus-visible {
  outline: 2px solid var(--dm-primary);
  outline-offset: 2px;
}
```

---

## 🎯 Future Enhancements

- [ ] Add dark/light mode toggle
- [ ] Create theme variants (blue, green, etc.)
- [ ] Add more animation presets
- [ ] Create component showcase/storybook
- [ ] Document accessibility patterns
- [ ] Add RTL support

---

## 📚 Resources

- **Landing Page**: See `/apps/synapse/src/pages/Landing/` for reference
- **Design Tokens**: `/libs/ui/src/tokens/tokens.scss`
- **UI Library**: `/libs/ui/src/lib/` for reusable components
- **Figma**: Design tokens exported from Figma design system

---

**Last Updated**: January 11, 2026
**Version**: 2.0.0
**Maintained by**: Synapse Design Team
