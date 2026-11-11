#!/usr/bin/env python3
"""
Seed demo jobs into a Rivet account.
Run this from the Render shell: python scripts/seed_demo_jobs.py
"""

import os, sys
from datetime import datetime, timedelta, timezone
from supabase import create_client

OWNER_EMAIL = "jonathanlapinsky1@gmail.com"

JOBS = [
    {
        "title": "Deck staining and sealing",
        "description": "Need my back deck stained and sealed before winter. It's a wood deck, pretty weathered. Some boards may need replacing.",
        "customer_name": "Mike Harrington", "email": "mharrington@email.com", "phone": "555-234-7890",
        "address": "142 Birchwood Ave, Austin, TX 78701", "location": "Austin, TX",
        "op_status": "needs_review", "recommendation": "review", "confidence": 52,
        "price": 680, "profit": 310, "costs": 370, "hours": "5–8 hrs", "hours_num": 6.5,
        "rate": "$48/hr", "rate_num": 48, "travel": "8 mi",
        "preferred_date": (datetime.now(timezone.utc) + timedelta(days=5)).date().isoformat(),
        "cost_breakdown": [{"label": "Materials", "value": "$180"}, {"label": "Travel", "value": "$22"}],
        "reasons": ["Deck dimensions not provided", "Board replacement scope unknown"],
        "scope_analysis": {"readyToQuote": False, "questions": [
            "What are the approximate dimensions of the deck (length x width in feet)?",
            "How many boards appear to need replacement?",
            "Has the deck been stained before, or is this the first time?",
        ], "context": "Need dimensions and board condition before pricing."},
    },
    {
        "title": "Bathroom vanity and faucet replacement",
        "description": "Replace a 36-inch bathroom vanity with new vanity I already purchased. Also replace the faucet. Single bathroom, standard hookup.",
        "customer_name": "Sandra Okonkwo", "email": "s.okonkwo@gmail.com", "phone": "555-801-3344",
        "address": "78 Maplewood Dr, Austin, TX 78702", "location": "Austin, TX",
        "op_status": "needs_review", "recommendation": "take", "confidence": 87,
        "price": 420, "profit": 285, "costs": 135, "hours": "2–4 hrs", "hours_num": 3.0,
        "rate": "$95/hr", "rate_num": 95, "travel": "4 mi",
        "preferred_date": (datetime.now(timezone.utc) + timedelta(days=3)).date().isoformat(),
        "cost_breakdown": [{"label": "Materials", "value": "$40"}, {"label": "Travel", "value": "$11"}],
        "reasons": ["Clean scope", "Materials supplied by customer", "High contribution margin"],
        "scope_analysis": {"readyToQuote": True, "questions": [], "context": "Customer supplying vanity. Standard install, shutoff valves accessible. Ready to quote."},
    },
    {
        "title": "Drywall patch and paint — living room wall",
        "description": "Large hole in living room drywall from moving furniture. About 12x12 inches. Needs patching, mudding, sanding, and paint matched to existing wall.",
        "customer_name": "Amy Chen", "email": "amychen22@gmail.com", "phone": "555-782-3391",
        "address": "56 Willowbrook Ct, Austin, TX 78731", "location": "Austin, TX",
        "op_status": "needs_review", "recommendation": "take_at_price", "confidence": 70,
        "price": 280, "profit": 155, "costs": 125, "hours": "2–4 hrs", "hours_num": 3.0,
        "rate": "$52/hr", "rate_num": 52, "travel": "7 mi",
        "preferred_date": (datetime.now(timezone.utc) + timedelta(days=6)).date().isoformat(),
        "cost_breakdown": [{"label": "Materials", "value": "$85"}, {"label": "Travel", "value": "$20"}],
        "reasons": ["Paint matching adds time", "Acceptable margin at this price", "Consider $320 for better hourly"],
    },
    {
        "title": "Wood fence repair — 3 damaged sections",
        "description": "Three sections of my wood privacy fence blew down in a storm. Posts are still in ground, just need new pickets and rails. About 30 feet total.",
        "customer_name": "Carlos Rivera", "email": "crivera@outlook.com", "phone": "555-412-9900",
        "address": "905 Elm Street, Austin, TX 78704", "location": "Austin, TX",
        "op_status": "quoted", "recommendation": "take", "confidence": 91,
        "price": 580, "profit": 340, "costs": 240, "hours": "4–6 hrs", "hours_num": 5.0,
        "rate": "$68/hr", "rate_num": 68, "travel": "6 mi",
        "preferred_date": (datetime.now(timezone.utc) + timedelta(days=7)).date().isoformat(),
        "cost_breakdown": [{"label": "Materials", "value": "$190"}, {"label": "Travel", "value": "$17"}],
        "reasons": ["Clear scope", "Good margin", "Efficient job"],
        "contractor_notes": "Quoted 11/8. Customer said they'd get back to me by end of week.",
    },
    {
        "title": "Kitchen backsplash tile installation",
        "description": "Install subway tile backsplash in kitchen. About 40 sq ft behind stove and sink. I have all the tile, grout, and supplies already.",
        "customer_name": "Priya Nair", "email": "priya.nair@gmail.com", "phone": "555-677-2211",
        "address": "1203 Riverside Blvd, Austin, TX 78703", "location": "Austin, TX",
        "op_status": "quoted", "recommendation": "take", "confidence": 83,
        "price": 750, "profit": 520, "costs": 230, "hours": "5–8 hrs", "hours_num": 6.5,
        "rate": "$80/hr", "rate_num": 80, "travel": "5 mi",
        "preferred_date": (datetime.now(timezone.utc) + timedelta(days=10)).date().isoformat(),
        "cost_breakdown": [{"label": "Materials", "value": "$180"}, {"label": "Travel", "value": "$14"}],
        "reasons": ["All materials supplied", "High value job", "Strong margin"],
        "contractor_notes": "Sent estimate 11/9. Customer is comparing quotes.",
    },
    {
        "title": "Ceiling fan installation — 3 rooms",
        "description": "Install 3 ceiling fans in bedrooms. Existing light fixtures are there, just swapping to fans. Customer has the fans.",
        "customer_name": "Robert Nguyen", "email": "rnguyen@workmail.com", "phone": "555-543-8872",
        "address": "7 Sage Meadow Dr, Austin, TX 78749", "location": "Austin, TX",
        "op_status": "quoted", "recommendation": "take", "confidence": 89,
        "price": 390, "profit": 300, "costs": 90, "hours": "2–4 hrs", "hours_num": 3.0,
        "rate": "$100/hr", "rate_num": 100, "travel": "11 mi",
        "preferred_date": (datetime.now(timezone.utc) + timedelta(days=12)).date().isoformat(),
        "cost_breakdown": [{"label": "Materials", "value": "$50"}, {"label": "Travel", "value": "$30"}],
        "reasons": ["Fans supplied by customer", "Straightforward swap", "Top hourly rate"],
        "contractor_notes": "Quoted 11/4. No response yet. Need to follow up.",
        "created_at": (datetime.now(timezone.utc) - timedelta(days=7)).isoformat(),
    },
    {
        "title": "TV mounting and cable management",
        "description": "Mount 65-inch TV above fireplace. Need cables run through wall to hide them. Already have the wall mount.",
        "customer_name": "Derek Thompson", "email": "d.thompson@gmail.com", "phone": "555-903-5544",
        "address": "334 Oak Lane, Austin, TX 78745", "location": "Austin, TX",
        "op_status": "approved", "recommendation": "take", "confidence": 94,
        "price": 320, "profit": 235, "costs": 85, "hours": "2–3 hrs", "hours_num": 2.5,
        "rate": "$94/hr", "rate_num": 94, "travel": "9 mi",
        "preferred_date": (datetime.now(timezone.utc) + timedelta(days=2)).date().isoformat(),
        "cost_breakdown": [{"label": "Materials", "value": "$45"}, {"label": "Travel", "value": "$25"}],
        "reasons": ["Simple scope", "Mount provided", "High hourly rate"],
        "contractor_notes": "Derek confirmed Friday morning works. Need to bring stud finder and drywall anchors.",
    },
    {
        "title": "Exterior door installation — front entry",
        "description": "Replace front entry door. Customer has new door already. Old door needs to be removed, new pre-hung door installed, weather stripping and caulking included.",
        "customer_name": "Janet Kowalski", "email": "jkowalski@email.com", "phone": "555-234-0012",
        "address": "2401 Pecan Grove Rd, Austin, TX 78758", "location": "Austin, TX",
        "op_status": "approved", "recommendation": "take_at_price", "confidence": 78,
        "price": 890, "profit": 480, "costs": 410, "hours": "4–7 hrs", "hours_num": 5.5,
        "rate": "$87/hr", "rate_num": 87, "travel": "12 mi",
        "preferred_date": (datetime.now(timezone.utc) + timedelta(days=4)).date().isoformat(),
        "cost_breakdown": [{"label": "Materials", "value": "$320"}, {"label": "Travel", "value": "$33"}],
        "reasons": ["Door supplied by customer", "Moderate complexity", "Good profit"],
        "contractor_notes": "Janet approved via email 11/10. Flexible on timing.",
    },
    {
        "title": "Garbage disposal replacement",
        "description": "Old disposal seized up, needs full replacement. Standard under-sink hookup.",
        "customer_name": "Lisa Patel", "email": "lpatel@gmail.com", "phone": "555-291-6634",
        "address": "1890 Creek Bend Ln, Austin, TX 78726", "location": "Austin, TX",
        "op_status": "completed", "recommendation": "take", "confidence": 95,
        "price": 245, "profit": 160, "costs": 85, "hours": "1–2 hrs", "hours_num": 1.5,
        "rate": "$107/hr", "rate_num": 107, "travel": "14 mi",
        "preferred_date": (datetime.now(timezone.utc) - timedelta(days=5)).date().isoformat(),
        "cost_breakdown": [{"label": "Materials", "value": "$50"}, {"label": "Travel", "value": "$39"}],
        "reasons": ["Quick job", "High hourly", "Materials cost low"],
        "contractor_notes": "Completed 11/6. Easy job, customer was happy.",
        "created_at": (datetime.now(timezone.utc) - timedelta(days=10)).isoformat(),
    },
    {
        "title": "Hang 4 picture frames",
        "description": "Need 4 picture frames hung in hallway. Mix of small and medium sizes.",
        "customer_name": "Tom Bradley", "email": "tombradley@email.com", "phone": "555-120-9988",
        "address": "420 Lakeview Pkwy, Austin, TX 78732", "location": "Austin, TX",
        "op_status": "declined", "recommendation": "pass", "confidence": 97,
        "price": 95, "profit": 30, "costs": 65, "hours": "1–1 hrs", "hours_num": 1.0,
        "rate": "$30/hr", "rate_num": 30, "travel": "16 mi",
        "preferred_date": (datetime.now(timezone.utc) - timedelta(days=2)).date().isoformat(),
        "cost_breakdown": [{"label": "Materials", "value": "$10"}, {"label": "Travel", "value": "$44"}],
        "reasons": ["Below minimum job value", "Travel cost eats margin"],
        "contractor_notes": "Passed — not worth the trip.",
        "created_at": (datetime.now(timezone.utc) - timedelta(days=4)).isoformat(),
    },
]


def main():
    url = os.environ["SUPABASE_URL"]
    key = os.environ["SUPABASE_SERVICE_KEY"]
    supabase = create_client(url, key)

    # Find user by email
    result = supabase.auth.admin.list_users()
    user = next((u for u in result if u.email == OWNER_EMAIL), None)
    if not user:
        print(f"No user found with email {OWNER_EMAIL}")
        sys.exit(1)

    # Find their business
    res = supabase.table("businesses").select("id, name").eq("owner_user_id", user.id).single().execute()
    if not res.data:
        print(f"No business found for user {OWNER_EMAIL}")
        sys.exit(1)

    business_id = res.data["id"]
    business_name = res.data["name"]
    print(f"Found business: {business_name} ({business_id})\n")

    # Wipe existing demo jobs (by known demo emails)
    demo_emails = [j["email"] for j in JOBS]
    supabase.table("work_items").delete().eq("business_id", business_id).in_("email", demo_emails).execute()
    print("Cleared old demo jobs.\n")

    # Insert fresh
    for job in JOBS:
        row = {"business_id": business_id, "source": "customer_request",
               "customer_type": "individual", "billing_status": "not_invoiced",
               "service_type": "Handyman", **job}
        res = supabase.table("work_items").insert(row).execute()
        status = job["op_status"]
        title = job["title"]
        price = job["price"]
        print(f"  [{status:12}]  {title[:50]:50}  ${price}")

    print(f"\nDone. Seeded {len(JOBS)} demo jobs.")


main()
