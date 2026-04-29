## ORCA PH Dashboard Specs

Purpose:
ORCA PH = command dashboard for Prestige Holidays
Tracks builder → quote → UT execution → margin → guest journey

# 1. Main Dashboard Sections
ORCA PH DASHBOARD
├── Executive Overview
├── Builder Sessions
├── Quote & Pricing Monitor
├── UT RFP / Vendor Bidding
├── Activity Revenue-Pulse
├── Journey Operations
├── Margin Control
├── SHADOW Audit Feed
└── Alerts / Risk Center

# 2. Executive Overview
Show:
- Today Revenue
- Active Builder Sessions
- Quotes Created
- Quotes Sealed
- Bookings Confirmed
- UT Jobs Pending
- Average PH Margin
- Top Selling Activity

# 3. Builder Sessions Panel
Tracks user behavior:
- Session ID, Guest Count, Budget, Blocks, Current Step, Status.

# 4. Quote & Pricing Monitor
- Quote Ref, Price, Net Cost, Margin %, Mutable/Sealed, Expiry.

# 5. UT RFP / Vendor Bidding Panel
- RFP ID, Activity/Transfer, Vendor Bids, Selected Vendor, PH Margin, Status.

# 6. Activity Revenue-Pulse
- Activity, Views, Selections, Bookings, Conversion %, Margin.

# 7. Journey Operations View
- Timeline per guest (Arrival, Snorkeling, etc.)

# 8. Margin Control Center
- Breakdown: Sell Price, Hotel Cost, Activity Cost, UT Cost, Vendor Cost, PH Margin, Commission, Tax, Final Profit.

# 9. SHADOW Audit Feed
- Truth events: PH_QUOTE_SEALED, PH_BOOKING_CONFIRMED, PH_UT_RFP_AWARDED, etc.

# 10. Alerts / Risk Center
- Severity: P1 (Guest journey), P2 (Margin/Vendor), P3 (Sales optimization).

# 11. Dashboard User Roles
- CEO / Admin (Everything)
- Finance (Pricing/Margin/Tax)
- Sales Agent (Quotes/Bookings)
- Operations (Journeys/UT)
- Marketing (Revenue-Pulse)
