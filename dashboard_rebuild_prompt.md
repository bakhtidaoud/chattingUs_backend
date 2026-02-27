# Admin Dashboard Premium Rebuild Instructions

To rebuild the admin dashboard with a premium, state-of-the-art design, follow these specifications:

## 🎨 Visual Identity
*   **Theme**: Deep Midnight/Obsidian with Electric Indigo accents (`#6366f1`).
*   **Aesthetic**: Glassmorphism (blur: 20px, background: `rgba(255,255,255,0.03)`, border: `1px solid rgba(255,255,255,0.1)`).
*   **Typography**: Use **Outfit** font from Google Fonts. Headers should have `letter-spacing: -0.04em`.
*   **Colors**: 
    *   Primary: Indigo `#6366f1`
    *   Success: Emerald `#10b981`
    *   Warning: Amber `#f59e0b`
    *   Error: Rose `#f43f5e`
    *   Background: `#0f172a` (Slate-950)

## 🏗️ Layout & Structure
*   **Main Wrapper**: Use a wide, responsive container with maximum width of `1600px`.
*   **Stat Cards**:
    *   Display key metrics (Revenue, Users, Listings) at the top.
    *   Include meaningful icons (Lucide icons via CDN).
    *   Add a subtle gradient background that glows on hover.
*   **Chart Grid**:
    *   Large area for Revenue Growth (Line chart with gradient fill).
    *   Sidebar area for Category Distribution (Doughnut with inner labels).
*   **Live Activity Feed**:
    *   Add a section for "Recent System Events" or "Live Audit Stream".
    *   Use small avatars/icons for event types.

## ✨ Interactions & Micro-animations
*   **Entrance**: All cards should fade and slide up on page load using CSS animations.
*   **Charts**: Use `Chart.js` with smooth tension (`0.4`) and customized tooltips that match the glassmorphism theme.
*   **Live Updates**: Use the existing WebSocket (`/ws/admin/analytics/`) to update individual chart data and stat values *without* a full page reload.

## 🛠️ Implementation Steps
1.  **Update `admin/index.html`**:
    *   Replace the flat `dashboard-grid` with a more hierarchical layout.
    *   Implement Lucide icons via `<script src="https://unpkg.com/lucide@latest"></script>`.
    *   Refactor the CSS to use variables from our new `base.html`.
2.  **Enhance `Chart.js` Config**:
    *   Define global defaults for tooltips (glass background, white text).
    *   Use `CanvasGradient` for line charts.
3.  **Refine JavaScript**:
    *   Add a `updateDashboard(data)` function that targets specific DOM IDs for live updates.
