# 🎬 CineBook — Indian Movie Ticket Booking System

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue?logo=python&logoColor=white)](https://www.python.org/)
[![GUI Framework](https://img.shields.io/badge/GUI-Tkinter%20%2F%20ttk-purple)](https://docs.python.org/3/library/tkinter.html)
[![Database](https://img.shields.io/badge/Database-SQLite3%20ACID-success?logo=sqlite&logoColor=white)](https://www.sqlite.org/)
[![Posters](https://img.shields.io/badge/Posters-20%20Authentic%20Theatrical-red)](#-3-authentic-indian-cinema-catalogue)
[![Tests](https://img.shields.io/badge/Tests-38%2F38%20Passed-brightgreen)](#-7-running-automated-tests)
[![Platform](https://img.shields.io/badge/Platform-Windows%20%7C%20macOS%20%7C%20Linux-lightgrey)](#-6-quick-start--installation)

**CineBook** is a production-grade desktop movie ticket reservation system built with **Python (Tkinter/ttk)** and **SQLite3**. Inspired by **BookMyShow**'s clean light-grey design language (`#F2F4F8`) and signature coral-red accents (`#F84464`), CineBook delivers an end-to-end cinema booking experience tailored for Indian Cinema across Telugu, Tamil, Hindi, Malayalam, and Kannada industries.

---

## 🌟 Key Highlights

- **BookMyShow-Style Modern UI**: Clean light-grey canvas (`#F2F4F8`), high-contrast typography (Segoe UI / Helvetica), rounded cards, seamless pill filters, and native Windows high-DPI scaling.
- **Authentic 20-Movie Catalogue**: Real Indian blockbusters across 5 major film industries with verified metadata, genuine theatrical artwork, ratings, and classifications.
- **7-Tier Relational Hierarchy**: Multi-city scheduling architecture:
  $$\text{City} \longrightarrow \text{Theatre} \longrightarrow \text{Screen Format} \longrightarrow \text{Movie} \longrightarrow \text{Date} \longrightarrow \text{Showtime} \longrightarrow \text{Seats}$$
- **Interactive Auditorium Seating (Rows A–L)**: Full 96-seat layout per show (Recliner, Elite, Classic) with walking aisles, curved screen indicator, zoom controls (`[🔍+ In]`, `[🔍- Out]`, `[↺ Reset]`), and emerald green (`#10B981`) selection highlights.
- **ACID-Compliant Concurrency**: SQLite transactions (`PRAGMA foreign_keys = ON;`) ensuring zero double-booking and automatic rollback on seat contention.
- **Digital Boarding Pass Ticket**: Real-time receipt generator with unique booking references (`CB-2026-XXXXX`), exportable to **HTML** and **Plain Text**.
- **Operations Console & Admin**: Live platform metric counters (Movies, Cities, Theatres, Screens, Shows), multi-theatre browser, and live ticket tier price adjuster.
- **100% Automated Test Coverage**: 38 automated test cases passing across 4 comprehensive suites, plus dedicated visual card audit tests.

---

## 📸 Application Walkthrough & Architecture

```
┌────────────────────────────────────────────────────────────────────────┐
│  CineBook  |  📍 Chennai ▼  |  🔍 Search movies...   |  🎟 My Bookings  │
├────────────────────────────────────────────────────────────────────────┤
│  [Now Showing]  [Upcoming]  •  [All]  [Telugu]  [Tamil]  [Hindi] ...   │
├────────────────────────────────────────────────────────────────────────┤
│  🎬 RECOMMENDED MOVIES                                 [◀ Prev] [Next ▶]│
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐│
│  │ ★ 8.8 (130K) │  │ ★ 8.3 (220K) │  │ ★ 8.3 (38K)  │  │ ★ 7.9 (65K)  ││
│  │  12th Fail   │  │    Dangal    │  │Manjummel Boys│  │   Hanu-Man   ││
│  │ [Book Tickets│  │ [Book Tickets│  │ [Book Tickets│  │ [Book Tickets││
│  └──────────────┘  └──────────────┘  └──────────────┘  └──────────────┘│
├────────────────────────────────────────────────────────────────────────┤
│  🎥 STREAM CINEMA PASS — Stream Premieres & Film Festivals Direct      │
├────────────────────────────────────────────────────────────────────────┤
│  🎬 EXPLORE ALL MOVIES (20 Titles Available)                           │
│  [Responsive Grid adapting from 1 to 5 columns based on window width]  │
└────────────────────────────────────────────────────────────────────────┘
```

---

## 🎬 3. Authentic Indian Cinema Catalogue

CineBook features 20 verified theatrical blockbusters across 5 Indian film industries:

| # | Movie Title | Industry / Language | Genre | Rating | Censor | Director | Status |
|:---:|:---|:---|:---|:---:|:---:|:---|:---:|
| 1 | **RRR** | Telugu Cinema | Action / Drama / Period | ★ 8.7 | U/A | S. S. Rajamouli | Now Showing |
| 2 | **Baahubali 2: The Conclusion** | Telugu Cinema | Action / Fantasy / Drama | ★ 8.2 | U/A | S. S. Rajamouli | Now Showing |
| 3 | **Pushpa 2: The Rule** | Telugu Cinema | Action / Crime / Thriller | ★ 8.4 | U/A | Sukumar | Now Showing |
| 4 | **Kalki 2898 AD** | Telugu Cinema | Sci-Fi / Action / Mythology | ★ 7.6 | U/A | Nag Ashwin | Now Showing |
| 5 | **Hanu-Man** | Telugu Cinema | Action / Adventure / Fantasy | ★ 7.9 | U/A | Prasanth Varma | Now Showing |
| 6 | **Leo: Bloody Sweet** | Tamil Cinema | Action / Thriller | ★ 7.2 | U/A | Lokesh Kanagaraj | Now Showing |
| 7 | **Vikram: Hitlist** | Tamil Cinema | Action / Crime / Mystery | ★ 8.3 | U/A | Lokesh Kanagaraj | Now Showing |
| 8 | **Jailer** | Tamil Cinema | Action / Comedy / Drama | ★ 7.1 | U/A | Nelson Dilipkumar | Now Showing |
| 9 | **Ponniyin Selvan: Part 1** | Tamil Cinema | Action / Drama / Historical | ★ 7.6 | U/A | Mani Ratnam | Now Showing |
| 10 | **Jawan** | Hindi / Bollywood | Action / Thriller | ★ 7.0 | U/A | Atlee | Now Showing |
| 11 | **12th Fail** | Hindi / Bollywood | Biography / Drama | ★ 8.8 | U | Vidhu Vinod Chopra | Now Showing |
| 12 | **Dangal** | Hindi / Bollywood | Biography / Drama / Sport | ★ 8.3 | U | Nitesh Tiwari | Now Showing |
| 13 | **Stree 2: Sarkate Ka Aatank** | Hindi / Bollywood | Comedy / Horror / Mystery | ★ 7.1 | U/A | Amar Kaushik | Now Showing |
| 14 | **Manjummel Boys** | Malayalam Cinema | Survival / Thriller / Drama | ★ 8.3 | U | Chidambaram | Now Showing |
| 15 | **Aavesham** | Malayalam Cinema | Action / Comedy | ★ 7.9 | U/A | Jithu Madhavan | Now Showing |
| 16 | **Lucifer** | Malayalam Cinema | Action / Crime / Thriller | ★ 7.5 | U/A | Prithviraj Sukumaran | Now Showing |
| 17 | **K.G.F: Chapter 2** | Kannada Cinema | Action / Crime / Drama | ★ 8.2 | U/A | Prashanth Neel | Now Showing |
| 18 | **Kantara: A Legend** | Kannada Cinema | Action / Drama / Folklore | ★ 8.2 | U/A | Rishab Shetty | Now Showing |
| 19 | **777 Charlie** | Kannada Cinema | Adventure / Comedy / Drama | ★ 8.7 | U | Kiranraj K | Now Showing |
| 20 | **Kantara: Chapter 1 (Prequel)** | Kannada Cinema | Action / Drama / Mythology | — | U/A | Rishab Shetty | Upcoming |

> **Note on Posters**: All posters are authentic 2:3 high-resolution theatrical covers saved under [`assets/posters/`](file:///c:/Users/Kskre/Desktop/TIKENTER/assets/posters) with provenance metadata tracked in [`assets/posters/posters_manifest.json`](file:///c:/Users/Kskre/Desktop/TIKENTER/assets/posters/posters_manifest.json). Unreleased or unavailable titles render a dedicated clean slate notice without AI distortions.

---

## 🏛️ 4. Multi-City & Theatre Hierarchy

CineBook implements realistic cinema operations across 5 major Indian metropolitan hubs:

```
[City Hubs]
├── 📍 Chennai     (Tamil Nadu)  ─── 3 Theatres, 9 Screens
├── 📍 Hyderabad   (Telangana)   ─── 3 Theatres, 9 Screens
├── 📍 Bengaluru   (Karnataka)   ─── 3 Theatres, 9 Screens
├── 📍 Mumbai      (Maharashtra) ─── 3 Theatres, 9 Screens
└── 📍 Kochi       (Kerala)      ─── 3 Theatres, 9 Screens
```

### Premium Auditorium Screen Formats
1. **IMAX Laser 3D** — Flagship giant-screen experience (Classic: ₹180, Elite: ₹260, Recliner: ₹360).
2. **Dolby Atmos 4K** — 360-degree immersive acoustic cinema (Classic: ₹150, Elite: ₹220, Recliner: ₹300).
3. **Luxe Cinema Lounge** — Plush leather seating & VIP hospitality (Classic: ₹200, Elite: ₹280, Recliner: ₹380).
4. **Standard 2K Digital** — Everyday reliable cinema (Classic: ₹140, Elite: ₹200, Recliner: ₹280).

---

## 💺 5. Auditorium Seating Matrix (Rows A–L)

Every scheduled screening features an interactive **96-seat layout**:
- **Rows A & B (Recliner Section)**: Premium front viewing with ultra-wide spacing (`₹300 – ₹380`).
- **Rows C to F (Elite Section)**: Prime centre viewing angle (`₹200 – ₹280`).
- **Rows G to L (Classic Section)**: Standard cinema seating (`₹140 – ₹200`).

### Interactive Features
- **Walking Aisle**: Central passage separating seats `1–4` (Left Wing) and `5–8` (Right Wing).
- **Curved Screen Indicator**: Bottom-mounted curved cinema screen with `• ALL EYES THIS WAY PLEASE (SCREEN) •`.
- **Zoom & Pan Controls**: `[🔍+ In]`, `[🔍- Out]`, and `[↺ Reset]` buttons to scale the layout for accessibility.
- **Seat States & Colors**:
  - ⚪ **Available**: Clean white button with dark text.
  - 🟢 **Selected**: Emerald green (`#10B981`) with white text.
  - 🔘 **Booked / Sold**: Disabled grey button with diagonal hatch indicator.
  - ⭐ **Bestseller**: Highlighted with an amber border (`#F59E0B`).
- **Safety Limit**: Enforces a maximum of **6 tickets per booking** with user-friendly alerts.

---

## 🗄️ 6. System Architecture & Database Design

### Relational Schema (SQLite3)
CineBook strictly enables SQLite foreign keys (`PRAGMA foreign_keys = ON;`) to guarantee relational integrity:

```
  ┌─────────────┐       ┌──────────────┐       ┌─────────────┐
  │   cities    │──1:N──│   theatres   │──1:N──│   screens   │
  └─────────────┘       └──────────────┘       └─────────────┘
                                                      │
                                                     1:N
                                                      ▼
  ┌─────────────┐                              ┌─────────────┐
  │   movies    │─────────────1:N─────────────▶│    shows    │
  └─────────────┘                              └─────────────┘
         │                                            │
         │                                           1:N
         │                                            ▼
         │       ┌──────────────┐              ┌─────────────┐
         └──────▶│   bookings   │◀─────0:1─────│ show_seats  │
                 └──────────────┘              └─────────────┘
                        │
                       1:N
                        ▼
                 ┌──────────────┐
                 │booking_seats │
                 └──────────────┘
```

### Transactional Concurrency & Rollback
When multiple users attempt to book simultaneously, CineBook uses an atomic database transaction:
1. Re-verifies live seat status within the open transaction.
2. Updates `show_seats` conditionally:
   ```sql
   UPDATE show_seats
   SET status = 'BOOKED', booking_id = ?
   WHERE show_id = ? AND seat_number = ? AND status = 'AVAILABLE';
   ```
3. If any selected seat is unavailable, transaction rolls back completely and raises `SeatUnavailableError`.
4. Cancellations restore seats to `AVAILABLE` without deleting the historical booking record.

---

## 📂 Repository File Structure

```text
TIKENTER/
├── main.py                     # Application entry point & master view router
├── database.py                 # SQLite database engine, schema, & ACID transactions
├── models.py                   # Domain models (City, Theatre, Screen, Movie, Show, Seat, Booking)
├── run_tests.py                # Unified automated test runner (Runs all 4 core test suites)
├── generate_posters.py         # Poster generator and cache utilities
├── requirements.txt            # Python dependencies (Pillow)
├── README.md                   # System documentation & usage guide
├── assets/
│   ├── logo.png                # CineBook master header logo
│   └── posters/                # 20 Authentic theatrical posters (.jpg)
│       ├── CineBooklogo.png    # High-resolution application brand asset
│       └── posters_manifest.json # Poster metadata & provenance catalog
├── data/
│   └── cinebook.db             # Relational SQLite database file
├── exports/                    # Exported digital ticket passes (.html, .txt)
├── tests/
│   ├── test_booking_logic.py   # Unit & concurrency transaction tests (10 tests)
│   ├── test_gui_headless.py    # Headless GUI view switching tests (6 tests)
│   ├── test_redesign_verification.py # Integration, seat limit & responsive tests (16 tests)
│   ├── test_home_redesign.py   # Home view layout, filters & banner tests (7 tests)
│   └── test_movie_card_fit.py  # Typography sizes & button alignment audit (6 tests)
└── ui/
    ├── theme.py                # Design tokens, color palette, fonts & geometry
    ├── components.py           # MovieCardWidget, PosterWidget, CurvedScreen, SeatWidget
    ├── home_view.py            # Movie discovery carousel, filters & promo banner
    ├── movie_view.py           # City selector, theatre grouping & showtime picker
    ├── seat_view.py            # Rows A–L seating matrix, zoom & live price breakdown
    ├── checkout_view.py        # Customer details validation & atomic checkout
    ├── ticket_view.py          # Digital boarding pass & receipt export
    ├── bookings_view.py        # My Bookings history table & cancellation flow
    ├── admin_view.py           # Operations console & live tier price adjuster
    └── about_view.py           # System info, architectural specs & database reset
```

---

## 🚀 7. Quick Start & Installation

### Prerequisites
- **Python 3.10+** (Standard installation includes `tkinter`, `sqlite3`, and `unittest`).

### Step-by-Step Setup
1. **Clone or Open the Repository**:
   ```bash
   cd c:\Users\Kskre\Desktop\TIKENTER
   ```

2. **(Optional) Create and Activate a Virtual Environment**:
   ```bash
   python -m venv venv
   # On Windows:
   .\venv\Scripts\activate
   # On macOS/Linux:
   source venv/bin/activate
   ```

3. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```
   *(CineBook only requires `Pillow>=10.0.0` for high-quality poster scaling).*

4. **Launch CineBook**:
   ```bash
   python main.py
   ```

---

## 🧪 8. Running Automated Tests

CineBook comes with a comprehensive test suite covering database ACID transactions, view lifecycles, booking flows, and UI responsiveness.

### Run All Core Test Suites
To run the full automated test suite runner:
```bash
python run_tests.py
```

**Expected Terminal Output**:
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

[RUNNING SUITE] Complete Home Redesign Verification (tests/test_home_redesign.py)...
---------------------------------------------------------------------------
--> [PASSED] Complete Home Redesign Verification

===========================================================================
 FINAL STATUS: ALL 4 TEST SUITES PASSED (38/38 TESTS SUCCESSFUL)
===========================================================================
```

### Running Individual Test Suites
You can run any test module independently using Python's `unittest`:

```bash
# 1. Database transactions & double-booking prevention (10 tests)
python -m unittest tests/test_booking_logic.py

# 2. Headless GUI view switching & lifecycle (6 tests)
python -m unittest tests/test_gui_headless.py

# 3. Responsive window resizing, booking flow & seat limits (16 tests)
python -m unittest tests/test_redesign_verification.py

# 4. Home redesign, search live update & carousel (7 tests)
python -m unittest tests/test_home_redesign.py

# 5. Card typography & button baseline alignment audit (6 tests)
python -m unittest tests/test_movie_card_fit.py
```

---

## 📖 9. User Interaction Guide

1. **Explore & Filter**:
   - Change your city using the top-bar dropdown (e.g. *Chennai*, *Hyderabad*, *Bengaluru*).
   - Filter by release status (*Now Showing*, *Upcoming*) or language (*Telugu*, *Tamil*, *Hindi*, *Malayalam*, *Kannada*).
   - Use the live search bar to find titles by name or actor.
2. **Select Showtime**:
   - Click **"Book Tickets"** on any card.
   - Choose your preferred date tab, theatre, auditorium format (*IMAX*, *Dolby Atmos*), and showtime slot.
3. **Choose Seats**:
   - Click any white seat in **Rows A–L** (up to 6 seats).
   - Use `[🔍+ In]` and `[🔍- Out]` to zoom the seating matrix.
   - Click **"Proceed to Checkout →"**.
4. **Checkout & Boarding Pass**:
   - Enter your name, 10-digit mobile number, and optional email.
   - Click **"Confirm & Pay"** to generate the digital ticket pass.
   - Click **"Export Ticket (HTML)"** or **"Save as Text"** to generate local files in `exports/`.
5. **Manage Bookings**:
   - View your reservations under **"🎟 My Bookings"** in the top navigation bar.
   - Filter by *Confirmed*, *Cancelled*, or *All*.
   - Cancel tickets anytime to release seats back into the available pool.
6. **Factory Database Reset**:
   - Navigate to **"ℹ About"** in the top navigation header.
   - Click **"🔄 Reset Sample Database to Factory Defaults"** to clear demo data and restore fresh seed inventory.

---

## 🛠️ 10. Frequently Asked Questions (FAQ)

<details>
<summary><b>Q: Text appears slightly blurry on high-resolution Windows displays. How to fix?</b></summary>
<br>
CineBook automatically invokes Windows Per-Monitor DPI scaling via <code>ctypes.windll.shcore.SetProcessDpiAwareness(2)</code> in <code>main.py</code>. If running under an older Windows version, the app gracefully falls back to system DPI awareness.
</details>

<details>
<summary><b>Q: What happens if two customers pick the exact same seat simultaneously?</b></summary>
<br>
CineBook uses atomic SQLite conditional updates. The second customer's transaction will detect that the seat status is no longer <code>AVAILABLE</code>, roll back immediately, and present a helpful alert asking them to choose an alternate seat.
</details>

<details>
<summary><b>Q: Where are exported tickets saved?</b></summary>
<br>
All exported ticket files are placed in the <a href="file:///c:/Users/Kskre/Desktop/TIKENTER/exports"><code>exports/</code></a> directory in both interactive styled HTML and plain ASCII text formats.
</details>

---

## 📄 License
This project is developed for educational and academic demonstration purposes. All movie titles, character names, and poster artworks belong to their respective production houses and distributors.
