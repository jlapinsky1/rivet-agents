#!/usr/bin/env python3
"""
Seed demo work items for a Rivet account.

Inserts realistic jobs across all pipeline stages so you can demo
the AI and the UI without needing real customer requests.

Usage:
    python scripts/seed_demo_jobs.py --business-id <your_business_id>

To find your business_id: open the Rivet admin, open browser DevTools ->
Network tab, make any API call and look for businessId in the request body.
Or run:  python scripts/seed_demo_jobs.py --find-email jonathanlapinsky1@gmail.com

Requires environment variables: SUPABASE_URL, SUPABASE_SERVICE_KEY
(copy from your Render service env vars)
"""

import argparse
import os
import sys
from datetime import datetime, timedelta, timezone

try:
    from supabase import create_client
except ImportError:
    print("Run: pip install supabase")
    sys.exit(1)


# ── Demo jobs ──────────────────────────────────────────────────────────────────
# Each dict maps to work_items columns. Covers every op_status stage.

JOBS = [
    # 1. needs_review — missing info, good for demoing scope analysis
    {
        "title": "Deck staining and sealing",
        "description": "Need my back deck stained and sealed before winter. It's a wood deck, pretty weathered. Some boards may need replacing.",
        "customer_name": "Mike Harrington",
        "email": "mharrington@email.com",
        "phone": "555-234-7890",
        "address": "142 Birchwood Ave, Austin, TX 78701",
        "location": "Austin, TX",
        "op_status": "needs_review",
        "recommendation": "review",
        "confidence": 52,
        "price": 680,
        "profit": 310,
        "costs": 370,
        "hours": "5–8 hrs",
        "hours_num": 6.5,
        "rate": "$48/hr",
        "rate_num": 48,
        "travel": "8 mi",
        "preferred_date": (datetime.now(timezone.utc) + timedelta(days=5)).date().isoformat(),
        "cost_breakdown": [
            {"label": "Materials", "value": "$180"},
            {"label": "Travel", "value": "$22"},
        ],
        "reasons": ["Deck dimensions not provided", "Board replacement scope unknown"],
        "scope_analysis": {
            "readyToQuote": False,
            "questions": [
                "What are the approximate dimensions of the deck (length x width in feet)?",
                "How many boards appear to need replacement?",
                "Has the deck been stained before, or is this the first time?",
            ],
            "context": "Deck staining cost depends heavily on square footage and board condition. Need dimensions and board count before pricing.",
        },
    },

    # 2. needs_review — all info present, ready to quote
    {
        "title": "Bathroom vanity and faucet replacement",
        "description": "Replace a 36-inch bathroom vanity with new vanity I already purchased. Also replace the faucet. Single bathroom, standard hookup.",
        "customer_name": "Sandra Okonkwo",
        "email": "s.okonkwo@gmail.com",
        "phone": "555-801-3344",
        "address": "78 Maplewood Dr, Austin, TX 78702",
        "location": "Austin, TX",
        "op_status": "needs_review",
        "recommendation": "take",
        "confidence": 87,
        "price": 420,
        "profit": 285,
        "costs": 135,
        "hours": "2–4 hrs",
        "hours_num": 3.0,
        "rate": "$95/hr",
        "rate_num": 95,
        "travel": "4 mi",
        "preferred_date": (datetime.now(timezone.utc) + timedelta(days=3)).date().isoformat(),
        "cost_breakdown": [
            {"label": "Materials", "value": "$40"},
            {"label": "Travel", "value": "$11"},
        ],
        "reasons": ["Clean scope", "Materials supplied by customer", "High contribution margin"],
        "scope_analysis": {
            "readyToQuote": True,
            "questions": [],
            "context": "Customer is supplying the vanity. Standard installation with shutoff valves accessible. Ready to quote.",
        },
    },

    # 3. quoted — estimate sent, waiting on customer
    {
        "title": "Wood fence repair — 3 damaged sections",
        "description": "Three sections of my wood privacy fence blew down in a storm. Posts are still in ground, just need new pickets and rails. About 30 feet total.",
        "customer_name": "Carlos Rivera",
        "email": "crivera@outlook.com",
        "phone": "555-412-9900",
        "address": "905 Elm Street, Austin, TX 78704",
        "location": "Austin, TX",
        "op_status": "quoted",
        "recommendation": "take",
        "confidence": 91,
        "price": 580,
        "profit": 340,
        "costs": 240,
        "hours": "4–6 hrs",
        "hours_num": 5.0,
        "rate": "$68/hr",
        "rate_num": 68,
        "travel": "6 mi",
        "preferred_date": (datetime.now(timezone.utc) + timedelta(days=7)).date().isoformat(),
        "cost_breakdown": [
            {"label": "Materials", "value": "$190"},
            {"label": "Travel", "value": "$17"},
        ],
        "reasons": ["Clear scope from customer description", "Good margin", "Efficient job"],
        "contractor_notes": "Quoted 11/8. Customer said they'd get back to me by end of week.",
    },

    # 4. quoted — sent recently, higher value job
    {
        "title": "Kitchen backsplash tile installation",
        "description": "Install subway tile backsplash in kitchen. About 40 sq ft behind stove and sink. I have all the tile, grout, and supplies already.",
        "customer_name": "Priya Nair",
        "email": "priya.nair@gmail.com",
        "phone": "555-677-2211",
        "address": "1203 Riverside Blvd, Austin, TX 78703",
        "location": "Austin, TX",
        "op_status": "quoted",
        "recommendation": "take",
        "confidence": 83,
        "price": 750,
        "profit": 520,
        "costs": 230,
        "hours": "5–8 hrs",
        "hours_num": 6.5,
        "rate": "$80/hr",
        "rate_num": 80,
        "travel": "5 mi",
        "preferred_date": (datetime.now(timezone.utc) + timedelta(days=10)).date().isoformat(),
        "cost_breakdown": [
            {"label": "Materials", "value": "$180"},
            {"label": "Travel", "value": "$14"},
        ],
        "reasons": ["All materials supplied", "High value job", "Strong margin"],
        "contractor_notes": "Sent estimate 11/9. Customer is comparing quotes.",
    },

    # 5. approved — customer accepted, ready to schedule (highest priority)
    {
        "title": "TV mounting and cable management",
        "description": "Mount 65-inch TV above fireplace. Need cables run through wall to hide them. Already have the wall mount.",
        "customer_name": "Derek Thompson",
        "email": "d.thompson@gmail.com",
        "phone": "555-903-5544",
        "address": "334 Oak Lane, Austin, TX 78745",
        "location": "Austin, TX",
        "op_status": "approved",
        "recommendation": "take",
        "confidence": 94,
        "price": 320,
        "profit": 235,
        "costs": 85,
        "hours": "2–3 hrs",
        "hours_num": 2.5,
        "rate": "$94/hr",
        "rate_num": 94,
        "travel": "9 mi",
        "preferred_date": (datetime.now(timezone.utc) + timedelta(days=2)).date().isoformat(),
        "cost_breakdown": [
            {"label": "Materials", "value": "$45"},
            {"label": "Travel", "value": "$25"},
        ],
        "reasons": ["Simple scope", "Mount provided", "High hourly rate"],
        "contractor_notes": "Derek confirmed Friday morning works. Need to bring stud finder and drywall anchors.",
    },

    # 6. approved — higher value, ready to schedule
    {
        "title": "Exterior door installation — front entry",
        "description": "Replace front entry door. Customer has new door already. Old door needs to be removed, new pre-hung door installed, weather stripping and caulking included.",
        "customer_name": "Janet Kowalski",
        "email": "jkowalski@email.com",
        "phone": "555-234-0012",
        "address": "2401 Pecan Grove Rd, Austin, TX 78758",
        "location": "Austin, TX",
        "op_status": "approved",
        "recommendation": "take_at_price",
        "confidence": 78,
        "price": 890,
        "profit": 480,
        "costs": 410,
        "hours": "4–7 hrs",
        "hours_num": 5.5,
        "rate": "$87/hr",
        "rate_num": 87,
        "travel": "12 mi",
        "preferred_date": (datetime.now(timezone.utc) + timedelta(days=4)).date().isoformat(),
        "cost_breakdown": [
            {"label": "Materials", "value": "$320"},
            {"label": "Travel", "value": "$33"},
        ],
        "reasons": ["Door supplied by customer", "Moderate complexity — shimming required", "Good profit"],
        "contractor_notes": "Janet approved via email 11/10. She's flexible on timing this week.",
    },

    # 7. needs_review — take_at_price recommendation, price needs adjustment
    {
        "title": "Drywall patch and paint — living room wall",
        "description": "Large hole in living room drywall from moving furniture. About 12x12 inches. Needs patching, mudding, sanding, and paint matched to existing wall.",
        "customer_name": "Amy Chen",
        "email": "amychen22@gmail.com",
        "phone": "555-782-3391",
        "address": "56 Willowbrook Ct, Austin, TX 78731",
        "location": "Austin, TX",
        "op_status": "needs_review",
        "recommendation": "take_at_price",
        "confidence": 70,
        "price": 280,
        "profit": 155,
        "costs": 125,
        "hours": "2–4 hrs",
        "hours_num": 3.0,
        "rate": "$52/hr",
        "rate_num": 52,
        "travel": "7 mi",
        "preferred_date": (datetime.now(timezone.utc) + timedelta(days=6)).date().isoformat(),
        "cost_breakdown": [
            {"label": "Materials", "value": "$85"},
            {"label": "Travel", "value": "$20"},
        ],
        "reasons": ["Paint matching adds time", "Acceptable margin at this price", "Consider $320 for better hourly"],
    },

    # 8. quoted — older quote, follow-up needed
    {
        "title": "Ceiling fan installation — 3 rooms",
        "description": "Install 3 ceiling fans in bedrooms. Existing light fixtures are there, just swapping to fans. Customer has the fans.",
        "customer_name": "Robert Nguyen",
        "email": "rnguyen@workmail.com",
        "phone": "555-543-8872",
        "address": "7 Sage Meadow Dr, Austin, TX 78749",
        "location": "Austin, TX",
        "op_status": "quoted",
        "recommendation": "take",
        "confidence": 89,
        "price": 390,
        "profit": 300,
        "costs": 90,
        "hours": "2–4 hrs",
        "hours_num": 3.0,
        "rate": "$100/hr",
        "rate_num": 100,
        "travel": "11 mi",
        "preferred_date": (datetime.now(timezone.utc) + timedelta(days=12)).date().isoformat(),
        "cost_breakdown": [
            {"label": "Materials", "value": "$50"},
            {"label": "Travel", "value": "$30"},
        ],
        "reasons": ["Fans supplied by customer", "Straightforward swap", "Top hourly rate"],
        "contractor_notes": "Quoted 11/4. No response yet. Need to follow up.",
        "created_days_ago": 7,
    },

    # 9. completed — reference job
    {
        "title": "Garbage disposal replacement",
        "description": "Old disposal seized up, needs full replacement. Standard under-sink hookup.",
        "customer_name": "Lisa Patel",
        "email": "lpatel@gmail.com",
        "phone": "555-291-6634",
        "address": "1890 Creek Bend Ln, Austin, TX 78726",
        "location": "Austin, TX",
        "op_status": "completed",
        "recommendation": "take",
        "confidence": 95,
        "price": 245,
        "profit": 160,
        "costs": 85,
        "hours": "1–2 hrs",
        "hours_num": 1.5,
        "rate": "$107/hr",
        "rate_num": 107,
        "travel": "14 mi",
        "preferred_date": (datetime.now(timezone.utc) - timedelta(days=5)).date().isoformat(),
        "cost_breakdown": [
            {"label": "Materials", "value": "$50"},
            {"label": "Travel", "value": "$39"},
        ],
        "reasons": ["Quick job", "High hourly", "Materials cost low"],
        "contractor_notes": "Completed 11/6. Easy job, customer was happy.",
        "created_days_ago": 10,
    },

    # 10. declined — not worth it
    {
        "title": "Hang 4 picture frames",
        "description": "Need 4 picture frames hung in hallway. Mix of small and medium sizes.",
        "customer_name": "Tom Bradley",
        "email": "tombradley@email.com",
        "phone": "555-120-9988",
        "address": "420 Lakeview Pkwy, Austin, TX 78732",
        "location": "Austin, TX",
        "op_status": "declined",
        "recommendation": "pass",
        "confidence": 97,
        "price": 95,
        "profit": 30,
        "costs": 65,
        "hours": "1–1 hrs",
        "hours_num": 1.0,
        "rate": "$30/hr",
        "rate_num": 30,
        "travel": "16 mi",
        "preferred_date": (datetime.now(timezone.utc) - timedelta(days=2)).date().isoformat(),
        "cost_breakdown": [
            {"label": "Materials", "value": "$10"},
            {"label": "Travel", "value": "$44"},
        ],
        "reasons": ["Below minimum job value", "Travel cost eats margin", "Not worth dispatching"],
        "contractor_notes": "Passed — not worth the trip.",
        "created_days_ago": 4,
    },
]


def find_business_id_by_email(supabase, email: str) -> str | None:
    """Look up business_id by owner email via auth.users + businesses table."""
    # Try businesses table directly first (some schemas store owner_email)
    res = supabase.table('businesses').select('id, owner_email').execute()
    if res.data:
        for b in res.data:
            if b.get('owner_email', '').lower() == email.lower():
                return b['id']

    print(f"Could not find business with owner_email={email}.")
    print("Try passing --business-id directly.")
    return None


def insert_jobs(supabase, business_id: str):
    inserted = 0
    for job in JOBS:
        days_ago = job.pop("created_days_ago", 0)
        created_at = (datetime.now(timezone.utc) - timedelta(days=days_ago)).isoformat()

        row = {
            "business_id": business_id,
            "source": "customer_request",
            "customer_type": "individual",
            "billing_status": "not_invoiced",
            "service_type": "Handyman",
            "created_at": created_at,
            **{k: v for k, v in job.items()},
        }

        res = supabase.table("work_items").insert(row).execute()
        if res.data:
            item = res.data[0]
            print(f"  [{job['op_status']:12}]  {job['title'][:55]}  (id={item['id']})")
            inserted += 1
        else:
            print(f"  ERROR inserting: {job['title']}")

    return inserted


def main():
    parser = argparse.ArgumentParser(description="Seed demo jobs into a Rivet account")
    parser.add_argument("--business-id", help="Business ID to seed jobs under")
    parser.add_argument("--find-email", help="Look up business ID by owner email")
    parser.add_argument("--clear", action="store_true", help="Delete existing demo jobs first (by customer email match)")
    args = parser.parse_args()

    url = os.environ.get("SUPABASE_URL")
    key = os.environ.get("SUPABASE_SERVICE_KEY")
    if not url or not key:
        print("Set SUPABASE_URL and SUPABASE_SERVICE_KEY environment variables.")
        sys.exit(1)

    supabase = create_client(url, key)

    # Resolve business ID
    business_id = args.business_id
    if not business_id and args.find_email:
        business_id = find_business_id_by_email(supabase, args.find_email)
    if not business_id:
        parser.print_help()
        sys.exit(1)

    print(f"\nSeeding demo jobs for business_id: {business_id}\n")

    if args.clear:
        demo_emails = [j["email"] for j in JOBS]
        for email in demo_emails:
            supabase.table("work_items").delete().eq("business_id", business_id).eq("email", email).execute()
        print(f"Cleared existing demo jobs.\n")

    count = insert_jobs(supabase, business_id)
    print(f"\nDone. Inserted {count} demo jobs.")


if __name__ == "__main__":
    main()
