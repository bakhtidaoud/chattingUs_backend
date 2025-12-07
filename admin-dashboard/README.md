# ChattingUs Admin Dashboard

A modern, beautiful admin dashboard for the ChattingUs social media platform built with vanilla HTML, CSS, and JavaScript.

## 🎨 Features

- **Premium UI Design**: Glassmorphism effects with vibrant gradient color schemes
- **Dark Mode Support**: Toggle between light and dark themes
- **Fully Responsive**: Works seamlessly on desktop, tablet, and mobile devices
- **JWT Authentication**: Secure token-based authentication with auto-refresh
- **Real-time Updates**: Live data synchronization with Django backend
- **Smooth Animations**: Engaging micro-interactions and transitions
- **Chart.js Integration**: Beautiful data visualizations and analytics

## 🚀 Tech Stack

- **Frontend**: HTML5, CSS3, Vanilla JavaScript
- **Charts**: Chart.js
- **Icons**: Font Awesome 6
- **Authentication**: JWT tokens (localStorage)
- **Backend**: Django REST API

## 📁 Project Structure

```
admin-dashboard/
├── index.html              # Login page
├── dashboard.html          # Main dashboard (coming soon)
├── css/
│   ├── style.css          # Main styles & design tokens
│   ├── dark-mode.css      # Dark theme styles
│   └── responsive.css     # Media queries
├── js/
│   ├── auth.js            # Authentication logic
│   ├── api.js             # API service layer
│   ├── main.js            # Dashboard logic (coming soon)
│   └── utils.js           # Helper functions
└── assets/
    └── images/            # Image assets
```

## 🛠️ Setup Instructions

### 1. Configure Backend URL

Edit `js/api.js` and update the `baseURL` to match your Django backend:

```javascript
const API = {
    baseURL: 'http://localhost:8000/api',  // Update this
    // ...
};
```

### 2. Django Backend Requirements

Your Django backend should have the following endpoints:

#### Authentication
- `POST /api/auth/login/` - Login with email/password
  - Request: `{ "email": "string", "password": "string" }`
  - Response: `{ "access": "token", "refresh": "token", "user": {...} }`
- `POST /api/auth/token/refresh/` - Refresh access token
- `POST /api/auth/logout/` - Logout user

#### Users
- `GET /api/users/` - List all users
- `GET /api/users/{id}/` - Get user details
- `POST /api/users/` - Create user
- `PATCH /api/users/{id}/` - Update user
- `DELETE /api/users/{id}/` - Delete user

#### Posts
- `GET /api/posts/` - List all posts
- `GET /api/posts/{id}/` - Get post details
- `POST /api/posts/` - Create post
- `PATCH /api/posts/{id}/` - Update post
- `DELETE /api/posts/{id}/` - Delete post

#### Comments
- `GET /api/comments/` - List all comments
- `DELETE /api/comments/{id}/` - Delete comment

#### Stories
- `GET /api/stories/` - List all stories
- `DELETE /api/stories/{id}/` - Delete story

#### Analytics
- `GET /api/analytics/dashboard/` - Dashboard statistics
- `GET /api/analytics/users/` - User analytics
- `GET /api/analytics/posts/` - Post analytics

### 3. CORS Configuration

Make sure your Django backend allows CORS requests from your frontend:

```python
# settings.py
CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    # Add your frontend URL
]
```

### 4. Run the Dashboard

Simply open `index.html` in a web browser, or use a local server:

```bash
# Using Python
python -m http.server 3000

# Using Node.js
npx http-server -p 3000

# Using PHP
php -S localhost:3000
```

Then navigate to `http://localhost:3000`

## 🎯 Usage

### Login

1. Open the dashboard in your browser
2. Enter your admin credentials (email and password)
3. Click "Sign In"
4. You'll be redirected to the dashboard upon successful authentication

### Theme Toggle

Click the moon/sun icon in the bottom-right corner to toggle between light and dark modes.

## 🔐 Security Features

- JWT token-based authentication
- Automatic token refresh (every 4 minutes)
- Secure token storage in localStorage
- XSS protection with HTML sanitization
- CSRF protection via Django backend

## 🎨 Design Features

### Glassmorphism
The dashboard uses modern glassmorphism effects with:
- Semi-transparent backgrounds
- Backdrop blur filters
- Subtle borders and shadows

### Color Palette
- Primary Purple: `#8b5cf6`
- Primary Blue: `#3b82f6`
- Primary Pink: `#ec4899`
- Primary Cyan: `#06b6d4`

### Animations
- Floating gradient orbs
- Smooth hover effects
- Loading spinners
- Fade-in transitions
- Pulse effects

## 📱 Responsive Breakpoints

- **Desktop**: 1440px and above
- **Laptop**: 1024px - 1439px
- **Tablet**: 768px - 1023px
- **Mobile**: 480px - 767px
- **Small Mobile**: Below 480px

## 🔧 Customization

### Update API Base URL

Edit `js/api.js`:
```javascript
baseURL: 'https://your-api-domain.com/api'
```

### Change Color Scheme

Edit CSS variables in `css/style.css`:
```css
:root {
    --primary-purple: #8b5cf6;
    --primary-blue: #3b82f6;
    /* Add your colors */
}
```

### Add New API Endpoints

Add methods to `js/api.js`:
```javascript
async getCustomData() {
    return this.get('/custom-endpoint/');
}
```

## 🐛 Troubleshooting

### Login Not Working
- Check browser console for errors
- Verify backend URL is correct
- Ensure Django backend is running
- Check CORS configuration

### Token Expired
- Tokens automatically refresh every 4 minutes
- If refresh fails, you'll be redirected to login

### Styling Issues
- Clear browser cache
- Check if all CSS files are loading
- Verify file paths are correct

## 📄 License

This project is part of the ChattingUs platform.

## 🤝 Contributing

This is an internal admin dashboard. For issues or improvements, contact the development team.

## 📞 Support

For technical support, please contact the ChattingUs development team.
