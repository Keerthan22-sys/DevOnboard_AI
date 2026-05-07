# Think Tank Platform — Authentication & Authorization

## Authentication Flow

The platform uses Keycloak as the identity provider with OIDC (OpenID Connect) for SSO.

### Login Flow

1. User visits `thinktank.mhp.com` and clicks "Sign In"
2. Frontend redirects to Keycloak authorization endpoint
3. Keycloak displays the MHP Active Directory login page
4. User enters corporate credentials (email + password)
5. Keycloak validates against Active Directory via LDAP federation
6. On success, Keycloak issues an authorization code
7. Frontend exchanges the code for access + refresh tokens via the backend
8. Backend validates the tokens, creates/updates the local user record
9. Backend issues a session JWT (1-hour expiry) containing: `user_id`, `role`, `team_id`
10. Frontend stores the JWT in an HttpOnly cookie and attaches it to all API requests

### Token Refresh

- Access tokens expire after **1 hour**
- Refresh tokens expire after **24 hours**
- The frontend uses an Axios interceptor to detect 401 responses and automatically refresh
- If refresh fails, user is redirected to the login page

### Session Management

- Sessions are stored in Redis with key pattern `session:{user_id}:{session_id}`
- Maximum 5 concurrent sessions per user
- Admin can force-expire all sessions for a user via the User Service API

## Authorization Model

### Roles

| Role | Description | Permissions |
|------|-------------|-------------|
| admin | Platform administrator | Full access: manage users, teams, spaces, all articles |
| editor | Content creator | Create/edit articles in assigned spaces, manage own content |
| viewer | Read-only user | View published articles in accessible spaces |

### Space-Level Permissions

Each space has a visibility setting that controls access:

- **public:** All authenticated users can read. Editors in the owning team can write.
- **private:** Only members of the owning team can read or write.
- **team:** Members of the owning team and explicitly invited users can access.

### API Authorization

Every API endpoint checks authorization in this order:

1. **JWT validation** — Is the token valid and not expired?
2. **User existence** — Does the user still exist in the database?
3. **Role check** — Does the user's role permit this action?
4. **Resource check** — Does the user have access to the specific resource (space, article)?

The authorization middleware is implemented in `api-gateway/src/middleware/auth.ts` and uses decorators:

```typescript
@RequireAuth()                    // Any authenticated user
@RequireRole('admin')             // Admin only
@RequireSpaceAccess('editor')     // Editor access to the space
```

## API Keys

For service-to-service communication and CI/CD integrations:

- API keys are generated per-team via the admin dashboard
- Keys are scoped to specific spaces and operations
- Rate limited to 1000 requests/minute per key
- Keys can be rotated without downtime (grace period of 24 hours for old key)
