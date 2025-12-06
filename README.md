# Chattingus Backend

A Django REST Framework backend for a social media platform with real-time messaging capabilities.

## Features

- **User Management**: Custom user model with profiles, follow/unfollow functionality
- **Posts**: Create, like, and comment on posts
- **Stories**: 24-hour temporary content with view tracking
- **Reels**: Short-form video content
- **Real-time Messaging**: WebSocket-based chat using Django Channels
- **Notifications**: Real-time notifications for user interactions
- **JWT Authentication**: Secure token-based authentication
- **REST API**: Comprehensive RESTful API endpoints

## Technology Stack

- **Django 5.0+**: Web framework
- **Django REST Framework**: API development
- **Django Channels**: WebSocket support for real-time features
- **PostgreSQL**: Database
- **Redis**: Channel layer backend
- **JWT**: Authentication tokens
- **Pillow**: Image processing

## Prerequisites

- Python 3.10+
- PostgreSQL
- Redis Server

## Installation

### 1. Clone the repository

```bash
git clone <repository-url>
cd chattingus_backend
```

### 2. Create a virtual environment

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Set up environment variables

Create a `.env` file in the project root (use `.env.example` as template):

```bash
cp .env.example .env
```

Edit `.env` and configure your settings:

```env
SECRET_KEY=your-secret-key-here
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# PostgreSQL Database
DB_NAME=chattingus_db
DB_USER=postgres
DB_PASSWORD=your-password
DB_HOST=localhost
DB_PORT=5432

# Redis
REDIS_HOST=localhost
REDIS_PORT=6379

# CORS
CORS_ALLOWED_ORIGINS=http://localhost:3000,http://localhost:8080
```

### 5. Create PostgreSQL database

```bash
psql -U postgres
CREATE DATABASE chattingus_db;
\q
```

### 6. Run migrations

```bash
python manage.py makemigrations
python manage.py migrate
```

### 7. Create a superuser

```bash
python manage.py createsuperuser
```

### 8. Create media directories

```bash
mkdir media
```

## Running the Development Server

### Start Redis (required for Channels)

```bash
redis-server
```

### Start Django development server

```bash
python manage.py runserver
```

The API will be available at `http://localhost:8000/`

## API Endpoints

### Authentication

- `POST /api/token/` - Obtain JWT token pair
- `POST /api/token/refresh/` - Refresh access token
- `POST /api/token/verify/` - Verify token

### Users

- `GET /api/users/` - List users
- `POST /api/users/` - Create user
- `GET /api/users/{id}/` - Get user details
- `POST /api/users/{id}/follow/` - Follow user
- `POST /api/users/{id}/unfollow/` - Unfollow user

### Posts

- `GET /api/posts/` - List posts
- `POST /api/posts/` - Create post
- `GET /api/posts/{id}/` - Get post details
- `POST /api/posts/{id}/like/` - Like post
- `POST /api/posts/{id}/unlike/` - Unlike post

### Stories

- `GET /api/stories/` - List active stories
- `POST /api/stories/` - Create story
- `POST /api/stories/{id}/view/` - Mark story as viewed

### Reels

- `GET /api/reels/` - List reels
- `POST /api/reels/` - Create reel
- `POST /api/reels/{id}/like/` - Like reel
- `POST /api/reels/{id}/view/` - Increment view count

### Messages

- `GET /api/messages/` - List conversations
- `POST /api/messages/` - Send message
- `POST /api/messages/{id}/mark_read/` - Mark conversation as read

### Notifications

- `GET /api/notifications/` - List notifications
- `POST /api/notifications/mark_all_read/` - Mark all as read
- `POST /api/notifications/{id}/mark_read/` - Mark notification as read

## WebSocket Endpoints

### Chat

```
ws://localhost:8000/ws/chat/<room_id>/
```

### Notifications

```
ws://localhost:8000/ws/notifications/
```

## Project Structure

```
chattingus_backend/
├── chattingus_backend/      # Main project settings
│   ├── settings.py          # Django settings
│   ├── urls.py              # Main URL configuration
│   ├── asgi.py              # ASGI configuration for Channels
│   └── routing.py           # WebSocket routing
├── users/                   # User management app
├── posts/                   # Posts app
├── stories/                 # Stories app
├── reels/                   # Reels app
├── messages/                # Real-time messaging app
├── notifications/           # Notifications app
├── media/                   # User-uploaded media files
├── requirements.txt         # Python dependencies
├── .env.example             # Environment variables template
└── manage.py                # Django management script
```

## Admin Panel

Access the Django admin panel at `http://localhost:8000/admin/` using your superuser credentials.

## Development

### Running Tests

```bash
python manage.py test
```

### Creating Migrations

```bash
python manage.py makemigrations
python manage.py migrate
```

### Collecting Static Files

```bash
python manage.py collectstatic
```

## Production Deployment

1. Set `DEBUG=False` in `.env`
2. Configure `ALLOWED_HOSTS` with your domain
3. Set up a production-grade database
4. Configure a production ASGI server (e.g., Daphne with Nginx)
5. Set up Redis for production
6. Configure static file serving
7. Use environment-specific settings

## License

[Your License Here]

## Contributing

[Your Contributing Guidelines Here]
