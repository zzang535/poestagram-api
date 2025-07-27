# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Development Commands

### Virtual Environment
```bash
python -m venv venv
source venv/bin/activate  # macOS/Linux
pip install -r requirements.txt
```

### Running the Application
```bash
uvicorn main:app --reload
```

### Database Migrations
Use virtual environment for all migration operations:
```bash
# Generate new migration
alembic revision --autogenerate -m "description"

# Apply migrations
alembic upgrade head

# Custom CLI supports database URL parameter
alembic -x db_url="mysql+pymysql://user:pass@host/db" upgrade head
```

### API Documentation
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc
- Health check: http://localhost:8000/health

## Architecture Overview

### Core Structure
- **FastAPI application** with modular router structure
- **SQLAlchemy ORM** with Alembic for database migrations
- **MySQL database** with PyMySQL connector
- **AWS S3** integration for file storage with CloudFront CDN
- **JWT authentication** with email verification system

### API Organization
```
app/
├── api/          # API route handlers
├── core/         # Configuration and database setup
├── models/       # SQLAlchemy database models
├── schemas/      # Pydantic request/response models
└── services/     # Business logic (auth, media, S3)
```

### Key Models
- **User**: User accounts with profile management
- **Feed**: Social media posts with file attachments
- **File**: Media files (images/videos) stored in S3
- **Comment**: Nested comments on feeds
- **FeedLike/CommentLike**: Like system for social interactions
- **Verify**: Email verification tokens
- **Privacy**: Privacy policy acceptance tracking

### Media Handling
- **Dual CDN setup**: IMAGE_BASE_URL for images/thumbnails, STORAGE_BASE_URL for videos
- **S3 integration**: Direct upload with thumbnail generation
- **Video processing**: MoviePy for video manipulation, frame ratio extraction
- **Image processing**: OpenCV and Pillow for image operations

### Configuration
- **Environment-based settings** via Pydantic Settings
- **Required environment variables**: Database credentials, AWS keys, JWT secrets, CDN URLs
- **Database URL construction** automatically handles MySQL connection string

### Authentication Flow
- JWT-based authentication with 7-day token expiry
- Email verification system with temporary tokens
- Password hashing with bcrypt

## Commit Conventions

- Do not commit until explicitly requested
- Use "/" to separate multiple work items in commit messages
- Always use virtual environment for migration work