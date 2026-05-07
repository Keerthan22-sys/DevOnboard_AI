# Think Tank Platform — Search Implementation

## Overview

The search functionality is powered by Elasticsearch 8.x and is implemented in the `search-service/`. It provides full-text search across all articles, with faceted filtering and relevance ranking.

## Architecture

### Indexing Pipeline

When an article is created or updated:

1. Knowledge Service publishes an `article.updated` event to RabbitMQ
2. Search Service consumes the event
3. Article content (Markdown) is converted to plain text
4. Text is analyzed with a custom analyzer (English stemming + edge n-grams)
5. Document is indexed in Elasticsearch with metadata

### Elasticsearch Index Mapping

```json
{
  "mappings": {
    "properties": {
      "title": { "type": "text", "analyzer": "english_custom", "boost": 2.0 },
      "content": { "type": "text", "analyzer": "english_custom" },
      "author_name": { "type": "keyword" },
      "space_slug": { "type": "keyword" },
      "tags": { "type": "keyword" },
      "status": { "type": "keyword" },
      "published_at": { "type": "date" },
      "updated_at": { "type": "date" }
    }
  }
}
```

### Search API

**Endpoint:** `GET /api/search?q=<query>&space=<slug>&tags=<tag1,tag2>&page=1&size=20`

**Response:**
```json
{
  "hits": [
    {
      "id": "article-uuid",
      "title": "Setting Up Local Development",
      "snippet": "...highlighted match...",
      "space": "engineering",
      "score": 12.5,
      "updated_at": "2026-01-15T10:30:00Z"
    }
  ],
  "total": 142,
  "facets": {
    "spaces": [{"name": "engineering", "count": 45}],
    "tags": [{"name": "setup", "count": 12}]
  }
}
```

## Implementation Details

The search service code is located at:

- `search-service/src/indexer.ts` — Consumes RabbitMQ events and indexes documents
- `search-service/src/searcher.ts` — Handles search queries with filtering and pagination
- `search-service/src/analyzer.ts` — Custom Elasticsearch analyzer configuration
- `search-service/src/routes/search.ts` — Express route handlers

### Relevance Tuning

- Title matches are boosted 2x over content matches
- Recently updated articles get a recency boost (decay function, half-life = 30 days)
- Articles with more views get a slight popularity boost
- Exact phrase matches are boosted 3x
