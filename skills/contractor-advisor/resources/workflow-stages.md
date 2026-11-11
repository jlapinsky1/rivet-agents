# Workflow Stages

Each work item has an `op_status` field indicating where it is in the contractor's pipeline. Use this to give accurate context and suggest the right next action.

## needs_review

The job came in but has not been evaluated yet. The contractor or the AI scope analysis may have flagged missing info.

**What it means:** This job has not been quoted. It needs attention.

**Next actions:**
- If the job has scope questions (`scope_analysis.questions` is non-empty), suggest emailing the customer to get answers before quoting.
- If the job looks ready (`scope_analysis.readyToQuote` is true), suggest sending the estimate.
- If there is no scope analysis, suggest reviewing the job details.

## quoted

The estimate has been sent to the customer. Waiting on their response.

**What it means:** The ball is in the customer's court.

**Next actions:**
- If it has been more than a few days with no response, suggest following up.
- Otherwise, nothing urgent.

## approved

The customer accepted the estimate. The contractor has committed to the job.

**What it means:** This job is happening. It needs to get scheduled.

**Next actions:**
- Suggest scheduling the job.
- This is high priority, especially if the contractor needs revenue this week.

## scheduled

The job has a confirmed date.

**What it means:** Logistics are set.

**Next actions:**
- Confirm any final details with the customer if needed.
- Nothing urgent unless the date is imminent.

## in_progress

The job is currently being done.

**What it means:** Contractor is on-site or the job is active.

**Next actions:**
- Flag if it has been in this state for an unusually long time.

## completed

The job is done.

**What it means:** Work finished. Billing should follow.

**Next actions:**
- Check billing status. If not invoiced, suggest sending the invoice.

## declined

The contractor passed on this job.

**What it means:** No action needed.

**Next actions:**
- None. Do not surface declined jobs unless specifically asked.
