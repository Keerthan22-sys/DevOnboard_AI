# Think Tank Platform — Database Schema

## Overview

The platform uses PostgreSQL 15 with the following core tables. All tables use UUID primary keys and include `created_at` / `updated_at` timestamps.

## Core Tables

### users
| Column | Type | Description |
|--------|------|-------------|
| id | UUID (PK) | User identifier |
| email | VARCHAR(255) UNIQUE | Corporate email |
| name | VARCHAR(255) | Display name |
| keycloak_id | VARCHAR(255) | SSO identity link |
| role | ENUM('admin','editor','viewer') | Platform role |
| team_id | UUID (FK → teams.id) | Primary team |
| avatar_url | TEXT | Profile picture URL |
| created_at | TIMESTAMPTZ | Account creation |
| updated_at | TIMESTAMPTZ | Last update |

### teams
| Column | Type | Description |
|--------|------|-------------|
| id | UUID (PK) | Team identifier |
| name | VARCHAR(255) | Team name |
| description | TEXT | Team description |
| parent_team_id | UUID (FK → teams.id) | For nested team hierarchy |
| created_at | TIMESTAMPTZ | Creation timestamp |

### articles
| Column | Type | Description |
|--------|------|-------------|
| id | UUID (PK) | Article identifier |
| title | VARCHAR(500) | Article title |
| content | TEXT | Markdown content |
| status | ENUM('draft','published','archived') | Publication status |
| author_id | UUID (FK → users.id) | Original author |
| space_id | UUID (FK → spaces.id) | Knowledge space |
| parent_id | UUID (FK → articles.id) | For hierarchical pages |
| version | INTEGER | Content version number |
| created_at | TIMESTAMPTZ | Creation timestamp |
| updated_at | TIMESTAMPTZ | Last edit |
| published_at | TIMESTAMPTZ | Publication date |

### spaces
| Column | Type | Description |
|--------|------|-------------|
| id | UUID (PK) | Space identifier |
| name | VARCHAR(255) | Space name (e.g., "Engineering", "Product") |
| slug | VARCHAR(255) UNIQUE | URL-friendly identifier |
| description | TEXT | Space purpose |
| visibility | ENUM('public','private','team') | Access level |
| owner_team_id | UUID (FK → teams.id) | Owning team |
| created_at | TIMESTAMPTZ | Creation timestamp |

### tags
| Column | Type | Description |
|--------|------|-------------|
| id | UUID (PK) | Tag identifier |
| name | VARCHAR(100) UNIQUE | Tag label |
| color | VARCHAR(7) | Hex color code |

### article_tags (join table)
| Column | Type | Description |
|--------|------|-------------|
| article_id | UUID (FK → articles.id) | Article reference |
| tag_id | UUID (FK → tags.id) | Tag reference |

## Key Relationships

- **users → teams:** Many-to-one. Each user belongs to exactly one primary team.
- **articles → spaces:** Many-to-one. Each article lives in one knowledge space.
- **articles → articles:** Self-referential. Supports nested page hierarchies (like Confluence).
- **articles ↔ tags:** Many-to-many via `article_tags` join table.
- **spaces → teams:** Many-to-one. Each space is owned by one team.
- **teams → teams:** Self-referential for organizational hierarchy.

## Indexes

- `idx_articles_space_id` on `articles(space_id)` — fast space listing
- `idx_articles_author_id` on `articles(author_id)` — user's articles
- `idx_articles_status` on `articles(status)` — filter by publication state
- `idx_users_email` on `users(email)` — login lookups
- `idx_users_keycloak_id` on `users(keycloak_id)` — SSO resolution
