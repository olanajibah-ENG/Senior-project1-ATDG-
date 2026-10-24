# Frontend API Guide - Projects Endpoints

This guide provides comprehensive documentation for frontend developers working with the UPM (University Project Management) API, specifically focusing on the Projects endpoints.

## Table of Contents
- [Base URL](#base-url)
- [Authentication](#authentication)
- [Projects Endpoints](#projects-endpoints)
- [Request/Response Schemas](#requestresponse-schemas)
- [Error Handling](#error-handling)
- [Pagination](#pagination)
- [Examples](#examples)

---

## Base URL

All API endpoints are prefixed with `/api/upm/`:

```
Base URL: http://localhost:8000/api/upm/
```

**Note:** In production, replace `localhost:8000` with your actual server domain.

---

## Authentication

All project endpoints require authentication using **JWT (JSON Web Tokens)**.

### Getting an Access Token

1. **Register a new user:**
   ```
   POST /api/upm/signup/
   ```

2. **Login to get tokens:**
   ```
   POST /api/upm/login/
   ```

### Using the Access Token

Include the access token in the `Authorization` header of all authenticated requests:

```
Authorization: Bearer <your_access_token>
```

**Example:**
```javascript
headers: {
  'Authorization': 'Bearer eyJ0eXAiOiJKV1QiLCJhbGc...',
  'Content-Type': 'application/json'
}
```

### Token Refresh

If your access token expires, use the refresh token to get a new one:

```
POST /api/token/refresh/
Body: { "refresh": "<your_refresh_token>" }
```

---

## Projects Endpoints

### 1. List All Projects (GET)

Retrieve a paginated list of all projects for the authenticated user.

**Endpoint:**
```
GET /api/upm/projects/
```

**Authentication:** Required

**Query Parameters:**
- `page` (optional): Page number (default: 1)
- `page_size` (optional): Number of items per page (default: 20, max: 100)

**Response:** `200 OK`

**Response Schema:**
```json
{
  "count": 50,
  "next": "http://localhost:8000/api/upm/projects/?page=2",
  "previous": null,
  "results": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "title": "My Project",
      "description": "Project description",
      "user": 1,
      "username": "john_doe",
      "created_at": "2024-01-15T10:30:00Z",
      "updated_at": "2024-01-15T10:30:00Z"
    }
  ]
}
```

**Field Descriptions:**
- `id` (UUID): Unique project identifier
- `title` (string): Project title/name
- `description` (string): Project description (can be empty)
- `user` (integer): User ID of the project owner
- `username` (string): Username of the project owner
- `created_at` (datetime): Project creation timestamp (ISO 8601 format)
- `updated_at` (datetime): Last modification timestamp (ISO 8601 format)

---

### 2. Create a New Project (POST)

Create a new project for the authenticated user.

**Endpoint:**
```
POST /api/upm/projects/
```

**Authentication:** Required

**Request Body:**
```json
{
  "title": "My New Project",
  "description": "Optional project description"
}
```

**Request Schema:**
- `title` (string, required): Project title. Must not be empty or whitespace only. Max length: 255 characters.
- `description` (string, optional): Project description. Can be empty or omitted.

**Response:** `201 Created`

**Response Schema:**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "title": "My New Project",
  "description": "Optional project description",
  "user": 1,
  "username": "john_doe",
  "created_at": "2024-01-15T10:30:00Z",
  "updated_at": "2024-01-15T10:30:00Z"
}
```

**Validation Rules:**
- `title` is required and cannot be empty or contain only whitespace
- `title` will be automatically trimmed of leading/trailing whitespace
- `description` is optional and can be an empty string

---

### 3. Retrieve a Single Project (GET)

Get detailed information about a specific project.

**Endpoint:**
```
GET /api/upm/projects/{project_id}/
```

**Authentication:** Required

**URL Parameters:**
- `project_id` (UUID, required): The unique identifier of the project

**Response:** `200 OK`

**Response Schema:**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "title": "My Project",
  "description": "Project description",
  "user": 1,
  "username": "john_doe",
  "created_at": "2024-01-15T10:30:00Z",
  "updated_at": "2024-01-15T10:30:00Z"
}
```

**Note:** Users can only retrieve their own projects. Attempting to access another user's project will return a `404 Not Found` error.

---

### 4. Update a Project (PUT/PATCH)

Update an existing project. You can use either `PUT` (full update) or `PATCH` (partial update).

**Endpoint:**
```
PUT /api/upm/projects/{project_id}/
PATCH /api/upm/projects/{project_id}/
```

**Authentication:** Required

**URL Parameters:**
- `project_id` (UUID, required): The unique identifier of the project

**Request Body (PUT - Full Update):**
```json
{
  "title": "Updated Project Title",
  "description": "Updated description"
}
```

**Request Body (PATCH - Partial Update):**
```json
{
  "title": "Updated Project Title"
}
```
or
```json
{
  "description": "Updated description only"
}
```

**Request Schema:**
- `title` (string, optional): Project title. If provided, must not be empty or whitespace only. Max length: 255 characters.
- `description` (string, optional): Project description. Can be empty.

**Response:** `200 OK`

**Response Schema:**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "title": "Updated Project Title",
  "description": "Updated description",
  "user": 1,
  "username": "john_doe",
  "created_at": "2024-01-15T10:30:00Z",
  "updated_at": "2024-01-15T11:45:00Z"
}
```

**Validation Rules:**
- `title` cannot be empty or contain only whitespace if provided
- `title` will be automatically trimmed of leading/trailing whitespace
- At least one field (`title` or `description`) must be provided

**Note:** Users can only update their own projects.

---

### 5. Delete a Project (DELETE)

Delete a project permanently.

**Endpoint:**
```
DELETE /api/upm/projects/{project_id}/
```

**Authentication:** Required

**URL Parameters:**
- `project_id` (UUID, required): The unique identifier of the project

**Response:** `204 No Content`

**Response Body:** Empty

**Note:** 
- This operation is permanent and cannot be undone
- Users can only delete their own projects
- Attempting to delete a non-existent project or another user's project will return a `404 Not Found` error

---

## Request/Response Schemas

### Project Object Schema

```typescript
interface Project {
  id: string;              // UUID format
  title: string;           // Required, max 255 chars
  description: string;     // Optional, can be empty
  user: number;            // User ID (read-only)
  username: string;        // Username (read-only)
  created_at: string;      // ISO 8601 datetime (read-only)
  updated_at: string;      // ISO 8601 datetime (read-only)
}
```

### Create Project Request Schema

```typescript
interface CreateProjectRequest {
  title: string;           // Required, non-empty
  description?: string;    // Optional
}
```

### Update Project Request Schema

```typescript
interface UpdateProjectRequest {
  title?: string;          // Optional, non-empty if provided
  description?: string;    // Optional
}
```

### Paginated Response Schema

```typescript
interface PaginatedResponse<T> {
  count: number;           // Total number of items
  next: string | null;     // URL to next page
  previous: string | null; // URL to previous page
  results: T[];            // Array of items
}
```

---

## Error Handling

The API uses standard HTTP status codes and returns error details in JSON format.

### Common Status Codes

- `200 OK`: Request successful
- `201 Created`: Resource created successfully
- `204 No Content`: Resource deleted successfully
- `400 Bad Request`: Invalid request data or validation error
- `401 Unauthorized`: Authentication required or invalid token
- `404 Not Found`: Resource not found or access denied
- `500 Internal Server Error`: Server error

### Error Response Format

```json
{
  "detail": "Error message description"
}
```

or for validation errors:

```json
{
  "field_name": ["Error message for this field"],
  "another_field": ["Another error message"]
}
```

### Example Error Responses

**401 Unauthorized (Missing/Invalid Token):**
```json
{
  "detail": "Authentication credentials were not provided."
}
```

**400 Bad Request (Validation Error):**
```json
{
  "title": ["Title is required and cannot be empty."]
}
```

**404 Not Found:**
```json
{
  "detail": "Not found."
}
```

---

## Pagination

The list projects endpoint uses **page-based pagination**.

### Default Settings
- **Page size:** 20 items per page
- **Maximum page size:** 100 items per page
- **Page size parameter:** `page_size`

### Pagination Query Parameters

- `page`: Page number (starts from 1)
- `page_size`: Number of items per page (1-100)

### Example Requests

```
GET /api/upm/projects/?page=1&page_size=10
GET /api/upm/projects/?page=2
```

### Pagination Response Structure

```json
{
  "count": 50,
  "next": "http://localhost:8000/api/upm/projects/?page=3",
  "previous": "http://localhost:8000/api/upm/projects/?page=1",
  "results": [...]
}
```

**Fields:**
- `count`: Total number of items across all pages
- `next`: URL to the next page (null if on last page)
- `previous`: URL to the previous page (null if on first page)
- `results`: Array of project objects for the current page

---

## Examples

### JavaScript/TypeScript Examples

#### 1. List All Projects

```javascript
async function listProjects(page = 1, pageSize = 20) {
  const response = await fetch(
    `http://localhost:8000/api/upm/projects/?page=${page}&page_size=${pageSize}`,
    {
      method: 'GET',
      headers: {
        'Authorization': `Bearer ${accessToken}`,
        'Content-Type': 'application/json'
      }
    }
  );
  
  if (!response.ok) {
    throw new Error(`HTTP error! status: ${response.status}`);
  }
  
  return await response.json();
}
```

#### 2. Create a New Project

```javascript
async function createProject(title, description = '') {
  const response = await fetch('http://localhost:8000/api/upm/projects/', {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${accessToken}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      title: title,
      description: description
    })
  });
  
  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || JSON.stringify(error));
  }
  
  return await response.json();
}
```

#### 3. Get a Single Project

```javascript
async function getProject(projectId) {
  const response = await fetch(
    `http://localhost:8000/api/upm/projects/${projectId}/`,
    {
      method: 'GET',
      headers: {
        'Authorization': `Bearer ${accessToken}`,
        'Content-Type': 'application/json'
      }
    }
  );
  
  if (!response.ok) {
    throw new Error(`HTTP error! status: ${response.status}`);
  }
  
  return await response.json();
}
```

#### 4. Update a Project (PATCH)

```javascript
async function updateProject(projectId, updates) {
  const response = await fetch(
    `http://localhost:8000/api/upm/projects/${projectId}/`,
    {
      method: 'PATCH',
      headers: {
        'Authorization': `Bearer ${accessToken}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(updates)
    }
  );
  
  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || JSON.stringify(error));
  }
  
  return await response.json();
}

// Usage:
// updateProject(projectId, { title: 'New Title' });
// updateProject(projectId, { description: 'New Description' });
// updateProject(projectId, { title: 'New Title', description: 'New Description' });
```

#### 5. Delete a Project

```javascript
async function deleteProject(projectId) {
  const response = await fetch(
    `http://localhost:8000/api/upm/projects/${projectId}/`,
    {
      method: 'DELETE',
      headers: {
        'Authorization': `Bearer ${accessToken}`,
        'Content-Type': 'application/json'
      }
    }
  );
  
  if (!response.ok) {
    throw new Error(`HTTP error! status: ${response.status}`);
  }
  
  // DELETE returns 204 No Content, so no JSON to parse
  return true;
}
```

#### 6. Complete Example with Error Handling

```javascript
class ProjectAPI {
  constructor(baseURL, accessToken) {
    this.baseURL = baseURL;
    this.accessToken = accessToken;
  }

  async request(endpoint, options = {}) {
    const url = `${this.baseURL}${endpoint}`;
    const config = {
      ...options,
      headers: {
        'Authorization': `Bearer ${this.accessToken}`,
        'Content-Type': 'application/json',
        ...options.headers
      }
    };

    try {
      const response = await fetch(url, config);
      
      if (!response.ok) {
        const error = await response.json().catch(() => ({ 
          detail: `HTTP ${response.status}` 
        }));
        throw new Error(error.detail || JSON.stringify(error));
      }
      
      // Handle 204 No Content
      if (response.status === 204) {
        return null;
      }
      
      return await response.json();
    } catch (error) {
      console.error('API request failed:', error);
      throw error;
    }
  }

  async listProjects(page = 1, pageSize = 20) {
    return this.request(`/projects/?page=${page}&page_size=${pageSize}`);
  }

  async createProject(title, description = '') {
    return this.request('/projects/', {
      method: 'POST',
      body: JSON.stringify({ title, description })
    });
  }

  async getProject(projectId) {
    return this.request(`/projects/${projectId}/`);
  }

  async updateProject(projectId, updates) {
    return this.request(`/projects/${projectId}/`, {
      method: 'PATCH',
      body: JSON.stringify(updates)
    });
  }

  async deleteProject(projectId) {
    return this.request(`/projects/${projectId}/`, {
      method: 'DELETE'
    });
  }
}

// Usage:
const api = new ProjectAPI('http://localhost:8000/api/upm', accessToken);

try {
  const projects = await api.listProjects();
  console.log('Projects:', projects);
  
  const newProject = await api.createProject('My Project', 'Description');
  console.log('Created:', newProject);
  
  const updated = await api.updateProject(newProject.id, { 
    title: 'Updated Title' 
  });
  console.log('Updated:', updated);
  
  await api.deleteProject(newProject.id);
  console.log('Deleted successfully');
} catch (error) {
  console.error('Error:', error.message);
}
```

### React Example Hook

```javascript
import { useState, useEffect } from 'react';

function useProjects(accessToken) {
  const [projects, setProjects] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [pagination, setPagination] = useState({
    page: 1,
    pageSize: 20,
    count: 0,
    hasNext: false,
    hasPrevious: false
  });

  const fetchProjects = async (page = 1, pageSize = 20) => {
    setLoading(true);
    setError(null);
    
    try {
      const response = await fetch(
        `http://localhost:8000/api/upm/projects/?page=${page}&page_size=${pageSize}`,
        {
          headers: {
            'Authorization': `Bearer ${accessToken}`,
            'Content-Type': 'application/json'
          }
        }
      );
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      const data = await response.json();
      setProjects(data.results);
      setPagination({
        page,
        pageSize,
        count: data.count,
        hasNext: !!data.next,
        hasPrevious: !!data.previous
      });
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchProjects();
  }, [accessToken]);

  return {
    projects,
    loading,
    error,
    pagination,
    refetch: fetchProjects
  };
}
```

---

## Additional Resources

### API Documentation

The project includes Swagger/OpenAPI documentation:

- **Swagger UI:** `http://localhost:8000/swagger/`
- **ReDoc:** `http://localhost:8000/redoc/`

These interactive documentation interfaces allow you to explore and test all endpoints directly from your browser.

### CORS Configuration

The API is configured to handle CORS requests. Make sure your frontend origin is included in the allowed origins if you encounter CORS issues.

---

## Summary

### Quick Reference

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| GET | `/api/upm/projects/` | List all projects | Yes |
| POST | `/api/upm/projects/` | Create new project | Yes |
| GET | `/api/upm/projects/{id}/` | Get single project | Yes |
| PUT/PATCH | `/api/upm/projects/{id}/` | Update project | Yes |
| DELETE | `/api/upm/projects/{id}/` | Delete project | Yes |

### Key Points

1. **Authentication:** All endpoints require JWT Bearer token authentication
2. **User Isolation:** Users can only access their own projects
3. **Pagination:** List endpoint supports pagination (default: 20 items per page)
4. **Validation:** Title is required and cannot be empty; description is optional
5. **UUIDs:** Project IDs are UUIDs, not integers
6. **Timestamps:** All datetime fields are in ISO 8601 format (UTC)

---

## Support

For questions or issues, please contact the backend development team or refer to the Swagger documentation at `/swagger/`.

