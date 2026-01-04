# HTTP: The Complete Guide for Software Engineers
## From Protocol Fundamentals to Command-Line Mastery

---

# Part 0: Engineering Foundation

## 1. What IS HTTP?

**HTTP** = **H**yper**T**ext **T**ransfer **P**rotocol

HTTP is the **application-layer protocol** that powers the World Wide Web. Every time you visit a website, call an API, or fetch data — HTTP is involved.

### Key Characteristics

| Property | Meaning | Implication |
|----------|---------|-------------|
| **Text-based** | Messages are human-readable text | You can debug by literally reading the bytes |
| **Stateless** | Each request is independent | Server doesn't remember previous requests |
| **Request-Response** | Client asks, server answers | Always initiated by client, never by server |
| **Layered** | Sits on top of TCP/IP | Doesn't care about network details |

### Where HTTP Fits in the Network Stack

```
┌─────────────────────────────────────────────────────────┐
│  APPLICATION LAYER                                       │
│  ┌─────────────────────────────────────────────────┐    │
│  │  HTTP / HTTPS / WebSocket / gRPC                │    │  ← YOU ARE HERE
│  └─────────────────────────────────────────────────┘    │
├─────────────────────────────────────────────────────────┤
│  TRANSPORT LAYER                                         │
│  ┌─────────────────────────────────────────────────┐    │
│  │  TCP (reliable) / UDP (fast)                    │    │
│  └─────────────────────────────────────────────────┘    │
├─────────────────────────────────────────────────────────┤
│  NETWORK LAYER                                          │
│  ┌─────────────────────────────────────────────────┐    │
│  │  IP (routing packets across the internet)       │    │
│  └─────────────────────────────────────────────────┘    │
├─────────────────────────────────────────────────────────┤
│  LINK LAYER                                             │
│  ┌─────────────────────────────────────────────────────│
│  │  Ethernet / WiFi / Physical cables              │    │
│  └─────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────┘
```

---

## 2. Brief History

| Year | Version | Key Changes |
|------|---------|-------------|
| 1991 | HTTP/0.9 | Single line: `GET /page.html` — response was just HTML |
| 1996 | HTTP/1.0 | Added headers, status codes, POST method |
| 1999 | HTTP/1.1 | Persistent connections, chunked transfer, Host header |
| 2015 | HTTP/2 | Binary protocol, multiplexing, server push |
| 2022 | HTTP/3 | Built on QUIC (UDP-based), even faster |

**For this tutorial**: We focus on HTTP/1.1 because it's text-based and easier to understand manually. The concepts transfer to HTTP/2 and HTTP/3.

---

## 3. The Anatomy of an HTTP Transaction

Every HTTP interaction has exactly two parts:

### 3.1 The Request (Client → Server)

```
┌──────────────────────────────────────────────────────────────┐
│                      HTTP REQUEST                            │
├──────────────────────────────────────────────────────────────┤
│  Request Line:   METHOD /path HTTP/version                   │
├──────────────────────────────────────────────────────────────┤
│  Headers:        Header-Name: Header-Value                   │
│                  Header-Name: Header-Value                   │
│                  ...                                         │
├──────────────────────────────────────────────────────────────┤
│  (blank line)                                                │
├──────────────────────────────────────────────────────────────┤
│  Body:           (optional data)                             │
└──────────────────────────────────────────────────────────────┘
```

**Real Example:**

```http
POST /api/users HTTP/1.1
Host: api.example.com
Content-Type: application/json
Content-Length: 42
Authorization: Bearer abc123

{"name": "Alice", "email": "alice@test.com"}
```

### 3.2 The Response (Server → Client)

```
┌──────────────────────────────────────────────────────────────┐
│                      HTTP RESPONSE                            │
├──────────────────────────────────────────────────────────────┤
│  Status Line:    HTTP/version STATUS_CODE Reason-Phrase      │
├──────────────────────────────────────────────────────────────┤
│  Headers:        Header-Name: Header-Value                   │
│                  Header-Name: Header-Value                   │
│                  ...                                         │
├──────────────────────────────────────────────────────────────┤
│  (blank line)                                                │
├──────────────────────────────────────────────────────────────┤
│  Body:           (the actual content)                        │
└──────────────────────────────────────────────────────────────┘
```

**Real Example:**

```http
HTTP/1.1 201 Created
Content-Type: application/json
Content-Length: 58
Location: /api/users/42

{"id": 42, "name": "Alice", "email": "alice@test.com"}
```

---

# Part 1: HTTP Methods (Verbs)

HTTP methods tell the server **what action** you want to perform.

## Method Reference Table

| Method | Purpose | Has Body? | Idempotent? | Safe? |
|--------|---------|-----------|-------------|-------|
| **GET** | Retrieve data | ❌ No | ✅ Yes | ✅ Yes |
| **POST** | Submit data / Create resource | ✅ Yes | ❌ No | ❌ No |
| **PUT** | Replace entire resource | ✅ Yes | ✅ Yes | ❌ No |
| **PATCH** | Partial update | ✅ Yes | ❌ No | ❌ No |
| **DELETE** | Remove resource | ❌ Usually no | ✅ Yes | ❌ No |
| **HEAD** | GET without body | ❌ No | ✅ Yes | ✅ Yes |
| **OPTIONS** | Ask what methods are allowed | ❌ No | ✅ Yes | ✅ Yes |

### Key Terms Explained

**Idempotent**: Making the same request N times has the same effect as making it once.
- GET /users/5 → always returns user 5
- DELETE /users/5 → user 5 is gone, calling again still results in "gone"
- POST /users → creates new user EACH time (not idempotent)

**Safe**: Request doesn't modify server state.
- GET just reads
- POST creates/modifies

### Method Deep Dives

#### GET — Retrieve Data

```http
GET /api/users?status=active HTTP/1.1
Host: api.example.com
Accept: application/json
```

**Rules:**
- No request body (data goes in URL as query parameters)
- Should never modify server state
- Response should be cacheable
- Can be bookmarked/shared

#### POST — Create or Submit

```http
POST /api/users HTTP/1.1
Host: api.example.com
Content-Type: application/json
Content-Length: 42

{"name": "Bob", "email": "bob@example.com"}
```

**Rules:**
- Has request body
- Creates new resources
- NOT idempotent (each POST might create a new resource)
- Can't be bookmarked (no URL represents the action)

#### PUT — Replace Entirely

```http
PUT /api/users/42 HTTP/1.1
Host: api.example.com
Content-Type: application/json

{"id": 42, "name": "Robert", "email": "robert@example.com"}
```

**Rules:**
- Replaces the ENTIRE resource
- If you omit a field, it's removed
- Idempotent: same PUT = same result

#### PATCH — Partial Update

```http
PATCH /api/users/42 HTTP/1.1
Host: api.example.com
Content-Type: application/json

{"name": "Bobby"}
```

**Rules:**
- Updates ONLY specified fields
- Other fields remain unchanged
- Preferred for most updates in practice

#### DELETE — Remove Resource

```http
DELETE /api/users/42 HTTP/1.1
Host: api.example.com
Authorization: Bearer admin-token
```

**Rules:**
- Removes the resource
- Idempotent: deleting twice = resource still gone
- Usually no body (nothing to send)

---

# Part 2: HTTP Status Codes

The server's response begins with a **status code** — a 3-digit number indicating what happened.

## Status Code Categories

| Range | Category | Meaning |
|-------|----------|---------|
| **1xx** | Informational | Request received, continuing process |
| **2xx** | Success | Request received, understood, accepted |
| **3xx** | Redirection | Further action needed to complete request |
| **4xx** | Client Error | Request contains bad syntax or cannot be fulfilled |
| **5xx** | Server Error | Server failed to fulfill valid request |

## Essential Status Codes

### 2xx Success

| Code | Name | When To Use |
|------|------|-------------|
| **200** | OK | General success, response has body |
| **201** | Created | Resource created (POST success) |
| **204** | No Content | Success, but no body (DELETE success) |

### 3xx Redirection

| Code | Name | When To Use |
|------|------|-------------|
| **301** | Moved Permanently | Resource has new URL forever |
| **302** | Found (Temporary) | Resource temporarily at different URL |
| **304** | Not Modified | Cached version is still valid |

### 4xx Client Errors

| Code | Name | When To Use |
|------|------|-------------|
| **400** | Bad Request | Malformed request syntax |
| **401** | Unauthorized | Authentication required |
| **403** | Forbidden | Authenticated but not authorized |
| **404** | Not Found | Resource doesn't exist |
| **405** | Method Not Allowed | Wrong HTTP method |
| **409** | Conflict | Request conflicts with server state |
| **422** | Unprocessable Entity | Validation errors |
| **429** | Too Many Requests | Rate limit exceeded |

### 5xx Server Errors

| Code | Name | When To Use |
|------|------|-------------|
| **500** | Internal Server Error | Generic server crash |
| **502** | Bad Gateway | Upstream server gave bad response |
| **503** | Service Unavailable | Server overloaded or down for maintenance |
| **504** | Gateway Timeout | Upstream server didn't respond in time |

### 401 vs 403 — The Confusion

| Code | Meaning | Example |
|------|---------|---------|
| **401** | "Who are you?" | No token provided, or token invalid |
| **403** | "I know who you are, but no." | Valid token, but user lacks permission |

---

# Part 3: HTTP Headers

Headers are **key-value pairs** providing metadata about the request or response.

## Request Headers

| Header | Purpose | Example |
|--------|---------|---------|
| `Host` | Target server (required in HTTP/1.1) | `Host: api.example.com` |
| `Content-Type` | Format of request body | `Content-Type: application/json` |
| `Content-Length` | Size of body in bytes | `Content-Length: 42` |
| `Accept` | What response formats client accepts | `Accept: application/json` |
| `Authorization` | Authentication credentials | `Authorization: Bearer abc123` |
| `User-Agent` | Client software description | `User-Agent: curl/7.68.0` |
| `Cookie` | Session data from previous responses | `Cookie: session=xyz` |
| `Cache-Control` | Caching instructions | `Cache-Control: no-cache` |

## Response Headers

| Header | Purpose | Example |
|--------|---------|---------|
| `Content-Type` | Format of response body | `Content-Type: application/json` |
| `Content-Length` | Size of body | `Content-Length: 1234` |
| `Location` | URL for redirects or new resources | `Location: /users/42` |
| `Set-Cookie` | Store cookie on client | `Set-Cookie: session=xyz; HttpOnly` |
| `Cache-Control` | How clients should cache | `Cache-Control: max-age=3600` |
| `WWW-Authenticate` | How to authenticate (with 401) | `WWW-Authenticate: Bearer` |

## Content-Type Values (MIME Types)

| MIME Type | Format | Use Case |
|-----------|--------|----------|
| `application/json` | JSON | APIs |
| `application/x-www-form-urlencoded` | Form data | HTML form submissions |
| `multipart/form-data` | Mixed (files + data) | File uploads |
| `text/html` | HTML | Web pages |
| `text/plain` | Plain text | Simple text responses |
| `application/xml` | XML | Legacy systems |

---

# Part 4: curl — The Command-Line HTTP Client

`curl` (Client URL) is the most universal tool for making HTTP requests from the command line.

## Basic Syntax

```bash
curl [options] URL
```

## Essential Options Reference

| Option | Long Form | Purpose |
|--------|-----------|---------|
| `-X` | `--request` | HTTP method |
| `-H` | `--header` | Add header |
| `-d` | `--data` | Request body |
| `-i` | `--include` | Show response headers |
| `-v` | `--verbose` | Show full request/response |
| `-o` | `--output` | Save to file |
| `-s` | `--silent` | Suppress progress bar |
| `-L` | `--location` | Follow redirects |
| `-u` | `--user` | Username:password |
| `-k` | `--insecure` | Skip TLS verification |

## Practical Examples

### GET Request (Basic)

```powershell
# Simplest request
curl http://httpbin.org/get

# With headers shown
curl -i http://httpbin.org/get

# Verbose (shows everything)
curl -v http://httpbin.org/get
```

### GET with Query Parameters

```powershell
# URL encoding happens automatically if you quote the URL
curl "http://api.example.com/search?q=hello+world&limit=10"

# Or use --data-urlencode for complex values
curl -G http://api.example.com/search --data-urlencode "q=hello world"
```

### GET with Custom Headers

```powershell
curl http://api.example.com/data ^
    -H "Accept: application/json" ^
    -H "Authorization: Bearer your-token-here"
```

### POST with JSON Body

```powershell
curl -X POST http://127.0.0.1:5000/acceptjson ^
    -H "Content-Type: application/json" ^
    -d "{\"name\": \"Mike\", \"age\": 30}"
```

**Line-by-line explanation:**

| Part | Purpose |
|------|---------|
| `curl` | The command |
| `-X POST` | Use POST method |
| `http://127.0.0.1:5000/acceptjson` | URL to request |
| `-H "Content-Type: application/json"` | Tell server we're sending JSON |
| `-d "{...}"` | The JSON body |

### POST with Form Data

```powershell
curl -X POST http://example.com/login ^
    -d "username=mike&password=secret"
```

This sends `Content-Type: application/x-www-form-urlencoded` automatically.

### POST with File Upload

```powershell
curl -X POST http://example.com/upload ^
    -F "file=@C:\path\to\document.pdf" ^
    -F "description=My file"
```

`-F` (form) sends `multipart/form-data` and `@` reads file contents.

### PUT (Replace Resource)

```powershell
curl -X PUT http://api.example.com/users/42 ^
    -H "Content-Type: application/json" ^
    -d "{\"name\": \"Updated Name\", \"email\": \"new@email.com\"}"
```

### PATCH (Partial Update)

```powershell
curl -X PATCH http://api.example.com/users/42 ^
    -H "Content-Type: application/json" ^
    -d "{\"name\": \"Just the name\"}"
```

### DELETE

```powershell
curl -X DELETE http://api.example.com/users/42 ^
    -H "Authorization: Bearer admin-token"
```

### Authentication Examples

```powershell
# Basic auth (username:password)
curl -u username:password http://api.example.com/private

# Bearer token
curl -H "Authorization: Bearer eyJhbGciOiJI..." http://api.example.com/private

# API key in header
curl -H "X-API-Key: your-api-key" http://api.example.com/data
```

### Follow Redirects

```powershell
# Without -L: stops at redirect
curl http://example.com/old-page
# Returns: 301 Moved Permanently

# With -L: follows redirect
curl -L http://example.com/old-page
# Returns: actual content from new location
```

### Save Output to File

```powershell
# Save response body
curl -o output.json http://api.example.com/data

# Save with remote filename
curl -O http://example.com/file.zip
```

### Reading the Verbose Output

```powershell
curl -v http://httpbin.org/get
```

Output explained:
```
* Trying 34.236.82.78:80...              ← Connecting to IP
* Connected to httpbin.org               ← TCP connection established
> GET /get HTTP/1.1                       ← Request line WE sent
> Host: httpbin.org                       ← Request headers WE sent
> User-Agent: curl/7.68.0                 ← (> = outgoing)
> Accept: */*
>                                         ← Blank line (end of headers)
< HTTP/1.1 200 OK                         ← Response status (< = incoming)
< Content-Type: application/json          ← Response headers
< Content-Length: 256
<                                         ← Blank line
{                                         ← Response body
  "args": {},
  ...
}
```

---

# Part 5: Other HTTP Tools

## PowerShell: Invoke-RestMethod

Windows' built-in alternative to curl:

```powershell
# GET request
Invoke-RestMethod -Uri "http://api.example.com/data"

# POST with JSON
$body = @{name="Mike"; age=30} | ConvertTo-Json
Invoke-RestMethod -Uri "http://127.0.0.1:5000/acceptjson" `
    -Method POST `
    -ContentType "application/json" `
    -Body $body
```

## httpie (pip install httpie)

More human-friendly than curl:

```bash
# GET
http httpbin.org/get

# POST JSON (automatic Content-Type)
http POST httpbin.org/post name=Mike age:=30

# Headers
http httpbin.org/headers Authorization:"Bearer token"
```

## Python requests Library

```python
import requests

# GET
response = requests.get("http://httpbin.org/get")
print(response.json())

# POST
response = requests.post(
    "http://httpbin.org/post",
    json={"name": "Mike", "age": 30}
)
print(response.json())
```

## Browser DevTools

Press F12 → Network tab to see all HTTP requests your browser makes.

---

# Part 6: Testing Your Flask Routes

Based on your current Flask app, here's how to test:

## Your Current Routes

```python
# Route 1: GET/POST form
@app.route("/form", methods=["GET", "POST"])
def form_page():
    ...

# Route 2: JSON endpoint
@app.route("/acceptjson")
def acceptjson():
    api_input = request.get_json()
    return {"api_input": api_input}
```

## Testing Commands

### Test /acceptjson (GET with JSON)

```powershell
curl http://127.0.0.1:5000/acceptjson ^
    -H "Content-Type: application/json" ^
    -d "{\"message\": \"hello\", \"count\": 5}"
```

Expected response:
```json
{"api_input": {"message": "hello", "count": 5}}
```

### Test /form (GET)

```powershell
curl http://127.0.0.1:5000/form
```

Expected: HTML form

### Test /form (POST)

```powershell
curl -X POST http://127.0.0.1:5000/form ^
    -d "user_input=Hello+World"
```

Expected: "Hello World POSTed"

---

# Part 7: Common Issues and Debugging

## Issue: "Connection Refused"

```
curl: (7) Failed to connect to 127.0.0.1 port 5000: Connection refused
```

**Causes:**
- Flask server not running
- Wrong port
- Firewall blocking

**Fix:** Make sure `flask run` is active in another terminal.

## Issue: get_json() Returns None

**Causes:**
1. Missing `Content-Type: application/json` header
2. Invalid JSON syntax
3. Wrong HTTP method

**Debug:** Add verbose output:
```powershell
curl -v http://127.0.0.1:5000/acceptjson ^
    -H "Content-Type: application/json" ^
    -d "{\"test\": 1}"
```

## Issue: 405 Method Not Allowed

**Cause:** Route doesn't accept the HTTP method you're using.

**Fix:** Add method to route:
```python
@app.route("/acceptjson", methods=["GET", "POST"])
```

## Issue: JSON Escaping in PowerShell

PowerShell requires escaping quotes:
```powershell
# This fails:
-d "{"name": "Mike"}"

# This works:
-d "{\"name\": \"Mike\"}"
```

Or use single quotes (if available):
```bash
# In bash/WSL:
-d '{"name": "Mike"}'
```

---

# Summary: Quick Reference

## HTTP Request Structure
```
METHOD /path HTTP/1.1
Header: Value

Body
```

## Common Methods
| Method | Purpose | Body? |
|--------|---------|-------|
| GET | Read | No |
| POST | Create | Yes |
| PUT | Replace | Yes |
| DELETE | Remove | No |

## Common Status Codes
| Code | Meaning |
|------|---------|
| 200 | OK |
| 201 | Created |
| 400 | Bad Request |
| 401 | Auth Required |
| 404 | Not Found |
| 500 | Server Error |

## curl Cheat Sheet
```powershell
# GET
curl http://localhost:5000/endpoint

# POST JSON
curl -X POST http://localhost:5000/endpoint ^
    -H "Content-Type: application/json" ^
    -d "{\"key\": \"value\"}"

# With auth
curl -H "Authorization: Bearer TOKEN" http://example.com/api

# Verbose
curl -v http://example.com

# Follow redirects
curl -L http://example.com
```

Now go test your `/acceptjson` route! 🚀
