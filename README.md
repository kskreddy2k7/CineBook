# CineBook — Indian Movie Ticket Booking System
### Advanced Programming Practice | Python Tkinter & SQLite3 Desktop Application

![Python](https://img.shields.io/badge/Python-3.10%2B-blue?logo=python)
![GUI Framework](https://img.shields.io/badge/GUI-Tkinter%20%2F%20ttk-purple)
![Database](https://img.shields.io/badge/Database-SQLite3%20ACID-success)
![Posters](https://img.shields.io/badge/Posters-20%20Authentic%20Theatrical-red)
![Tests](https://img.shields.io/badge/Tests-28%20Passed-brightgreen)

**CineBook Pro** is a production-grade desktop movie ticket reservation application built in **Python Tkinter/ttk** and **SQLite3**, featuring an authentic **Indian Cinema catalogue** across Telugu, Tamil, Hindi, Malayalam, and Kannada industries. The interface is inspired by **BookMyShow**'s clean light-grey design (`#F2F4F8`), signature coral-red (`#F84464`) accents, large portrait theatrical posters, multi-city theatre scheduling, and a spacious Rows A–L seating matrix with interactive zoom controls and bottom screen indicator.

---

## 🎬 1. Authentic Indian Movie Posters & Catalogue

- **20 Verified Indian Blockbusters**:
  - **Telugu Cinema**: *RRR*, *Baahubali 2: The Conclusion*, *Pushpa 2: The Rule*, *Kalki 2898 AD*, *Hanu-Man*
  - **Tamil Cinema**: *Leo: Bloody Sweet*, *Vikram: Hitlist*, *Jailer*, *Ponniyin Selvan: Part 1*
  - **Hindi / Bollywood**: *Jawan*, *12th Fail*, *Dangal*, *Stree 2: Sarkate Ka Aatank*
  - **Malayalam Cinema**: *Manjummel Boys*, *Aavesham*, *Lucifer*
  - **Kannada Cinema**: *K.G.F: Chapter 2*, *Kantara: A Legend*, *777 Charlie*, *Kantara: Chapter 1 (Prequel)*
- **Authentic Theatrical Posters**:
  - Saved locally in `assets/posters/*.jpg`.
  - Stored with structured provenance in [`assets/posters/posters_manifest.json`](file:///c:/Users/Kskre/Desktop/TIKENTER/assets/posters/posters_manifest.json).
  - Scaled cleanly preserving portrait ~2:3 aspect ratio via Pillow `ImageOps.fit()` with Lanczos resampling.
  - In-memory `_POSTER_CACHE` avoids repetitive disk I/O and ensures stutter-free carousel scrolling.
  - Clearly labeled `[🎬 POSTER UNAVAILABLE / Theatrical Artwork Pending]` state for unreleased or missing artwork without synthetic AI art.
- **Complete Booking for Every Movie**:
  - Every movie card supports complete end-to-end booking from selecting the movie to generating a digital ticket.
  - If any movie has no configured showtimes in a selected city, an empty-state card offers an instant **"⚡ Add Demonstration Showtimes for this Movie"** button that dynamically generates realistic multi-screen schedules on demand.

---

## 🏙️ 2. Multi-City, Theatre, Screen & Showtime Hierarchy

CineBook implements the complete 7-level booking hierarchy:

$$\text{City} \longrightarrow \text{Demonstration Theatre} \longrightarrow \text{Auditorium Screen} \longrightarrow \text{Movie} \longrightarrow \text{Date} \longrightarrow \text{Showtime} \longrightarrow \text{Seats}$$

- **5 Major Indian Hubs**: Chennai, Hyderabad, Bengaluru, Mumbai, Kochi.
- **15 Sample Demonstration Theatres**: 3 per city (e.g. *CineBook Demo Cinemas*, *Palazzo Cineplex*, *PVR Heritage*).
- **45 Auditorium Formats**: 3 formats per theatre (*IMAX Laser 3D*, *Dolby Atmos 4K*, *Luxe Lounge*).
- **Date Selector**: Browse today, tomorrow, and upcoming calendar dates.
- **Multi-Screen Format Selector**: Displays theatre location, distance, format badges, and live pricing.

---

## 💺 3. Spacious Theatre Seat Selection (Rows A–L)

- **Auditorium Grid**:
  - 12 Rows labeled **A through L** down the left.
  - Small numbered seat buttons (1 to 8).
  - Separate left block (1–4) and right block (5–8) with central walking aisle.
  - Section category labels and prices above each section:
    - **Recliner (Rows A–B)**: `RECLINER - Rs. 300.00`
    - **Elite (Rows C–F)**: `ELITE - Rs. 220.00`
    - **Normal (Rows G–L)**: `NORMAL - Rs. 150.00`
  - Cinema screen indicator at the **bottom**: `CurvedScreenWidget` with arc curved towards the audience and `• ALL EYES THIS WAY PLEASE (SCREEN) •`.
  - Zoom controls at top right: `[🔍+ In]`, `[🔍- Out]`, `[↺ Reset]`.
  - Fixed status legend: **Available** (White), **Selected** (Emerald Green `#10B981`), **Sold** (Disabled Grey), **★ Bestseller** (Amber Border `#F59E0B`), and category pricing badges.
- **Interactive Seat Behavior**:
  - Click available seat to select (turns emerald green `#10B981`).
  - Click selected seat to deselect.
  - Booked seats disabled with hatch pattern.
  - Bestseller seats highlighted with amber outline and star badge.
  - Configurable maximum seat limit (6 tickets per transaction) with friendly warning.
  - Real-time itemized pricing: Subtotal + ₹25 convenience fee = Grand Total in ₹.
  - Revalidation and selection reset when switching showtimes.

---

## 🔒 4. Database & Atomic Double-Booking Protection

- SQLite3 relational engine with strict foreign keys (`PRAGMA foreign_keys = ON;`).
- Atomic transactions (`with conn:`):
  1. Validates customer contact details.
  2. Re-checks live seat availability immediately before writing.
  3. Executes `UPDATE show_seats SET status='BOOKED' ... WHERE status='AVAILABLE'`.
  4. Automatically rolls back on any conflict, raising `SeatUnavailableError`.
- **Cancellation**: Restores seats to `AVAILABLE` without deleting historical booking records.

---

## 🎟️ 5. Customer Checkout & Digital Boarding Pass Ticket

- Validation: 10-digit Indian mobile number (`^[6-9]\d{9}$`), customer name ($\ge 2$ characters), and optional email.
- Boarding-pass cinema ticket with unique reference (`CB-2026-XXXXX`), cinema screen format, customer details, and itemized receipt.
- One-click export to local formatted **HTML** (`exports/*.html`) and **Plain Text** (`exports/*.txt`).

---

## ⚙️ 6. Demo Administration & Operations Console

- Accessible via the top navbar (`⚙ Demo Admin`).
- Platform metric counters (Movies, Cities, Theatres, Screens, Shows).
- Interactive Treeview hierarchy of sample cities and theatres.
- Active show ticket price adjuster (`Classic`, `Elite`, `Recliner`).

---

## 🏗️ 7. System Architecture & File Structure

```
TIKENTER/
├── main.py                     # Main application entry point & view coordinator
├── database.py                 # SQLite relational schema, CRUD, & ACID transactions
├── models.py                   # Dataclass entities (City, Theatre, Screen, Movie, Show, Seat, Booking)
├── fetch_authentic_posters.py  # Ingestion tool for 20 authentic Indian theatrical posters
├── run_tests.py                # Comprehensive automated test suite runner
├── requirements.txt            # Python dependencies (Pillow)
├── README.md                   # Full documentation & setup guide
├── VIVA_PREPARATION.md         # Complete viva script & 25 Q&A cheat sheet
├── assets/
│   ├── posters/                # 20 Authentic theatrical posters (.jpg)
│   │   └── posters_manifest.json # Image manifest (provenance, URLs, dimensions)
│   └── promos/                 # Widescreen cinema promotional banner
├── data/
│   └── cinebook.db             # Relational SQLite database
├── exports/                    # Saved HTML and plain-text ticket receipts
├── tests/
│   ├── test_booking_logic.py   # Unit & concurrency transaction tests (10 tests)
│   ├── test_gui_headless.py    # Headless GUI component tests (6 tests)
│   └── test_redesign_verification.py # Redesign & poster tests (9 tests)
└── ui/
    ├── theme.py                # Design tokens (BookMyShow light theme, colors, fonts)
    ├── components.py           # PosterWidget, MovieCardWidget, CurvedScreen, SeatWidget
    ├── home_view.py            # Movie discovery carousel, filters & promo banner
    ├── movie_view.py           # City selector, theatre grouping & showtime picker
    ├── seat_view.py            # Rows A-L seating grid, zoom controls & live summary
    ├── checkout_view.py        # Customer details validation & atomic checkout
    ├── ticket_view.py          # Boarding pass ticket & file export
    ├── bookings_view.py        # My Bookings history table & cancellation
    └── admin_view.py           # Operations console & live tier price adjuster
```

---

## 🚀 8. Installation & Launch Instructions

### Prerequisites
- Python 3.10 or higher.
- Standard libraries (`sqlite3`, `tkinter`, `urllib`, `json`, `pathlib`, `unittest`) are included with Python.

### Setup Steps
1. Open terminal in the project directory:
   ```bash
   cd c:\Users\Kskre\Desktop\TIKENTER
   ```
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Run CineBook:
   ```bash
   python main.py
   ```

---

## 🧪 9. Running Automated Tests

Run all 28 automated unit, GUI integration, and verification tests:
```bash
python run_tests.py
```

Expected output:
```text
===========================================================================
 CINEBOOK — COMPREHENSIVE AUTOMATED TEST SUITE RUNNER
===========================================================================

[RUNNING SUITE] Database & Booking Logic (tests/test_booking_logic.py)...
---------------------------------------------------------------------------
--> [PASSED] Database & Booking Logic

[RUNNING SUITE] Headless GUI Integration (tests/test_gui_headless.py)...
---------------------------------------------------------------------------
--> [PASSED] Headless GUI Integration

[RUNNING SUITE] Redesign & Poster Verification (tests/test_redesign_verification.py)...
---------------------------------------------------------------------------
--> [PASSED] Redesign & Poster Verification

===========================================================================
 FINAL STATUS: ALL 3 TEST SUITES PASSED (28/28 TESTS SUCCESSFUL)
===========================================================================
```

---

## 🎓 10. Viva Voce & Demonstration Aid

For college laboratory examinations, refer to [`VIVA_PREPARATION.md`](file:///c:/Users/Kskre/Desktop/TIKENTER/VIVA_PREPARATION.md) for the complete viva presentation script, demonstration walkthrough, and technical Q&A covering Tkinter widgets, SQLite ACID transactions, Pillow image scaling, and concurrency protection.
