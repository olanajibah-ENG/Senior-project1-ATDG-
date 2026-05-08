# 📋 Postman Test Cases - Notification Service (Async with Celery)

---

## **1️⃣ Create Project Notification (Async)**

### ✅ Test Case 1.1: Create Project Notification - Success

**Endpoint:**
```
POST http://localhost:8000/api/notifications/project/
```

**Request Headers:**
```json
Content-Type: application/json
```

**Request Body:**
```json
{
  "user_email": "user@example.com",
  "action": "created",
  "project_name": "AutoTest Project",
  "project_id": "project_123",
  "user_name": "Ahmed",
  "user_id": "user_456"
}
```

**Expected Response (202 Accepted - لسه بتتعالج!):**
```json
{
  "message": "Notification is being sent",
  "task_id": "abc123def456ghi789",
  "notification_id": 1,
  "status": "processing",
  "type": "PROJECT_CREATED"
}
```

**HTTP Status Code:** `202 Accepted` ✅

---

### ❌ Test Case 1.2: Missing Required Fields

**Request Body (بدون project_name):**
```json
{
  "user_email": "user@example.com",
  "action": "created",
  "project_id": "project_123"
}
```

**Expected Response:**
```json
{
  "error": "Required data: user_email, action, project_name"
}
```

**HTTP Status Code:** `400 Bad Request` ✅

---

### ✅ Test Case 1.3: Delete Project Notification

**Request Body (action = deleted):**
```json
{
  "user_email": "user@example.com",
  "action": "deleted",
  "project_name": "Old Project",
  "project_id": "project_old_123",
  "user_name": "Ahmed"
}
```

**Expected Response:**
```json
{
  "message": "Notification is being sent",
  "task_id": "xyz789uvw456rst123",
  "notification_id": 2,
  "status": "processing",
  "type": "PROJECT_DELETED"
}
```

**HTTP Status Code:** `202 Accepted` ✅

---

## **2️⃣ Create Code Notification (Async)**

### ✅ Test Case 2.1: Add Code Notification

**Endpoint:**
```
POST http://localhost:8000/api/notifications/code/
```

**Request Body:**
```json
{
  "user_email": "user@example.com",
  "action": "added",
  "code_name": "auth_handler.py",
  "project_name": "AutoTest Project",
  "code_id": "code_789",
  "user_name": "Ahmed",
  "user_id": "user_456"
}
```

**Expected Response:**
```json
{
  "message": "Notification is being sent",
  "task_id": "qwe123asd456zxc789",
  "notification_id": 3,
  "status": "processing",
  "type": "CODE_ADDED"
}
```

**HTTP Status Code:** `202 Accepted` ✅

---

### ✅ Test Case 2.2: Delete Code Notification

**Request Body (action = deleted):**
```json
{
  "user_email": "user@example.com",
  "action": "deleted",
  "code_name": "old_handler.py",
  "project_name": "AutoTest Project",
  "code_id": "code_old_789"
}
```

**Expected Response:**
```json
{
  "message": "Notification is being sent",
  "task_id": "poi456lkj789mno123",
  "notification_id": 4,
  "status": "processing",
  "type": "CODE_DELETED"
}
```

---

## **3️⃣ Create Documentation Notification (Async)**

### ✅ Test Case 3.1: Export Documentation

**Endpoint:**
```
POST http://localhost:8000/api/notifications/documentation/
```

**Request Body:**
```json
{
  "user_email": "user@example.com",
  "file_name": "API_Documentation.pdf",
  "file_type": "pdf",
  "project_name": "AutoTest Project",
  "user_name": "Ahmed",
  "user_id": "user_456"
}
```

**Expected Response:**
```json
{
  "message": "Notification is being sent",
  "task_id": "bnm890qaz321uik456",
  "notification_id": 5,
  "status": "processing",
  "type": "DOCUMENTATION_EXPORTED"
}
```

**HTTP Status Code:** `202 Accepted` ✅

---

## **4️⃣ Create Custom Notification (Async)**

### ✅ Test Case 4.1: Custom Notification with All Fields

**Endpoint:**
```
POST http://localhost:8000/api/notifications/custom/
```

**Request Body:**
```json
{
  "user_email": "user@example.com",
  "title": "Build Completed Successfully",
  "message": "Your project build has completed with 0 errors and 5 warnings.",
  "notification_type": "CUSTOM",
  "user_name": "Ahmed",
  "user_id": "user_456",
  "priority": "HIGH",
  "action_url": "https://example.com/project/123/build",
  "action_text": "View Build Details"
}
```

**Expected Response:**
```json
{
  "message": "Notification is being sent",
  "task_id": "vbn567ewq890rtz234",
  "notification_id": 6,
  "status": "processing"
}
```

**HTTP Status Code:** `202 Accepted` ✅

---

## **5️⃣ Get Notification Task Status (الـ Status Tracker)**

### ✅ Test Case 5.1: Check Task Status - Processing

**Endpoint:**
```
GET http://localhost:8000/api/notifications/task-status/?task_id=abc123def456ghi789
```

**Expected Response (لسه بتتعالج):**
```json
{
  "task_id": "abc123def456ghi789",
  "status": "PROCESSING",
  "notification_id": 1,
  "notification_type": "PROJECT_CREATED",
  "created_at": "2026-02-09T10:30:00Z",
  "sent_at": null,
  "message": "Notification is being sent...",
  "progress": 50
}
```

**HTTP Status Code:** `200 OK` ✅

---

### ✅ Test Case 5.2: Check Task Status - Completed

**Endpoint:**
```
GET http://localhost:8000/api/notifications/task-status/?task_id=abc123def456ghi789
```

**Expected Response (خلصت بنجاح):**
```json
{
  "task_id": "abc123def456ghi789",
  "status": "SENT",
  "notification_id": 1,
  "notification_type": "PROJECT_CREATED",
  "created_at": "2026-02-09T10:30:00Z",
  "sent_at": "2026-02-09T10:30:05Z",
  "message": "Notification sent successfully",
  "progress": 100,
  "title": "Project created",
  "recipient": "user@example.com"
}
```

**HTTP Status Code:** `200 OK` ✅

---

### ❌ Test Case 5.3: Check Task Status - Failed

**Endpoint:**
```
GET http://localhost:8000/api/notifications/task-status/?task_id=invalid_task_id
```

**Expected Response (البريد فشل):**
```json
{
  "task_id": "failed_task_id",
  "status": "FAILED",
  "notification_id": 7,
  "notification_type": "PROJECT_CREATED",
  "created_at": "2026-02-09T10:35:00Z",
  "sent_at": null,
  "message": "Failed to send notification",
  "progress": 0,
  "error_message": "SMTP connection timeout: Connection refused at host mail.gmail.com:587"
}
```

**HTTP Status Code:** `200 OK` ✅

---

### ❌ Test Case 5.4: Task Not Found

**Endpoint:**
```
GET http://localhost:8000/api/notifications/task-status/?task_id=nonexistent_task
```

**Expected Response:**
```json
{
  "error": "Task not found",
  "task_id": "nonexistent_task"
}
```

**HTTP Status Code:** `404 Not Found` ✅

---

## **6️⃣ System Alert Notification**

### ✅ Test Case 6.1: Create System Alert

**Endpoint:**
```
POST http://localhost:8000/api/notifications/system/
```

**Request Body:**
```json
{
  "user_email": "admin@example.com",
  "alert_type": "database_error",
  "message": "Database connection failed. Please check Redis connection.",
  "user_name": "System Admin",
  "user_id": "admin_001"
}
```

**Expected Response:**
```json
{
  "message": "System alert is being sent",
  "task_id": "hlj234mno567pqr890",
  "notification_id": 8,
  "status": "processing",
  "type": "SYSTEM_ALERT"
}
```

**HTTP Status Code:** `202 Accepted` ✅

---

## **7️⃣ User Notification**

### ✅ Test Case 7.1: User Registration Notification

**Endpoint:**
```
POST http://localhost:8000/api/notifications/user/
```

**Request Body:**
```json
{
  "user_email": "newuser@example.com",
  "action": "registered",
  "user_name": "Fatima",
  "user_id": "user_999"
}
```

**Expected Response:**
```json
{
  "message": "Notification is being sent",
  "task_id": "stu567vwx890yza123",
  "notification_id": 9,
  "status": "processing",
  "type": "USER_REGISTERED"
}
```

**HTTP Status Code:** `202 Accepted` ✅

---

### ✅ Test Case 7.2: Password Changed Notification

**Request Body (action = password_changed):**
```json
{
  "user_email": "user@example.com",
  "action": "password_changed",
  "user_name": "Ahmed",
  "user_id": "user_456"
}
```

**Expected Response:**
```json
{
  "message": "Notification is being sent",
  "task_id": "bcd234efg567hij890",
  "notification_id": 10,
  "status": "processing",
  "type": "PASSWORD_CHANGED"
}
```

**HTTP Status Code:** `202 Accepted` ✅

---

## **8️⃣ Get Notification List**

### ✅ Test Case 8.1: Get All Notifications

**Endpoint:**
```
GET http://localhost:8000/api/notifications/
```

**Expected Response:**
```json
{
  "count": 10,
  "next": "http://localhost:8000/api/notifications/?page=2",
  "previous": null,
  "results": [
    {
      "id": 10,
      "user_email": "user@example.com",
      "title": "Password changed",
      "message": "Your account has been password changed",
      "notification_type": "PASSWORD_CHANGED",
      "status": "SENT",
      "priority": "CRITICAL",
      "is_read": false,
      "created_at": "2026-02-09T10:40:00Z",
      "sent_at": "2026-02-09T10:40:05Z"
    },
    {
      "id": 9,
      "user_email": "newuser@example.com",
      "title": "User registered",
      "message": "Your account has been registered",
      "notification_type": "USER_REGISTERED",
      "status": "SENT",
      "priority": "HIGH",
      "is_read": false,
      "created_at": "2026-02-09T10:35:00Z",
      "sent_at": "2026-02-09T10:35:05Z"
    }
  ]
}
```

**HTTP Status Code:** `200 OK` ✅

---

### ✅ Test Case 8.2: Get Notifications for Specific User

**Endpoint:**
```
GET http://localhost:8000/api/notifications/?user_id=user_456
```

**Expected Response:** (نفس البنية بس فقط للـ user_456)

---

## **9️⃣ Mark Notification as Read**

### ✅ Test Case 9.1: Mark Single Notification as Read

**Endpoint:**
```
PATCH http://localhost:8000/api/notifications/1/mark-read/
```

**Expected Response:**
```json
{
  "id": 1,
  "user_email": "user@example.com",
  "title": "Project created",
  "status": "READ",
  "is_read": true,
  "read_at": "2026-02-09T10:50:00Z"
}
```

**HTTP Status Code:** `200 OK` ✅

---

### ✅ Test Case 9.2: Mark All Notifications as Read

**Endpoint:**
```
POST http://localhost:8000/api/notifications/mark-all-read/
```

**Request Body:**
```json
{
  "user_id": "user_456"
}
```

**Expected Response:**
```json
{
  "message": "Marked 5 notifications as read",
  "updated_count": 5
}
```

**HTTP Status Code:** `200 OK` ✅

---

## **🔟 Get Notification Statistics**

### ✅ Test Case 10.1: Get Stats for Specific User

**Endpoint:**
```
GET http://localhost:8000/api/notifications/stats/?user_id=user_456
```

**Expected Response:**
```json
{
  "total": 10,
  "unread": 3,
  "read": 7
}
```

**HTTP Status Code:** `200 OK` ✅

---

## **1️⃣1️⃣ Get Notification Details**

### ✅ Test Case 11.1: Get Single Notification Details

**Endpoint:**
```
GET http://localhost:8000/api/notifications/1/
```

**Expected Response:**
```json
{
  "id": 1,
  "user_email": "user@example.com",
  "user_name": "Ahmed",
  "title": "Project created",
  "message": "Project 'AutoTest Project' has been created",
  "notification_type": "PROJECT_CREATED",
  "status": "SENT",
  "priority": "HIGH",
  "is_read": true,
  "task_id": "abc123def456ghi789",
  "created_at": "2026-02-09T10:30:00Z",
  "sent_at": "2026-02-09T10:30:05Z",
  "read_at": "2026-02-09T10:50:00Z",
  "extra_data": {
    "project_name": "AutoTest Project",
    "action": "created"
  }
}
```

**HTTP Status Code:** `200 OK` ✅

---

## **1️⃣2️⃣ Error Handling Test Cases**

### ❌ Test Case 12.1: Invalid Email

**Endpoint:**
```
POST http://localhost:8000/api/notifications/project/
```

**Request Body:**
```json
{
  "user_email": "invalid-email",
  "action": "created",
  "project_name": "Test Project"
}
```

**Expected Response:**
```json
{
  "message": "Notification is being sent",
  "task_id": "err123qwe456rty789",
  "notification_id": 11,
  "status": "processing"
}
```

**Note:** الـ Celery task بيحاول يرسل البريد، لو الإيميل غلط بيفشل والـ status بيصير `FAILED`

**Check Status:**
```
GET http://localhost:8000/api/notifications/task-status/?task_id=err123qwe456rty789
```

**Expected Response (بعد فترة):**
```json
{
  "status": "FAILED",
  "error_message": "Invalid email address: invalid-email",
  "progress": 0
}
```

---

### ❌ Test Case 12.2: Missing task_id Parameter

**Endpoint:**
```
GET http://localhost:8000/api/notifications/task-status/
```

**Expected Response:**
```json
{
  "error": "task_id is required"
}
```

**HTTP Status Code:** `400 Bad Request` ✅

---

## **🎯 Test Summary Table**

| # | Test Case | Method | Status Expected | Input | Output |
|---|-----------|--------|-----------------|-------|--------|
| 1.1 | Create Project | POST | 202 | Valid data | task_id ✅ |
| 1.2 | Missing Fields | POST | 400 | Missing field | error ❌ |
| 2.1 | Add Code | POST | 202 | Valid data | task_id ✅ |
| 3.1 | Export Docs | POST | 202 | Valid data | task_id ✅ |
| 4.1 | Custom Notif | POST | 202 | Valid data | task_id ✅ |
| 5.1 | Task Status (Processing) | GET | 200 | task_id | status: PROCESSING |
| 5.2 | Task Status (Sent) | GET | 200 | task_id | status: SENT ✅ |
| 5.3 | Task Status (Failed) | GET | 200 | task_id | status: FAILED ❌ |
| 5.4 | Task Not Found | GET | 404 | invalid task_id | error ❌ |
| 6.1 | System Alert | POST | 202 | Valid data | task_id ✅ |
| 7.1 | User Register | POST | 202 | Valid data | task_id ✅ |
| 7.2 | Password Change | POST | 202 | Valid data | task_id ✅ |
| 8.1 | List Notifications | GET | 200 | - | notification list |
| 9.1 | Mark as Read | PATCH | 200 | notif_id | is_read: true |
| 10.1 | Get Stats | GET | 200 | user_id | {total, unread, read} |

---

## **⚡ Important Notes:**

1. **202 Accepted ≠ 201 Created** - الآن نرجع 202 لأنو الشغل بـ Process
2. **task_id is KEY** - استخدمه عشان تتابع الـ notification
3. **Status Polling** - اطلب status كل 5 ثواني:
   ```
   GET /api/notifications/task-status/?task_id=xxx
   ```
4. **Celery Worker لازم يكون شغال** عشان الـ tasks تتنفذ
5. **Redis لازم يكون متصل** عشان البروكر يشتغل

