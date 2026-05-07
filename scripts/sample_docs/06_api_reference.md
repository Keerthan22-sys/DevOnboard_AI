# Think Tank Platform — API Reference

## Base URL

- Development: `http://localhost:4000/api`
- Staging: `https://staging.thinktank.mhp.internal/api`
- Production: `https://thinktank.mhp.com/api`

## Authentication

All endpoints require a valid JWT in the `Authorization` header:
```
Authorization: Bearer <jwt_token>
```

## Endpoints

### Articles

#### Create Article
```
POST /api/articles
Content-Type: application/json

{
  "title": "Getting Started Guide",
  "content": "# Welcome\n\nThis guide...",
  "space_id": "uuid",
  "tags": ["onboarding", "guide"],
  "status": "draft"
}

Response: 201 Created
{
  "id": "uuid",
  "title": "Getting Started Guide",
  "status": "draft",
  "author": { "id": "uuid", "name": "Keerthan" },
  "created_at": "2026-03-20T10:00:00Z"
}
```

#### List Articles
```
GET /api/articles?space_id=<uuid>&status=published&page=1&size=20

Response: 200 OK
{
  "data": [...],
  "pagination": { "page": 1, "size": 20, "total": 142 }
}
```

#### Get Article
```
GET /api/articles/:id

Response: 200 OK
{
  "id": "uuid",
  "title": "...",
  "content": "...",
  "version": 3,
  "author": {...},
  "space": {...},
  "tags": [...],
  "created_at": "...",
  "updated_at": "..."
}
```

#### Update Article
```
PUT /api/articles/:id
{
  "title": "Updated Title",
  "content": "Updated content..."
}

Response: 200 OK
```

#### Delete Article
```
DELETE /api/articles/:id
Response: 204 No Content
```

### Spaces

#### List Spaces
```
GET /api/spaces
Response: 200 OK
{
  "data": [
    { "id": "uuid", "name": "Engineering", "slug": "engineering", "article_count": 45 }
  ]
}
```

#### Create Space
```
POST /api/spaces
{
  "name": "Engineering",
  "description": "Technical documentation and guides",
  "visibility": "public",
  "owner_team_id": "uuid"
}
Response: 201 Created
```

### Teams

#### List Teams
```
GET /api/teams
Response: 200 OK
```

#### Get Team Members
```
GET /api/teams/:id/members
Response: 200 OK
{
  "data": [
    { "id": "uuid", "name": "Keerthan", "email": "keerthan@mhp.com", "role": "admin" }
  ]
}
```

### File Uploads

#### Upload Attachment
```
POST /api/articles/:id/attachments
Content-Type: multipart/form-data
file: <binary>

Response: 201 Created
{
  "id": "uuid",
  "filename": "architecture-diagram.png",
  "url": "https://s3.amazonaws.com/think-tank/...",
  "size_bytes": 245000
}
```
