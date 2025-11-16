# Challenge Host Management

A clear and beginner-friendly guide explaining how to add, remove, and manage Challenge Hosts on EvalAI using both the Web UI and the REST API.

This document is intended for contributors, challenge creators, and challenge organizers.

---

## 1. Overview

**Challenge Hosts** are users with elevated permissions for a specific challenge.

They can:

- Create, edit, and delete challenges  
- Upload challenge configuration files  
- Manage submissions and leaderboard  
- Add or remove participant teams  
- Add or remove other hosts  

A challenge may have multiple hosts with full access unless restricted by an Admin.

---

## 2. Adding a Challenge Host (Web UI)

- Sign in to your EvalAI instance  
- Navigate to **My Challenges**  
- Select the challenge you want to manage  
- Open the left sidebar and click **Challenge Hosts**  
- Click **Add Host**  
- Enter the user's email and press **Enter**  
- Click **Add**

If the user already exists, they are added immediately.  
If not, an invitation email is sent to them.

---

## 3. Removing a Challenge Host (Web UI)

- Log in and go to **My Challenges**  
- Select the challenge  
- Open **Challenge Hosts** in the sidebar  
- Locate the host you want to remove  
- Click **Remove**  
- Confirm the action  

The host will be removed instantly.

---

## 4. API Usage (Programmatic Host Management)

Requirements:

- Your API Token (Profile → API Tokens)  
- Base URL (example: `https://eval.ai`)  
- `curl` installed  
- Replace `<challenge_id>`, `<host_id>`, and `<your_token>` with real values  

### 5. Add a Challenge Host (API)

```bash
curl -X POST "https://eval.ai/api/challenges/<challenge_id>/hosts/add/" \
  -H "Authorization: Token <your_token>" \
  -H "Content-Type: application/json" \
  -d '{
        "email": "newhost@example.com"
      }'
```

Expected response:

200 OK

### 6. Remove a Challenge Host (API)

```bash
curl -X DELETE "https://eval.ai/api/challenges/<challenge_id>/hosts/remove/<host_id>/" \
  -H "Authorization: Token <your_token>"
``` 

Expected response:

204 No Content

## 7. Roles and Permissions
### Challenge Host

    Full access to challenge configuration

    Can add or remove other hosts

    Can manage submissions and participant teams

### Admin

    Full system-wide privileges

    Can override actions taken by hosts

### Participant

    Cannot add or remove hosts

    Limited to participating in challenges

## 8. Troubleshooting
### 8.1 “Host already exists”

The user is already a host for that challenge.
### 8.2 “User does not exist”

In self-hosted setups, SMTP/email configuration may be incorrect.
### 8.3 API: 401 Unauthorized

Your authentication token is missing or invalid.
### 8.4 API: 403 Forbidden

You do not have permission to perform this action.
### 8.5 API: 404 Not Found

Challenge ID or host ID is incorrect.
## 9. Recommended Tests (For Contributors)

    Add a sample host email to a test challenge

    Verify it appears in the host list

    Remove the host and confirm it disappears

## 10. Related Documentation

    Hosting Guide

    API Reference (Challenge Endpoints)

    Participant Team Management


