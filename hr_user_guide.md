# HR Administrator User Guide — AEC Group HR Super App

Welcome to the **AEC Group HR Super App**. This guide provides step-by-step instructions for HR Administrators to manage candidate onboarding, staff verification, leave tracking, payroll generation, expense verification, and task delegation.

---

## 1. Dashboard Overview & Navigation
When you log in as an `HR` user, your workspace is organized into actionable module cards. E.g.:

```
[Login] -> [Main Dashboard] -> Select Module Card (Onboarding / Payroll / Reimbursement / Tasks / Mail / Notifications)
```

### Module Cards on HR Dashboard:
- **Onboarding Card**: Invite new candidates and verify submitted onboarding profiles.
- **Notifications Card**: View announcement boards and publish company-wide updates.
- **Reimbursement Card**: Review staff expense claims and verify submitted bills.
- **Task Management Card**: Assign tasks to staff and monitor department-wise progress.
- **Mail Card**: Check internal HR correspondence and candidate offer acceptances.
- **Payroll Card**: Review salary structures, late deductions, and monthly payroll slips.

---

## 2. Step-by-Step Core Workflows

### 2.1 Candidate Onboarding & Verification
Use this workflow to onboard new hires securely without creating manual accounts.

```
[Dashboard] -> Click 'Onboarding' Card -> Enter Email in 'Invite Candidate' -> [Candidate Submits Data] -> HR Inbox -> Click 'Verify'
```

1. Go to the **Onboarding Center** from the dashboard.
2. In the **Invite Candidate** card, input the applicant's email address and select their target department. Click **Send Invitation**.
3. Once the candidate completes their profile, an alert appears in your **HR Mailbox**.
4. Review their uploaded documents and click **Verify**. The system automatically creates their permanent `EmployeeProfile` and user credentials.

---

## 2.2 Reimbursement Verification Workflow
All staff expense claims must pass HR verification before being forwarded to the Managing Director.

```
[Dashboard] -> Click 'Reimbursement' Card -> View Department-Wise Table -> Review Bill Upload -> Click 'Verify' (Status -> HR_VERIFIED)
```

1. Open the **Reimbursement Center**.
2. Claims are categorized by department. Locate pending claims marked with status `PENDING`.
3. Click the **View Bill** link to inspect the uploaded invoice/receipt.
4. If valid, click **Verify**. The status changes to `HR_VERIFIED` and automatically appears on the MD's approval dashboard.

---

## 2.3 Task Assignment & Delegation
Delegate operational tasks to employees across any business unit.

```
[Dashboard] -> Click 'Task Management' Card -> Search Staff in Dropdown -> Enter Details -> Click 'Assign Task' -> Monitor Progress Report
```

1. Open the **Task Management** hub.
2. Scroll to the **Assign Task** card.
3. Start typing an employee's name in the **Assign To Employee** autocomplete box. Select the correct staff member from the filtered suggestions.
4. Enter the task title, detailed instructions, and due date. Click **Confirm & Assign Task**.
5. Track their progress (`PENDING`, `IN_PROGRESS`, `COMPLETED`) in real-time under the **Department-Wise Staff Tasks Report**.

---

## 2.4 Publishing Company Announcements
Broadcast official news, policy updates, and holiday notices across the organization.

```
[Dashboard] -> Click 'Notifications' Card -> Click 'Publish New Announcement' -> Enter Title & Message -> Click 'Post'
```

1. Open the **Notifications Center**.
2. Click the expandable accordion titled **Publish a New Announcement**.
3. Fill in the headline and message body. Click **Post Announcement**.
4. All staff members instantly receive an unread badge notification on their navigation bar.
