-- PostgreSQL Database Setup Script for Chattingus Backend
-- Run this script using pgAdmin or psql command line

-- Create the database
CREATE DATABASE chattingus_db;

-- Connect to the database
\c chattingus_db;

-- Create indexes for better performance (run after migrations)
-- These will be created after running Django migrations

-- User model indexes
CREATE INDEX idx_users_username ON users_user(username);
CREATE INDEX idx_users_email ON users_user(email);
CREATE INDEX idx_users_created_at ON users_user(created_at);

-- Post model indexes
CREATE INDEX idx_posts_user ON posts_post(user_id);
CREATE INDEX idx_posts_created_at ON posts_post(created_at);

-- Story model indexes
CREATE INDEX idx_stories_user ON stories_story(user_id);
CREATE INDEX idx_stories_expires_at ON stories_story(expires_at);

-- Reel model indexes
CREATE INDEX idx_reels_user ON reels_reel(user_id);
CREATE INDEX idx_reels_created_at ON reels_reel(created_at);

-- Chat model indexes
CREATE INDEX idx_chat_conversation_updated ON chat_conversation(updated_at);
CREATE INDEX idx_chat_message_conversation ON chat_message(conversation_id);
CREATE INDEX idx_chat_message_sender ON chat_message(sender_id);
CREATE INDEX idx_chat_message_created ON chat_message(created_at);

-- Notification model indexes
CREATE INDEX idx_notifications_recipient ON notifications_notification(recipient_id);
CREATE INDEX idx_notifications_is_read ON notifications_notification(is_read);
CREATE INDEX idx_notifications_created ON notifications_notification(created_at);
