# Settings Guide

Reference for every configurable setting. Use this to explain settings to contractors and to decide what to update.

---

## Goals & Capacity

### weeklyGoal
**What it is:** The dollar amount of contribution profit the contractor wants to earn each week.

**How Rivet uses it:** This number drives the "Still needed this week" metric on the Home screen and the weekly capacity pace floor in the decision engine. When the contractor is behind on their goal, Rivet raises the minimum send price on jobs to close the gap faster.

**How to explain it:** "Your weekly goal is what you're trying to earn this week. When you're behind, Rivet starts quoting a bit higher to make up the difference. If you feel like prices have been too high lately, your goal might be set higher than your actual target."

**Typical range:** $1,500 to $5,000 per week depending on crew size.

**Key:** `weeklyGoal` (number, dollars)

---

### weeklyHours
**What it is:** How many hours the contractor normally works per week.

**How Rivet uses it:** Sets the total capacity. Jobs are measured in capacity hours (labor + travel + procurement). When committed hours approach this number, Rivet gets more selective — it will Pass on low-margin jobs and raise prices to protect remaining time.

**How to explain it:** "This is your total available time each week. Rivet uses it to know when you're running out of room. If you keep seeing Pass on jobs late in the week, check whether your hours are set right."

**Key:** `weeklyHours` (number, hours)

---

## Pricing & Costs

### minimumHourlyRate
**What it is:** The minimum contribution profit Rivet requires per hands-on labor hour.

**How Rivet uses it:** One of the pricing floors. If a job's profit-per-labor-hour falls below this, it triggers a Pass or a higher send price to meet the floor.

**How to explain it:** "This is the least you want to earn per hour of actual work. It's not your charge-out rate — it's the floor for what lands in your pocket per hour. Set it too low and you'll take jobs that eat your time without paying enough."

**Key:** `minimumHourlyRate` (number, dollars per hour)

---

### minimumPrice
**What it is:** The smallest job the contractor will take, regardless of anything else.

**How Rivet uses it:** A hard floor. No job will be quoted below this number.

**How to explain it:** "Some jobs aren't worth leaving the house for. This setting is the minimum ticket size. Any job that would quote below this automatically gets bumped up or passed."

**Key:** `minimumPrice` (number, dollars)

---

### helperRate
**What it is:** What the contractor pays per hour when they bring in help.

**How Rivet uses it:** Included in the direct cost calculation when a job requires a helper. Affects the margin and profit floors.

**How to explain it:** "If you use a helper on a job, Rivet adds their cost to figure out what the job actually cost you. Set this to what you actually pay them — not what you charge the customer."

**Key:** `helperRate` (number, dollars per hour)

---

### mileageRate
**What it is:** Cost per mile driven to and from jobs.

**How Rivet uses it:** Travel cost is computed as roundtrip miles × this rate and added to the job's direct costs.

**How to explain it:** "Driving costs money. This rate covers fuel, wear, and vehicle cost per mile. The IRS standard rate is a reasonable starting point but you can set it to whatever reflects your actual costs."

**Key:** `mileageRate` (number, dollars per mile — e.g. 0.70 for 70 cents)

---

### materialMarkup
**What it is:** The percentage added to material costs before they hit the customer's price.

**How Rivet uses it:** Applied to all material estimates. Covers your time to source materials, supplier markup, and waste.

**How to explain it:** "When Rivet estimates materials, it marks them up by this percentage before adding them to the customer's price. 20% is common. If you're often eating material costs, raise it."

**Key:** `materialMarkup` (number, percent — e.g. 20 for 20%)

---

## Advanced Engine

### minimumMargin
**What it is:** The minimum gross margin percentage Rivet requires on a job.

**How Rivet uses it:** One of the pricing floors. If the margin on a job would fall below this, Rivet raises the price or passes.

**How to explain it:** "Margin is the percentage of revenue that isn't covering direct costs. If your margin is too thin, one surprise on a job wipes out your profit. This setting is the floor below which Rivet won't go."

**Typical range:** 40% to 65% depending on the trade and market.

**Key:** `minimumMargin` (number, percent — e.g. 55 for 55%)

---

### minimumJobProfit
**What it is:** The minimum absolute dollar profit required per job, regardless of margin.

**How Rivet uses it:** Works alongside margin as a floor. A very cheap job might clear the margin percentage but still not be worth the hassle. This catches that case.

**How to explain it:** "Even if the margin looks fine on paper, some jobs just don't generate enough cash to be worth it. This sets the minimum dollar profit per job. If a job won't put at least this much in your pocket, Rivet flags it."

**Key:** `minimumJobProfit` (number, dollars)

---

### dailyCapacityLimit
**What it is:** Maximum number of jobs the contractor wants to run in a single day.

**How Rivet uses it:** Prevents the schedule from getting overloaded. Once the limit is reached, additional jobs for that day get flagged.

**How to explain it:** "Even if the hours add up, there's a practical limit to how many jobs you can coordinate in a day. This sets that ceiling."

**Key:** `dailyCapacityLimit` (number, jobs per day)

---

## Business Profile

### businessName
Business display name used in emails and the client portal.
**Key:** `businessName` (string)

### phone
Business phone number shown on quote emails and customer-facing pages.
**Key:** `phone` (string)

### email
Business contact email for customer replies.
**Key:** `email` (string)

### homeBaseAddress
Starting location used to calculate travel distance and cost to job sites.
**Key:** `homeBaseAddress` (string — full address)

---

## Service Area

Service area is managed separately from business settings. Use `get_service_area` and `update_service_area` for these.

### mode
**What it is:** How the service area is defined — either a mile radius around a center ZIP or a manually curated list of ZIP codes.

**How Rivet uses it:** When a customer submits a quote request, their ZIP is checked against this config. If they are outside the service area, the form shows an out-of-area message and blocks submission.

**How to explain it:** "Radius mode is the easiest — set your base ZIP and how far out you'll travel and Rivet handles the rest. ZIP list mode is for contractors who only cover specific corridors or municipalities."

**Values:** `'radius'` or `'zip-list'`
**Key:** `mode`

---

### centerZip
**What it is:** The ZIP code at the center of your service radius. Usually your shop, home base, or main dispatch location.

**How Rivet uses it:** Distance from this ZIP is calculated for every customer ZIP in radius mode. Required when mode is `'radius'`.

**How to explain it:** "This is where you're based. Every customer ZIP gets checked against how far it is from here."

**Key:** `centerZip` (string — five-digit ZIP)

---

### radiusMiles
**What it is:** How many miles out from your center ZIP you will travel for jobs.

**How Rivet uses it:** Customer ZIPs whose centroid falls beyond this distance are rejected with the out-of-area message.

**How to explain it:** "Set this to the realistic max you'll drive one-way. If you won't do jobs more than 45 miles out, set it to 45."

**Typical range:** 15–75 miles depending on market density.
**Key:** `radiusMiles` (number, miles)

---

### serviceableZips
**What it is:** The list of ZIP codes you actively service (ZIP list mode only).

**How Rivet uses it:** Customers in ZIPs on this list can submit requests. Everyone else gets the out-of-area message.

**How to explain it:** "In ZIP list mode, only customers in these ZIPs can book. Radius mode replaces this with the automatic circle."

**Key:** `serviceableZips` (array of ZIP strings) — use `addServiceableZips` / `removeServiceableZips` in `update_service_area`

---

### excludedZips
**What it is:** ZIPs that are permanently blocked, even if they fall inside the radius or serviceable list.

**How Rivet uses it:** A hard block. Use for areas that are logistically impractical — a ZIP technically in range but across a river or in traffic-heavy territory.

**How to explain it:** "Even if a ZIP is inside your radius, you can exclude it completely. Customers there get rejected no matter what."

**Key:** `excludedZips` (array) — use `addExcludedZips` / `removeExcludedZips`

---

### unavailableZips
**What it is:** ZIPs that are temporarily paused. Customers see "we're not currently servicing your area — check back soon" instead of a flat rejection.

**How Rivet uses it:** A softer block. Good for seasonal coverage gaps or areas where you're temporarily at capacity.

**How to explain it:** "Use unavailable instead of excluded when you plan to come back to that area. The message customers see is friendlier."

**Key:** `unavailableZips` (array) — use `addUnavailableZips` / `removeUnavailableZips`
