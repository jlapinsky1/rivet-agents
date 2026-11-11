# Priority Signals

When ranking what the contractor should work on, use these signals in order of importance.

## 1. Estimates approved but not yet sent (highest urgency)

A job in `needs_review` with `recommendation: take` or `take_at_price` and no scope questions means money is sitting on the table. These should always come first.

## 2. Approved jobs not yet scheduled

Customer said yes. These generate revenue once scheduled. Surface them before jobs still awaiting customer response.

## 3. Weekly revenue gap

If the contractor has a weekly goal and has not hit it yet, prioritize jobs that close the gap. A $1,200 job matters more on a week where the contractor is $900 short of their target.

## 4. Days since submitted with no action

A job sitting in `needs_review` for 3+ days with no note, no scope analysis, and no email to the customer is a risk. Customers move on. Flag these.

## 5. AI recommendation score

The system has assessed each job:
- `take` = strong margin, clear scope, worth doing
- `take_at_price` = viable at the quoted price, do not discount
- `review` = unclear scope or tight margin, needs more info
- `pass` = not worth it at current pricing

Jobs rated `take` should come before `review` unless other signals override.

## 6. Customer communication pending

If the customer asked a question (visible in `customer_notes` or `scope_analysis.questions`), that job is blocked until someone responds. Flag it and offer to email the customer.

## 7. Quotes expiring soon

If a quote was sent but not accepted and the expiry is approaching, suggest following up.

## Deprioritize

- Jobs in `declined` or `completed` are closed. Do not surface them unless asked.
- Jobs with `pass` recommendation and no special context. Only bring them up if the contractor explicitly asks.
