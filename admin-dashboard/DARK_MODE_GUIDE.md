# Dark Mode Integration Guide

## Files Created

1. **`css/dark-mode.css`** - Complete dark mode theme with CSS variables
2. **`js/theme.js`** - Theme manager with persistence and auto-detection

## Quick Integration (3 Steps)

### Step 1: Add CSS to your HTML

Add this line in the `<head>` section of `dashboard.html` and `login.html`:

```html
<link rel="stylesheet" href="css/dark-mode.css">
```

### Step 2: Add JavaScript

Add this line before the closing `</body>` tag:

```html
<script src="js/theme.js"></script>
```

### Step 3: Add Toggle Button

Add this HTML to your sidebar (in `dashboard.html`):

```html
<!-- Dark Mode Toggle -->
<div class="sidebar-footer" style="padding: 1rem; border-top: 1px solid var(--border-color);">
    <div class="theme-toggle-container">
        <label style="display: flex; align-items: center; gap: 0.5rem; color: var(--text-secondary); font-size: 0.875rem;">
            <i class="fas fa-moon"></i>
            <span>Dark Mode</span>
        </label>
        <div id="themeToggle" class="theme-toggle">
            <div class="theme-toggle-slider">
                <i class="fas fa-sun"></i>
            </div>
        </div>
    </div>
</div>
```

## Features

### ✅ Automatic Features

- **localStorage Persistence** - Theme choice is saved
- **System Preference Detection** - Auto-detects OS dark mode
- **Smooth Transitions** - 0.3s transitions on all elements
- **Keyboard Shortcut** - `Ctrl/Cmd + Shift + D` to toggle
- **Chart.js Integration** - Automatically updates chart colors

### ✅ Color Schemes

**Light Mode:**
- Background: `#f5f7fa`
- Cards: `#ffffff`
- Text: `#2d3748`
- Borders: `#e2e8f0`
- Primary: `#667eea`

**Dark Mode:**
- Background: `#1a202c`
- Cards: `#2d3748`
- Text: `#e2e8f0`
- Borders: `#4a5568`
- Primary: `#667eea`

### ✅ Styled Components

All components are styled for both modes:
- ✅ Sidebar & Navbar
- ✅ Cards & Tables
- ✅ Modals & Forms
- ✅ Buttons & Inputs
- ✅ Charts & Graphs
- ✅ Tooltips & Dropdowns
- ✅ Badges & Alerts
- ✅ Scrollbars

## Usage in JavaScript

```javascript
// Check current theme
const isDark = ThemeManager.isDarkMode();

// Get theme name
const theme = ThemeManager.getTheme(); // 'light' or 'dark'

// Manually set theme
ThemeManager.setTheme('dark');

// Toggle theme
ThemeManager.toggleTheme();

// Listen for theme changes
window.addEventListener('themeChanged', (e) => {
    console.log('Theme changed to:', e.detail.theme);
});
```

## CSS Variables Usage

Use CSS variables in your custom styles:

```css
.my-custom-element {
    background: var(--bg-card);
    color: var(--text-primary);
    border: 1px solid var(--border-color);
}
```

## Available CSS Variables

### Backgrounds
- `--bg-primary` - Main background
- `--bg-secondary` - Secondary background
- `--bg-tertiary` - Tertiary background
- `--bg-card` - Card background

### Text
- `--text-primary` - Primary text
- `--text-secondary` - Secondary text
- `--text-tertiary` - Tertiary text
- `--text-white` - White text

### Colors
- `--primary-purple` - Primary brand color
- `--secondary-purple` - Secondary brand color
- `--success-color` - Success green
- `--warning-color` - Warning orange
- `--error-color` - Error red
- `--info-color` - Info blue

### Borders & Shadows
- `--border-color` - Border color
- `--shadow-sm` - Small shadow
- `--shadow-md` - Medium shadow
- `--shadow-lg` - Large shadow
- `--shadow-xl` - Extra large shadow

### Glassmorphism
- `--glass-bg` - Glass background
- `--glass-border` - Glass border
- `--glass-shadow` - Glass shadow

## Advanced Features

### System Preference Auto-Detection

The theme automatically detects and respects the user's OS dark mode preference on first visit.

### Chart.js Integration

Charts automatically update their colors when the theme changes:

```javascript
// Charts will automatically use:
// - var(--chart-primary)
// - var(--chart-secondary)
// - var(--chart-grid)
// - var(--chart-text)
```

### Image Adjustments

Images are automatically adjusted in dark mode:
- Slight opacity reduction (90%)
- Brightness filter on logos

### Accessibility

- High contrast mode support
- Reduced motion support
- Keyboard navigation
- Focus indicators

## Testing

1. **Toggle Button**: Click the toggle in the sidebar
2. **Keyboard**: Press `Ctrl/Cmd + Shift + D`
3. **Persistence**: Refresh page - theme should persist
4. **System Preference**: Change OS dark mode - should auto-detect

## Customization

### Change Colors

Edit the CSS variables in `dark-mode.css`:

```css
[data-theme="dark"] {
    --bg-primary: #your-color;
    --text-primary: #your-color;
    /* etc... */
}
```

### Add Custom Transitions

```css
.my-element {
    transition: background-color 0.3s ease,
                color 0.3s ease;
}
```

## Troubleshooting

### Theme not persisting?
- Check localStorage is enabled
- Check browser console for errors

### Colors not changing?
- Ensure `dark-mode.css` is loaded
- Check that elements use CSS variables
- Verify `data-theme` attribute is set on `<html>`

### Charts not updating?
- Ensure Chart.js is loaded before `theme.js`
- Check that charts are using CSS variables

## Browser Support

- ✅ Chrome/Edge (latest)
- ✅ Firefox (latest)
- ✅ Safari (latest)
- ✅ Opera (latest)

## Performance

- Minimal performance impact
- Uses CSS variables (hardware accelerated)
- Smooth 0.3s transitions
- No layout shifts
