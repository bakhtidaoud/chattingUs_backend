# ChattingUs Backend 🚀

![Banner](media/covers/profile_cover.png)

A high-performance, feature-rich social and marketplace backend built with **Django**, **PostgreSQL**, **Redis**, and **Celery**.

---

## ✨ Key Features

### 🛒 Marketplace & Finance
- **Stripe Integration**: Onboarding sellers via Stripe Connect, handling payouts, and subscription plans (Pro/Business).
- **Escrow System**: Automated funds release 7 days after shipping unless a dispute is opened.
- **Virtual Currency**: A custom wallet system for boosts and top-ups, integrated with Stripe.
- **Referral Program**: Viral growth engine providing rewards in virtual currency for successful referrals.

### 📱 Social Engagement
- **Dynamic Feeds**: Smart feed generation with personalized post discovery.
- **Rich Interaction**: Emoji reactions, nested comments, and hashtag/mention parsing.
- **Ephemeral Stories**: Stories that expire after 24 hours with view/reaction tracking.
- **Real-time Comms**: WebSocket-powered chat with delivery receipts, typing indicators, and media attachments.

### ⚡ Infrastructure & Performance
- **Advanced Search**: PostgreSQL Full-Text Search with GIN indexes and search vectors for Listings and Posts.
- **Smart Caching**: Multi-layered Redis cache for user profiles, category trees, and anonymous feeds.
- **Background Jobs**: Celery tasks for thumbnail generation, daily analytics (LogEntry aggregates), and email digests.
- **Reliable Backups**: Built-in S3 backup/restore for database and media assets.
- **Feature Rollouts**: Percentage-based feature flags for phased deployments.

---

## 🛠️ Getting Started

### 1. Requirements
Ensure you have Python 3.10+ installed.

### 2. Installation
```powershell
pip install -r requirements.txt
```

### 3. Database Setup (PostgreSQL)
Update `DATABASES` in `settings.py` with your credentials and run:
```powershell
python manage.py migrate
```

### 4. Background Services
Start your Redis server, then run:
```powershell
# Celery Worker
celery -A chattingUS_backend worker --loglevel=info

# Celery Beat (Scheduled tasks)
celery -A chattingUS_backend beat --loglevel=info
```

### 5. Populate Demo Data
We have already populated the database with AI-generated posts and high-quality product images! Check `users_list.txt` for demo credentials.
```powershell
python manage.py populate_dummy_data
```

---

## 🛡️ Admin Dashboard
The admin dashboard is enhanced with:
- **Admin Logs**: Full audit trail of all staff actions.
- **Growth Charts**: Daily aggregates of new users, orders, and revenue.
- **Feature Flags**: Instant toggle for new features.

---

## 📄 Documentation & API
The API is built using **Django Rest Framework**.
Check the `/api/` endpoints for full CRUD capabilities.

*Designed with 💜 by BAKHTI Daoud.*
