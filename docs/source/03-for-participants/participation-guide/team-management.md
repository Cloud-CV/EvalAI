# Team Management (Participants)

This guide explains, in a complete and beginner-friendly way, how to **create participant teams**, **add members**, and **remove members** on EvalAI using both the **Web UI** and the **REST API**.

It is written step-by-step, with clear instructions for new users as well as contributors.

---

## 1. Overview

Participant teams on EvalAI allow multiple users to collaborate and submit entries to a challenge.  
Using this guide, you will learn:

- How to create a participant team  
- How to add members using the UI and API  
- How to remove members  
- How permissions work  
- Common troubleshooting tips

This documentation applies to most EvalAI instances (public or self-hosted).

---

## 2. Creating a Participant Team (Web UI)

Follow these exact steps:

1. Open your EvalAI instance (example: `https://eval.ai`).
2. Click **Sign In** and log in with your account.
3. Go to **Challenges** from the top navigation bar.
4. Select the challenge you want to participate in.
5. On the challenge sidebar, click **Participant Teams**.  
   - If you are on a small screen, expand the left sidebar using the menu icon (☰).
6. Click the **Create Team** (or **Add Team**) button.
7. A dialog box appears:
   - In **Team Name**, type your preferred team name (example: `my-team-123`).
   - In **Add Member**, type the email of a team member → press **Enter** to add.
   - Repeat for additional emails.
8. Click **Create**.

Your participant team is now created.  
Users with existing EvalAI accounts are added immediately; others receive an invitation email.

---

## 3. Adding Members to an Existing Team (Web UI)

1. Go to **Challenges** → open the challenge.
2. Click **Participant Teams** in the sidebar.
3. Click on the **team name** you want to edit.
4. Click **Add Member**.
5. Enter the member’s email → press **Enter** → click **Add**.
6. The user should now appear in the team member list.

---

## 4. Removing Members from a Team (Web UI)

1. Go to **Challenges** → open the challenge → **Participant Teams**.
2. Click your **team name**.
3. In the members list, find the person to remove.
4. Click **Remove** (or open the ⋯ menu → **Remove**).
5. Confirm removal in the popup.

The member will disappear from the list immediately.

---

## 5. API Usage (Programmatic Team Management)

EvalAI provides REST API endpoints you can use to automate team management.  
You need:

- Your **API token** from Profile → API Tokens  
- Your instance base URL (example: `https://eval.ai`)  
- `curl` installed locally

> Replace `<your_token>`, `<team_id>`, `<member_id>` with real values.

### 5.1 Create a Team
```bash
curl -X POST "https://eval.ai/api/participants/team/" \
  -H "Authorization: Token <your_token>" \
  -H "Content-Type: application/json" \
  -d '{
        "team_name": "my-team",
        "members": "["alice@example.com", "bob@example.com"]"
      }'
```

Response contains fields like id (team ID), which you will use later.
### 5.2 Add a Member to a Team

```bash
curl -X POST "https://eval.ai/api/participants/team/<team_id>/members/" \
  -H "Authorization: Token <your_token>" \
  -H "Content-Type: application/json" \
  -d '{"email":"newmember@example.com"}'

```

### 5.3 Remove a Member

curl -X DELETE "https://eval.ai/api/participants/team/<team_id>/members/<member_id>/" \
  -H "Authorization: Token <your_token>"

A successful removal returns 204 No Content or 200 OK.
## 6. Permissions and Roles

    Team Owner / Creator — can add/remove members and edit team information.

    Team Member — cannot remove others or change team settings.

    Challenge Host — may have permissions to manage participant teams depending on challenge configuration.

    Admin — full control over all teams.

If you do not see the Add/Remove buttons, you likely lack permissions.
## 7. How to Get Your API Token

    Log in to EvalAI.

    Click your profile picture/name (top-right).

    Select Profile or Settings.

    Scroll to API Tokens.

    Copy your token and keep it safe.

Use it like this in API calls:

-H "Authorization: Token <your_token>"

## 8. Troubleshooting
### 8.1 “Participant Teams” option missing

    You may be on the wrong page.

    Sidebar may be collapsed.

    Challenge may not permit team submissions.

### 8.2 Invite email not received

    Check spam folder.

    Ensure the email typed is correct.

    For self-hosted instances, SMTP may be misconfigured.

### 8.3 API: 401 Unauthorized

    Token is missing or invalid.

### 8.4 API: 403 Forbidden

    You do not have sufficient permissions.

### 8.5 API: 404 Not Found

    The team ID or member ID is incorrect.

    The API path may differ on some deployments.

## 9. Recommended Tests (For New Users)

    Create a test team named test-team-<yourname>.

    Add a test email you own.

    Remove it to confirm removal works.

    Test API endpoints using a dummy team.

## 10. Related Documentation

    Participation Guide

    API Reference → Users & Teams endpoints

    Challenge Hosting Guide


---