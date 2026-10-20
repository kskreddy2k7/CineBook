"""
CineBook - Database Module
SQLite persistent storage, relational schema, ACID transactional booking and cancellation,
and multi-tier hierarchy: City → Theatre → Screen → Movie → Show → Seat → Booking.
"""

import sqlite3
import random
import string
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple, Any

from models import City, Theatre, Screen, Movie, Show, Seat, Booking, BookingItem


class DatabaseError(Exception):
    """Base exception for CineBook database operations."""
    pass


class SeatUnavailableError(DatabaseError):
    """Raised when one or more requested seats are already booked or invalid."""
    pass


class BookingNotFoundError(DatabaseError):
    """Raised when a booking reference or ID is not found."""
    pass


class DatabaseManager:
    """Manages SQLite connection, schema lifecycle, transactions, and multi-theatre queries."""

    def __init__(self, db_path: Optional[str] = None):
        if db_path is None:
            base_dir = Path(__file__).resolve().parent
            data_dir = base_dir / "data"
            data_dir.mkdir(parents=True, exist_ok=True)
            self.db_path = str(data_dir / "cinebook.db")
        else:
            self.db_path = str(db_path)
            Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)

        self._init_database()

    def get_connection(self) -> sqlite3.Connection:
        """Create and return a new SQLite connection with foreign keys enabled."""
        conn = sqlite3.connect(self.db_path, timeout=15.0)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON;")
        return conn

    def _init_database(self) -> None:
        """Create relational schema and populate Indian cinema data if unseeded."""
        conn = self.get_connection()
        try:
            with conn:
                cursor = conn.cursor()

                # Check if legacy shows table exists without screen_id column
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='shows';")
                if cursor.fetchone():
                    cursor.execute("PRAGMA table_info(shows);")
                    cols = [r["name"] for r in cursor.fetchall()]
                    if "screen_id" not in cols:
                        cursor.execute("DROP TABLE IF EXISTS booking_seats;")
                        cursor.execute("DROP TABLE IF EXISTS bookings;")
                        cursor.execute("DROP TABLE IF EXISTS show_seats;")
                        cursor.execute("DROP TABLE IF EXISTS shows;")
                        cursor.execute("DROP TABLE IF EXISTS screens;")
                        cursor.execute("DROP TABLE IF EXISTS theatres;")
                        cursor.execute("DROP TABLE IF EXISTS cities;")
                        cursor.execute("DROP TABLE IF EXISTS movies;")

                # 1. Cities Table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS cities (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        name TEXT UNIQUE NOT NULL,
                        state TEXT NOT NULL,
                        is_active INTEGER DEFAULT 1
                    );
                """)

                # 2. Theatres Table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS theatres (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        city_id INTEGER NOT NULL,
                        name TEXT NOT NULL,
                        location TEXT NOT NULL,
                        address TEXT,
                        FOREIGN KEY (city_id) REFERENCES cities (id) ON DELETE CASCADE
                    );
                """)

                # 3. Screens Table (Auditoriums)
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS screens (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        theatre_id INTEGER NOT NULL,
                        screen_name TEXT NOT NULL,
                        screen_type TEXT NOT NULL,
                        total_seats INTEGER DEFAULT 96,
                        rows_count INTEGER DEFAULT 12,
                        seats_per_row INTEGER DEFAULT 8,
                        FOREIGN KEY (theatre_id) REFERENCES theatres (id) ON DELETE CASCADE
                    );
                """)

                # 4. Movies Table (Indian Cinema)
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS movies (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        title TEXT NOT NULL,
                        genre TEXT NOT NULL,
                        duration TEXT NOT NULL,
                        rating REAL NOT NULL,
                        censor_rating TEXT DEFAULT 'U/A',
                        language TEXT DEFAULT 'Telugu',
                        description TEXT NOT NULL,
                        director TEXT NOT NULL,
                        cast TEXT NOT NULL,
                        poster_path TEXT,
                        banner_color TEXT DEFAULT '#1E293B',
                        industry TEXT DEFAULT 'Indian Cinema',
                        release_year INTEGER DEFAULT 2024,
                        vote_count TEXT DEFAULT '50K',
                        is_upcoming INTEGER DEFAULT 0,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    );
                """)

                # 5. Shows Table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS shows (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        movie_id INTEGER NOT NULL,
                        screen_id INTEGER NOT NULL,
                        show_date TEXT NOT NULL,
                        show_time TEXT NOT NULL,
                        price_classic REAL DEFAULT 150.0,
                        price_elite REAL DEFAULT 220.0,
                        price_recliner REAL DEFAULT 300.0,
                        price_standard REAL DEFAULT 150.0,
                        price_premium REAL DEFAULT 220.0,
                        total_seats INTEGER DEFAULT 96,
                        FOREIGN KEY (movie_id) REFERENCES movies (id) ON DELETE CASCADE,
                        FOREIGN KEY (screen_id) REFERENCES screens (id) ON DELETE CASCADE
                    );
                """)

                # 6. Show Seats Table (Inventory per show)
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS show_seats (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        show_id INTEGER NOT NULL,
                        seat_number TEXT NOT NULL,
                        tier TEXT NOT NULL,
                        price REAL NOT NULL,
                        status TEXT NOT NULL DEFAULT 'AVAILABLE',
                        booking_id INTEGER,
                        FOREIGN KEY (show_id) REFERENCES shows (id) ON DELETE CASCADE,
                        FOREIGN KEY (booking_id) REFERENCES bookings (id) ON DELETE SET NULL,
                        UNIQUE(show_id, seat_number)
                    );
                """)

                # 7. Bookings Table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS bookings (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        booking_ref TEXT UNIQUE NOT NULL,
                        show_id INTEGER NOT NULL,
                        customer_name TEXT NOT NULL,
                        customer_phone TEXT NOT NULL,
                        customer_email TEXT,
                        seat_count INTEGER NOT NULL,
                        subtotal REAL NOT NULL,
                        convenience_fee REAL NOT NULL,
                        total_price REAL NOT NULL,
                        booking_status TEXT NOT NULL DEFAULT 'CONFIRMED',
                        created_at TEXT NOT NULL,
                        cancelled_at TEXT,
                        FOREIGN KEY (show_id) REFERENCES shows (id) ON DELETE RESTRICT
                    );
                """)

                # 8. Booking Seats Junction Table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS booking_seats (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        booking_id INTEGER NOT NULL,
                        seat_number TEXT NOT NULL,
                        tier TEXT NOT NULL,
                        price REAL NOT NULL,
                        FOREIGN KEY (booking_id) REFERENCES bookings (id) ON DELETE CASCADE
                    );
                """)

                # Check if hierarchy is seeded
                cursor.execute("SELECT COUNT(*) AS cnt FROM cities;")
                city_count = cursor.fetchone()["cnt"]

                cursor.execute("SELECT COUNT(*) AS cnt FROM movies;")
                movie_count = cursor.fetchone()["cnt"]

                # Automatically update poster filenames to authentic .jpg theatrical assets if available
                cursor.execute("UPDATE movies SET poster_path = REPLACE(poster_path, '.png', '.jpg') WHERE poster_path LIKE '%.png';")

                cursor.execute("SELECT COUNT(*) AS cnt FROM movies WHERE title = 'Hanu-Man';")
                has_hanu_man = cursor.fetchone()["cnt"] > 0

                # If unseeded, old schema, or lacking Hanu-Man in authentic catalogue, seed complete hierarchy
                if city_count == 0 or movie_count < 20 or not has_hanu_man:
                    self._seed_complete_hierarchy(conn)
                else:
                    # Check if any movie lacks configured shows
                    cursor.execute("""
                        SELECT m.id FROM movies m
                        WHERE NOT EXISTS (SELECT 1 FROM shows s WHERE s.movie_id = m.id);
                    """)
                    if cursor.fetchall():
                        self._ensure_demo_shows(conn)
        finally:
            conn.close()

    def _seed_complete_hierarchy(self, conn: sqlite3.Connection) -> None:
        """Populates the complete Indian Cinema multi-city hierarchy with 20 movies and shows."""
        cursor = conn.cursor()

        # Clean old data if upgrading schema
        cursor.execute("DELETE FROM booking_seats;")
        cursor.execute("DELETE FROM bookings;")
        cursor.execute("DELETE FROM show_seats;")
        cursor.execute("DELETE FROM shows;")
        cursor.execute("DELETE FROM screens;")
        cursor.execute("DELETE FROM theatres;")
        cursor.execute("DELETE FROM cities;")
        cursor.execute("DELETE FROM movies;")
        try:
            cursor.execute("DELETE FROM sqlite_sequence WHERE name IN ('booking_seats', 'bookings', 'show_seats', 'shows', 'screens', 'theatres', 'cities', 'movies');")
        except Exception:
            pass

        # 1. Seed 5 Major Indian Cities
        sample_cities = [
            ("Chennai", "Tamil Nadu"),
            ("Hyderabad", "Telangana"),
            ("Bengaluru", "Karnataka"),
            ("Mumbai", "Maharashtra"),
            ("Kochi", "Kerala"),
        ]
        city_ids = {}
        for name, state in sample_cities:
            cursor.execute("INSERT INTO cities (name, state) VALUES (?, ?);", (name, state))
            city_ids[name] = cursor.lastrowid

        # 2. Seed Sample Demonstration Theatres (3 per city = 15 total)
        sample_theatres = [
            # Chennai
            (city_ids["Chennai"], "CineBook Luxe Cinemas", "Phoenix MarketCity, Velachery", "Velachery Main Rd, Chennai"),
            (city_ids["Chennai"], "CineBook PVR Grand", "Express Avenue, Royapettah", "Whites Rd, Royapettah, Chennai"),
            (city_ids["Chennai"], "CineBook INOX National", "Arcot Road, Vadapalani", "Arcot Rd, Vadapalani, Chennai"),
            # Hyderabad
            (city_ids["Hyderabad"], "CineBook Prasads Multiplex", "NTR Marg, Khairatabad", "NTR Marg, Central Hyderabad"),
            (city_ids["Hyderabad"], "CineBook AMB Cinemas", "Gachibowli - Kondapur", "Sarath City Capital Mall, Kondapur"),
            (city_ids["Hyderabad"], "CineBook PVR Forum Sujana", "KPHB, Kukatpally", "Forum Sujana Mall, Kukatpally"),
            # Bengaluru
            (city_ids["Bengaluru"], "CineBook Orion Mall IMAX", "Dr. Rajkumar Road", "Orion Mall, Brigade Gateway, Rajajinagar"),
            (city_ids["Bengaluru"], "CineBook PVR Vega City", "Bannerghatta Main Road", "Vega City Mall, BTM Layout, Bengaluru"),
            (city_ids["Bengaluru"], "CineBook INOX Forum Rex", "Brigade Road", "Forum Rex Walk, Central Bengaluru"),
            # Mumbai
            (city_ids["Mumbai"], "CineBook PVR Maison Luxe", "Jio World Drive, BKC", "Bandra Kurla Complex, Mumbai"),
            (city_ids["Mumbai"], "CineBook INOX Megaplex", "Inorbit Mall, Malad West", "Link Road, Malad West, Mumbai"),
            (city_ids["Mumbai"], "CineBook PVR Dynamix", "Juhu Tara Road", "Near Juhu Beach, Santacruz West, Mumbai"),
            # Kochi
            (city_ids["Kochi"], "CineBook PVR LuLu Mall", "Edappally, Kochi Metro", "LuLu International Shopping Mall, Edappally"),
            (city_ids["Kochi"], "CineBook Cinepolis", "Centre Square Mall, MG Road", "MG Road, Shenoys, Kochi"),
            (city_ids["Kochi"], "CineBook Shenoys 4K Laser", "Shenoys Junction", "Mahatma Gandhi Rd, Ernakulam, Kochi"),
        ]

        theatre_ids = []
        for c_id, name, loc, addr in sample_theatres:
            cursor.execute("""
                INSERT INTO theatres (city_id, name, location, address)
                VALUES (?, ?, ?, ?);
            """, (c_id, name, loc, addr))
            theatre_ids.append(cursor.lastrowid)

        # 3. Seed 3 Screens for each Theatre (45 total screens)
        screen_templates = [
            ("Audi 1 — IMAX Laser 3D", "IMAX Laser 3D", 96, 12, 8),
            ("Audi 2 — Dolby Atmos 4K", "Dolby Atmos 4K", 96, 12, 8),
            ("Audi 3 — CineBook Luxe Lounge", "Luxe Cinema Lounge", 96, 12, 8),
        ]

        screen_ids = []
        for t_id in theatre_ids:
            for s_name, s_type, total, rows, cols in screen_templates:
                cursor.execute("""
                    INSERT INTO screens (theatre_id, screen_name, screen_type, total_seats, rows_count, seats_per_row)
                    VALUES (?, ?, ?, ?, ?, ?);
                """, (t_id, s_name, s_type, total, rows, cols))
                screen_ids.append(cursor.lastrowid)

        # 4. Seed 20 Verified Indian Movies
        sample_movies = self._get_sample_indian_movies()
        movie_ids = []
        for m_data in sample_movies:
            cursor.execute("""
                INSERT INTO movies (
                    title, genre, duration, rating, censor_rating, language,
                    description, director, cast, poster_path, banner_color,
                    industry, release_year, vote_count, is_upcoming
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
            """, m_data)
            movie_ids.append(cursor.lastrowid)

        # 5. Populate Shows and Seating Inventory
        self._seed_shows_and_seats(conn)

    def _get_sample_indian_movies(self) -> List[Tuple]:
        """Canonical factual dataset of 20 Indian movies across Telugu, Tamil, Hindi, Malayalam, and Kannada."""
        return [
            # 1. RRR (Telugu)
            (
                "RRR",
                "Action / Drama / Epic",
                "187 min",
                8.8,
                "U/A",
                "Telugu",
                "A fearless warrior on a perilous rescue mission crosses paths with a steely officer in the British Indian police force, igniting a brotherhood that shakes an empire.",
                "S.S. Rajamouli",
                "NTR Jr, Ram Charan, Alia Bhatt, Ajay Devgn",
                "assets/posters/rrr.jpg",
                "#5A0F14",
                "Telugu Cinema",
                2022,
                "165K",
                0
            ),
            # 2. Baahubali 2: The Conclusion (Telugu)
            (
                "Baahubali 2: The Conclusion",
                "Action / Drama / Fantasy",
                "167 min",
                8.2,
                "U/A",
                "Telugu",
                "When Shiva, the son of Amarendra Baahubali, learns about his royal heritage, he embarks on an epochal battle to free Mahishmati from the tyrannical Bhallaladeva.",
                "S.S. Rajamouli",
                "Prabhas, Rana Daggubati, Anushka Shetty, Tamannaah Bhatia",
                "assets/posters/baahubali_2.jpg",
                "#78350F",
                "Telugu Cinema",
                2017,
                "115K",
                0
            ),
            # 3. Pushpa 2: The Rule (Telugu)
            (
                "Pushpa 2: The Rule",
                "Action / Crime / Thriller",
                "175 min",
                7.8,
                "U/A",
                "Telugu",
                "Pushpa Raj solidifies his unyielding grip over the clandestine red sandalwood smuggling empire while facing escalating rivalry from SP Bhanwar Singh Shekhawat.",
                "Sukumar",
                "Allu Arjun, Fahadh Faasil, Rashmika Mandanna, Jagapathi Babu",
                "assets/posters/pushpa_2.jpg",
                "#713F12",
                "Telugu Cinema",
                2024,
                "92K",
                0
            ),
            # 4. Kalki 2898 AD (Telugu)
            (
                "Kalki 2898 AD",
                "Action / Sci-Fi / Fantasy",
                "181 min",
                7.6,
                "U/A",
                "Telugu",
                "In a dystopian post-apocalyptic future ruled by the Complex, a mercenary, an immortal warrior, and a divine rebel converge around the miraculous child of destiny.",
                "Nag Ashwin",
                "Prabhas, Amitabh Bachchan, Kamal Haasan, Deepika Padukone",
                "assets/posters/kalki_2898_ad.jpg",
                "#1E1B4B",
                "Telugu Cinema",
                2024,
                "85K",
                0
            ),
            # 5. Leo: Bloody Sweet (Tamil)
            (
                "Leo: Bloody Sweet",
                "Action / Crime / Thriller",
                "164 min",
                7.2,
                "U/A",
                "Tamil",
                "A gentle cafe owner in Himachal Pradesh becomes an overnight hero after saving his town, only for vicious drug kingpins from his past to question his true identity.",
                "Lokesh Kanagaraj",
                "Thalapathy Vijay, Sanjay Dutt, Trisha Krishnan, Arjun Sarja",
                "assets/posters/leo.jpg",
                "#450A0A",
                "Tamil Cinema",
                2023,
                "78K",
                0
            ),
            # 6. Vikram: Hitlist (Tamil)
            (
                "Vikram: Hitlist",
                "Action / Crime / Mystery",
                "175 min",
                8.3,
                "U/A",
                "Tamil",
                "A covert special investigation team led by Amar probes a series of masked vigilante assassinations connected to a missing consignment of lethal narcotics.",
                "Lokesh Kanagaraj",
                "Kamal Haasan, Vijay Sethupathi, Fahadh Faasil, Suriya",
                "assets/posters/vikram.jpg",
                "#1C1917",
                "Tamil Cinema",
                2022,
                "82K",
                0
            ),
            # 7. Jailer (Tamil)
            (
                "Jailer",
                "Action / Comedy / Crime",
                "168 min",
                7.1,
                "U/A",
                "Tamil",
                "Tiger Muthuvel Pandian, a retired prison warden, wages a fierce war against an antique smuggler syndicate after discovering his police son was betrayed.",
                "Nelson Dilipkumar",
                "Rajinikanth, Vinayakan, Ramya Krishnan, Mohanlal",
                "assets/posters/jailer.jpg",
                "#3B0764",
                "Tamil Cinema",
                2023,
                "64K",
                0
            ),
            # 8. Ponniyin Selvan: Part 1 (Tamil)
            (
                "Ponniyin Selvan: Part 1",
                "Action / Adventure / Drama",
                "167 min",
                7.6,
                "U/A",
                "Tamil",
                "Vandiyathevan journeys across the Chola kingdom carrying a confidential message, unraveling a palace conspiracy plotting the overthrow of Emperor Sundara Chozhar.",
                "Mani Ratnam",
                "Vikram, Aishwarya Rai Bachchan, Jayam Ravi, Karthi, Trisha",
                "assets/posters/ponniyin_selvan_1.jpg",
                "#701A75",
                "Tamil Cinema",
                2022,
                "52K",
                0
            ),
            # 9. Jawan (Hindi)
            (
                "Jawan",
                "Action / Thriller",
                "169 min",
                7.0,
                "U/A",
                "Hindi",
                "A prison warden with a heroic band of female operatives orchestrates audacious nationwide heists to rectify societal injustices and expose a corrupt weapons oligarch.",
                "Atlee",
                "Shah Rukh Khan, Nayanthara, Vijay Sethupathi, Deepika Padukone",
                "assets/posters/jawan.jpg",
                "#831843",
                "Hindi / Bollywood",
                2023,
                "110K",
                0
            ),
            # 10. 12th Fail (Hindi)
            (
                "12th Fail",
                "Biography / Drama",
                "147 min",
                8.8,
                "U",
                "Hindi",
                "Inspired by the true journey of IPS officer Manoj Kumar Sharma, who rose from extreme poverty in the Chambal ravines to clear the arduous UPSC civil services exam.",
                "Vidhu Vinod Chopra",
                "Vikrant Massey, Medha Shankr, Anant V Joshi, Priyanshu Chatterjee",
                "assets/posters/12th_fail.jpg",
                "#14532D",
                "Hindi / Bollywood",
                2023,
                "130K",
                0
            ),
            # 11. Dangal (Hindi)
            (
                "Dangal",
                "Biography / Drama / Sport",
                "161 min",
                8.3,
                "U",
                "Hindi",
                "Former wrestler Mahavir Singh Phogat coaches his daughters Geeta and Babita to overcome cultural bias and win India's first Commonwealth gold medals in wrestling.",
                "Nitesh Tiwari",
                "Aamir Khan, Fatima Sana Shaikh, Sanya Malhotra, Sakshi Tanwar",
                "assets/posters/dangal.jpg",
                "#78350F",
                "Hindi / Bollywood",
                2016,
                "220K",
                0
            ),
            # 12. Stree 2: Sarkate Ka Aatank (Hindi)
            (
                "Stree 2: Sarkate Ka Aatank",
                "Comedy / Horror / Mystery",
                "147 min",
                7.1,
                "U/A",
                "Hindi",
                "The eccentric town of Chanderi is plagued by a sinister headless terror named Sarkata. Vicky and friends must team up with past allies to protect their loved ones.",
                "Amar Kaushik",
                "Rajkummar Rao, Shraddha Kapoor, Pankaj Tripathi, Abhishek Banerjee",
                "assets/posters/stree_2.jpg",
                "#312E81",
                "Hindi / Bollywood",
                2024,
                "45K",
                0
            ),
            # 13. Manjummel Boys (Malayalam)
            (
                "Manjummel Boys",
                "Survival / Thriller / Drama",
                "135 min",
                8.3,
                "U",
                "Malayalam",
                "A tight-knit circle of young friends from Kochi visit the treacherous Guna Caves in Kodaikanal, where a shocking fall tests the ultimate bounds of brotherhood.",
                "Chidambaram",
                "Soubin Shahir, Sreenath Bhasi, Balu Varghese, Ganapathi",
                "assets/posters/manjummel_boys.jpg",
                "#0F766E",
                "Malayalam Cinema",
                2024,
                "38K",
                0
            ),
            # 14. Aavesham (Malayalam)
            (
                "Aavesham",
                "Action / Comedy",
                "158 min",
                7.9,
                "U/A",
                "Malayalam",
                "Three engineering college freshers in Bengaluru seek the protection of an eccentric local gangster named Ranga, triggering riotous hilarity and explosive chaos.",
                "Jithu Madhavan",
                "Fahadh Faasil, Hipzster, Mithun Jai Shankar, Roshan Shanavas",
                "assets/posters/aavesham.jpg",
                "#065F46",
                "Malayalam Cinema",
                2024,
                "41K",
                0
            ),
            # 15. Lucifer (Malayalam)
            (
                "Lucifer",
                "Action / Crime / Thriller",
                "174 min",
                7.5,
                "U/A",
                "Malayalam",
                "A political godfather dies, unleashing a ferocious battle for succession that threatens the state, prompting the enigmatic Stephen Nedumpally to emerge from the shadows.",
                "Prithviraj Sukumaran",
                "Mohanlal, Vivek Oberoi, Manju Warrier, Tovino Thomas",
                "assets/posters/lucifer.jpg",
                "#1E293B",
                "Malayalam Cinema",
                2019,
                "48K",
                0
            ),
            # 16. K.G.F: Chapter 2 (Kannada)
            (
                "K.G.F: Chapter 2",
                "Action / Crime / Drama",
                "168 min",
                8.2,
                "U/A",
                "Kannada",
                "In the blood-soaked Kolar Gold Fields, Rocky's undisputed supremacy is violently challenged by the ruthless warlord Adheera and government forces.",
                "Prashanth Neel",
                "Yash, Sanjay Dutt, Raveena Tandon, Srinidhi Shetty",
                "assets/posters/kgf_chapter_2.jpg",
                "#292524",
                "Kannada Cinema",
                2022,
                "155K",
                0
            ),
            # 17. Kantara: A Legend (Kannada)
            (
                "Kantara: A Legend",
                "Action / Adventure / Drama",
                "148 min",
                8.2,
                "U/A",
                "Kannada",
                "In coastal Karnataka, a Kambala champion named Shiva clashes with a resolute forest officer, awakening the sacred spirits of the Bhoota Kola divine ritual.",
                "Rishab Shetty",
                "Rishab Shetty, Sapthami Gowda, Kishore Kumar G, Achyuth Kumar",
                "assets/posters/kantara.jpg",
                "#1C1917",
                "Kannada Cinema",
                2022,
                "98K",
                0
            ),
            # 18. 777 Charlie (Kannada)
            (
                "777 Charlie",
                "Adventure / Comedy / Drama",
                "164 min",
                8.8,
                "U",
                "Kannada",
                "Dharma, a solitary factory worker stuck in a desolate routine, has his life transformed when a spirited stray Labrador pup enters his world.",
                "Kiranraj K",
                "Rakshit Shetty, Sangeetha Sringeri, Raj B. Shetty, Danish Sait",
                "assets/posters/777_charlie.jpg",
                "#065F46",
                "Kannada Cinema",
                2022,
                "65K",
                0
            ),
            # 19. Kantara: Chapter 1 Prequel (Sample Upcoming)
            (
                "Kantara: Chapter 1 (Prequel)",
                "Action / Drama / Mythology",
                "160 min",
                0.0,
                "U/A",
                "Kannada",
                "The ancient mythological genesis of the divine Panjurli and Guliga spirits during the Kadamba dynasty era unfolds in this epic folklore prequel.",
                "Rishab Shetty",
                "Rishab Shetty, Rukmini Vasanth, Achyuth Kumar",
                "assets/posters/kantara_prequel.jpg",
                "#831843",
                "Kannada Cinema",
                2025,
                "Upcoming",
                1
            ),
            # 20. Hanu-Man (Telugu)
            (
                "Hanu-Man",
                "Action / Adventure / Fantasy",
                "158 min",
                7.9,
                "U/A",
                "Telugu",
                "In the fictional village of Anjanadri, a petty thief named Hanumanthu gains superhuman powers from a mystical solar gemstone and must rise to defend his people.",
                "Prasanth Varma",
                "Teja Sajja, Amritha Aiyer, Varalaxmi Sarathkumar, Vinay Rai",
                "assets/posters/hanu_man.jpg",
                "#1E1B4B",
                "Telugu Cinema",
                2024,
                "65K",
                0
            )
        ]

    def _seed_shows_and_seats(self, conn: sqlite3.Connection) -> None:
        """Generates realistic schedules across dates and populates Rows A–L for each show."""
        cursor = conn.cursor()

        cursor.execute("SELECT id, title, is_upcoming FROM movies;")
        movies = cursor.fetchall()
        if not movies:
            return

        cursor.execute("""
            SELECT s.id as screen_id, s.screen_name, s.screen_type, s.theatre_id,
                   t.name as theatre_name, c.name as city_name
            FROM screens s
            JOIN theatres t ON s.theatre_id = t.id
            JOIN cities c ON t.city_id = c.id;
        """)
        screens = cursor.fetchall()
        if not screens:
            return

        today = datetime.now()
        dates = [(today + timedelta(days=i)).strftime("%Y-%m-%d") for i in range(4)]

        # Pricing templates by screen type
        pricing_by_type = {
            "IMAX Laser 3D": (180.0, 260.0, 360.0),
            "Dolby Atmos 4K": (150.0, 220.0, 300.0),
            "Luxe Cinema Lounge": (200.0, 280.0, 380.0),
            "Standard": (140.0, 200.0, 280.0)
        }

        time_slots = ["10:30 AM", "02:15 PM", "06:45 PM", "10:00 PM"]

        # Rows A to L (12 rows, 8 seats per row = 96 seats)
        # Rows A, B: RECLINER
        # Rows C, D, E, F: ELITE
        # Rows G, H, I, J, K, L: CLASSIC
        rows_layout = [
            ("A", "RECLINER", 8),
            ("B", "RECLINER", 8),
            ("C", "ELITE", 8),
            ("D", "ELITE", 8),
            ("E", "ELITE", 8),
            ("F", "ELITE", 8),
            ("G", "CLASSIC", 8),
            ("H", "CLASSIC", 8),
            ("I", "CLASSIC", 8),
            ("J", "CLASSIC", 8),
            ("K", "CLASSIC", 8),
            ("L", "CLASSIC", 8),
        ]

        active_movies = list(movies)

        for scr_idx, screen in enumerate(screens):
            scr_id = screen["screen_id"]
            scr_type = screen["screen_type"]

            p_classic, p_elite, p_recliner = pricing_by_type.get(scr_type, (150.0, 220.0, 300.0))

            # Rotate through movies so all 5 industries are represented across screens
            m1 = active_movies[scr_idx % len(active_movies)]
            m2 = active_movies[(scr_idx + 1) % len(active_movies)]

            for d_idx, d_str in enumerate(dates):
                # 2 shows for m1, 2 shows for m2
                show_configs = [
                    (m1["id"], time_slots[0]),
                    (m1["id"], time_slots[2]),
                    (m2["id"], time_slots[1]),
                    (m2["id"], time_slots[3]),
                ]

                for m_id, t_slot in show_configs:
                    cursor.execute("""
                        INSERT INTO shows (
                            movie_id, screen_id, show_date, show_time,
                            price_classic, price_elite, price_recliner,
                            price_standard, price_premium, total_seats
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 96);
                    """, (
                        m_id, scr_id, d_str, t_slot,
                        p_classic, p_elite, p_recliner,
                        p_classic, p_elite
                    ))
                    show_id = cursor.lastrowid

                    # Populate seats inventory
                    seat_batch = []
                    for r_letter, tier_name, count in rows_layout:
                        tier_price = p_recliner if tier_name == "RECLINER" else (p_elite if tier_name == "ELITE" else p_classic)
                        for num in range(1, count + 1):
                            seat_batch.append((show_id, f"{r_letter}{num}", tier_name, tier_price, "AVAILABLE"))

                    cursor.executemany("""
                        INSERT INTO show_seats (show_id, seat_number, tier, price, status)
                        VALUES (?, ?, ?, ?, ?);
                    """, seat_batch)

    def _ensure_demo_shows(self, conn: sqlite3.Connection) -> None:
        """Finds any movies in the catalogue lacking shows and generates demo shows for them."""
        cursor = conn.cursor()
        cursor.execute("""
            SELECT m.id, m.title FROM movies m
            WHERE NOT EXISTS (SELECT 1 FROM shows s WHERE s.movie_id = m.id);
        """)
        unconfigured = cursor.fetchall()
        if not unconfigured:
            return

        cursor.execute("SELECT id, screen_type FROM screens LIMIT 6;")
        screens = cursor.fetchall()
        if not screens:
            return

        today = datetime.now()
        dates = [(today + timedelta(days=i)).strftime("%Y-%m-%d") for i in range(4)]
        time_slots = ["11:00 AM", "03:30 PM", "07:15 PM"]
        rows_layout = [
            ("A", "RECLINER", 8),
            ("B", "RECLINER", 8),
            ("C", "ELITE", 8),
            ("D", "ELITE", 8),
            ("E", "ELITE", 8),
            ("F", "ELITE", 8),
            ("G", "CLASSIC", 8),
            ("H", "CLASSIC", 8),
            ("I", "CLASSIC", 8),
            ("J", "CLASSIC", 8),
            ("K", "CLASSIC", 8),
            ("L", "CLASSIC", 8),
        ]
        for m in unconfigured:
            m_id = m["id"]
            for scr in screens:
                scr_id = scr["id"]
                p_classic = 150.0
                p_elite = 220.0
                p_recliner = 300.0
                for d_str in dates:
                    for t_slot in [time_slots[0], time_slots[2]]:
                        cursor.execute("""
                            INSERT INTO shows (
                                movie_id, screen_id, show_date, show_time,
                                price_classic, price_elite, price_recliner,
                                price_standard, price_premium, total_seats
                            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 96);
                        """, (m_id, scr_id, d_str, t_slot, p_classic, p_elite, p_recliner, p_classic, p_elite))
                        show_id = cursor.lastrowid
                        seat_batch = []
                        for r_letter, tier_name, count in rows_layout:
                            tier_price = p_recliner if tier_name == "RECLINER" else (p_elite if tier_name == "ELITE" else p_classic)
                            for num in range(1, count + 1):
                                seat_batch.append((show_id, f"{r_letter}{num}", tier_name, tier_price, "AVAILABLE"))
                        cursor.executemany("""
                            INSERT INTO show_seats (show_id, seat_number, tier, price, status)
                            VALUES (?, ?, ?, ?, ?);
                        """, seat_batch)

    def generate_demo_shows_for_movie(self, movie_id: int, city_name: Optional[str] = None) -> int:
        """
        Dynamically generates demonstration showtimes and seat inventory (Rows A-L)
        for a specific movie across screens and upcoming dates.
        Works for ANY movie added to the catalogue.
        Returns the number of shows created.
        """
        conn = self.get_connection()
        try:
            with conn:
                cursor = conn.cursor()
                cursor.execute("SELECT id, title FROM movies WHERE id = ?;", (movie_id,))
                movie = cursor.fetchone()
                if not movie:
                    raise DatabaseError(f"Movie with ID {movie_id} does not exist.")

                # Find candidate screens
                if city_name:
                    cursor.execute("""
                        SELECT s.id as screen_id, s.screen_name, s.screen_type, s.theatre_id,
                               t.name as theatre_name, c.name as city_name
                        FROM screens s
                        JOIN theatres t ON s.theatre_id = t.id
                        JOIN cities c ON t.city_id = c.id
                        WHERE LOWER(c.name) = LOWER(?);
                    """, (city_name.strip(),))
                    screens = cursor.fetchall()
                else:
                    screens = []

                if not screens:
                    cursor.execute("""
                        SELECT s.id as screen_id, s.screen_name, s.screen_type, s.theatre_id,
                               t.name as theatre_name, c.name as city_name
                        FROM screens s
                        JOIN theatres t ON s.theatre_id = t.id
                        JOIN cities c ON t.city_id = c.id;
                    """)
                    screens = cursor.fetchall()

                if not screens:
                    return 0

                today = datetime.now()
                dates = [(today + timedelta(days=i)).strftime("%Y-%m-%d") for i in range(4)]
                pricing_by_type = {
                    "IMAX Laser 3D": (180.0, 260.0, 360.0),
                    "Dolby Atmos 4K": (150.0, 220.0, 300.0),
                    "Luxe Cinema Lounge": (200.0, 280.0, 380.0),
                    "Standard": (140.0, 200.0, 280.0)
                }
                time_slots = ["10:30 AM", "02:15 PM", "06:45 PM", "10:00 PM"]
                rows_layout = [
                    ("A", "RECLINER", 8),
                    ("B", "RECLINER", 8),
                    ("C", "ELITE", 8),
                    ("D", "ELITE", 8),
                    ("E", "ELITE", 8),
                    ("F", "ELITE", 8),
                    ("G", "CLASSIC", 8),
                    ("H", "CLASSIC", 8),
                    ("I", "CLASSIC", 8),
                    ("J", "CLASSIC", 8),
                    ("K", "CLASSIC", 8),
                    ("L", "CLASSIC", 8),
                ]

                created_shows_count = 0
                selected_screens = screens[:min(len(screens), 6)]

                for screen in selected_screens:
                    scr_id = screen["screen_id"]
                    scr_type = screen["screen_type"]
                    p_classic, p_elite, p_recliner = pricing_by_type.get(scr_type, (150.0, 220.0, 300.0))

                    for d_str in dates:
                        for t_slot in [time_slots[1], time_slots[2]]:
                            cursor.execute("""
                                SELECT id FROM shows
                                WHERE movie_id = ? AND screen_id = ? AND show_date = ? AND show_time = ?;
                            """, (movie_id, scr_id, d_str, t_slot))
                            if cursor.fetchone():
                                continue

                            cursor.execute("""
                                INSERT INTO shows (
                                    movie_id, screen_id, show_date, show_time,
                                    price_classic, price_elite, price_recliner,
                                    price_standard, price_premium, total_seats
                                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 96);
                            """, (
                                movie_id, scr_id, d_str, t_slot,
                                p_classic, p_elite, p_recliner,
                                p_classic, p_elite
                            ))
                            show_id = cursor.lastrowid
                            created_shows_count += 1

                            seat_batch = []
                            for r_letter, tier_name, count in rows_layout:
                                tier_price = p_recliner if tier_name == "RECLINER" else (p_elite if tier_name == "ELITE" else p_classic)
                                for num in range(1, count + 1):
                                    seat_batch.append((show_id, f"{r_letter}{num}", tier_name, tier_price, "AVAILABLE"))

                            cursor.executemany("""
                                INSERT INTO show_seats (show_id, seat_number, tier, price, status)
                                VALUES (?, ?, ?, ?, ?);
                            """, seat_batch)

                return created_shows_count
        finally:
            conn.close()

    # =========================================================================
    # CITY & THEATRE HIERARCHY METHODS
    # =========================================================================
    def get_cities(self) -> List[City]:
        """Fetch all supported cities."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM cities WHERE is_active = 1 ORDER BY id ASC;")
            return [City(id=row["id"], name=row["name"], state=row["state"], is_active=bool(row["is_active"])) for row in cursor.fetchall()]

    def get_theatres_by_city(self, city_name_or_id: Any) -> List[Theatre]:
        """Fetch all theatres located in the given city."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            if isinstance(city_name_or_id, int) or (isinstance(city_name_or_id, str) and str(city_name_or_id).isdigit()):
                cursor.execute("""
                    SELECT t.*, c.name as city_name
                    FROM theatres t
                    JOIN cities c ON t.city_id = c.id
                    WHERE t.city_id = ?
                    ORDER BY t.name ASC;
                """, (int(city_name_or_id),))
            else:
                cursor.execute("""
                    SELECT t.*, c.name as city_name
                    FROM theatres t
                    JOIN cities c ON t.city_id = c.id
                    WHERE LOWER(c.name) = LOWER(?)
                    ORDER BY t.name ASC;
                """, (str(city_name_or_id).strip(),))

            rows = cursor.fetchall()
            return [
                Theatre(
                    id=r["id"],
                    city_id=r["city_id"],
                    name=r["name"],
                    location=r["location"],
                    address=r["address"] or "",
                    city_name=r["city_name"]
                )
                for r in rows
            ]

    def get_screens_by_theatre(self, theatre_id: int) -> List[Screen]:
        """Fetch all screens inside a theatre."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT s.*, t.name as theatre_name
                FROM screens s
                JOIN theatres t ON s.theatre_id = t.id
                WHERE s.theatre_id = ?
                ORDER BY s.id ASC;
            """, (theatre_id,))
            return [
                Screen(
                    id=r["id"],
                    theatre_id=r["theatre_id"],
                    screen_name=r["screen_name"],
                    screen_type=r["screen_type"],
                    total_seats=r["total_seats"],
                    rows_count=r["rows_count"],
                    seats_per_row=r["seats_per_row"],
                    theatre_name=r["theatre_name"]
                )
                for r in cursor.fetchall()
            ]

    def _row_to_movie(self, row: sqlite3.Row) -> Movie:
        """Converts an SQLite row to a Movie dataclass instance."""
        keys = row.keys()
        return Movie(
            id=row["id"],
            title=row["title"],
            genre=row["genre"],
            duration=row["duration"],
            rating=row["rating"],
            censor_rating=row["censor_rating"],
            language=row["language"],
            description=row["description"],
            director=row["director"],
            cast=row["cast"],
            poster_path=row["poster_path"],
            banner_color=row["banner_color"],
            industry=row["industry"] if "industry" in keys else "Indian Cinema",
            release_year=row["release_year"] if "release_year" in keys else 2024,
            vote_count=row["vote_count"] if "vote_count" in keys else "50K",
            is_upcoming=bool(row["is_upcoming"]) if "is_upcoming" in keys else False
        )

    def get_all_movies(
        self,
        search_query: str = "",
        genre: str = "All",
        language: str = "All",
        category: str = "All",
        city_name: Optional[str] = None
    ) -> List[Movie]:
        """Fetch all movies with optional title search, genre, language, category, and city filtering."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            query = "SELECT * FROM movies WHERE 1=1"
            params: List[Any] = []

            if search_query.strip():
                query += " AND (LOWER(title) LIKE ? OR LOWER(description) LIKE ? OR LOWER([cast]) LIKE ? OR LOWER(director) LIKE ? OR LOWER(industry) LIKE ?)"
                term = f"%{search_query.strip().lower()}%"
                params.extend([term, term, term, term, term])

            if genre and genre != "All":
                query += " AND LOWER(genre) LIKE ?"
                params.append(f"%{genre.strip().lower()}%")

            if language and language != "All":
                query += " AND LOWER(language) LIKE ?"
                params.append(f"%{language.strip().lower()}%")

            if category and category != "All":
                if category == "Upcoming":
                    query += " AND is_upcoming = 1"
                elif category == "Now Showing":
                    query += " AND is_upcoming = 0"

            query += " ORDER BY is_upcoming ASC, rating DESC, title ASC;"
            cursor.execute(query, params)
            rows = cursor.fetchall()

            return [self._row_to_movie(row) for row in rows]

    def get_movie_by_id(self, movie_id: int) -> Optional[Movie]:
        """Fetch a single movie by its primary key ID."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM movies WHERE id = ?;", (movie_id,))
            row = cursor.fetchone()
            if not row:
                return None
            return self._row_to_movie(row)

    def get_distinct_genres(self) -> List[str]:
        """Extract a distinct list of genres for filter pills."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT DISTINCT genre FROM movies;")
            rows = cursor.fetchall()
            genres_set = set(["All"])
            for r in rows:
                for g in r["genre"].split("/"):
                    genres_set.add(g.strip())
            return sorted(list(genres_set))

    def get_show_dates_for_movie_and_city(self, movie_id: int, city_name: Optional[str] = None) -> List[str]:
        """Return unique show dates available for a movie in a specific city."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            if city_name:
                cursor.execute("""
                    SELECT DISTINCT s.show_date
                    FROM shows s
                    JOIN screens scr ON s.screen_id = scr.id
                    JOIN theatres t ON scr.theatre_id = t.id
                    JOIN cities c ON t.city_id = c.id
                    WHERE s.movie_id = ? AND LOWER(c.name) = LOWER(?)
                    ORDER BY s.show_date ASC;
                """, (movie_id, city_name.strip()))
            else:
                cursor.execute("""
                    SELECT DISTINCT show_date FROM shows
                    WHERE movie_id = ?
                    ORDER BY show_date ASC;
                """, (movie_id,))
            return [row["show_date"] for row in cursor.fetchall()]

    def get_show_dates_for_movie(self, movie_id: int) -> List[str]:
        """Alias for backward compatibility."""
        return self.get_show_dates_for_movie_and_city(movie_id)

    def get_shows_grouped_by_theatre(
        self,
        movie_id: int,
        city_name: Optional[str] = None,
        show_date: Optional[str] = None
    ) -> Dict[str, Dict[str, Any]]:
        """
        Returns showtimes grouped by Theatre and Screen.
        Structure:
        {
            "theatre_name": {
                "theatre": Theatre object,
                "screens": {
                    "screen_name": [Show1, Show2, ...]
                }
            }
        }
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            query = """
                SELECT s.*,
                       scr.screen_name as scr_name, scr.screen_type,
                       t.id as theatre_id, t.name as theatre_name, t.location as theatre_loc, t.address as theatre_addr,
                       c.id as city_id, c.name as city_name,
                       m.title as movie_title, m.genre as movie_genre, m.duration as movie_duration, m.language as movie_language
                FROM shows s
                JOIN screens scr ON s.screen_id = scr.id
                JOIN theatres t ON scr.theatre_id = t.id
                JOIN cities c ON t.city_id = c.id
                JOIN movies m ON s.movie_id = m.id
                WHERE s.movie_id = ?
            """
            params: List[Any] = [movie_id]

            if city_name:
                query += " AND LOWER(c.name) = LOWER(?)"
                params.append(city_name.strip())

            if show_date:
                query += " AND s.show_date = ?"
                params.append(show_date)

            query += " ORDER BY t.name ASC, scr.screen_name ASC, s.show_time ASC;"
            cursor.execute(query, params)
            rows = cursor.fetchall()

            theatres_map: Dict[str, Dict[str, Any]] = {}
            for r in rows:
                t_name = r["theatre_name"]
                if t_name not in theatres_map:
                    theatres_map[t_name] = {
                        "theatre": Theatre(
                            id=r["theatre_id"],
                            city_id=r["city_id"],
                            name=r["theatre_name"],
                            location=r["theatre_loc"],
                            address=r["theatre_addr"] or "",
                            city_name=r["city_name"]
                        ),
                        "screens": {}
                    }

                scr_label = f"{r['scr_name']} ({r['screen_type']})"
                if scr_label not in theatres_map[t_name]["screens"]:
                    theatres_map[t_name]["screens"][scr_label] = []

                p_classic = r["price_classic"] if "price_classic" in r.keys() else r["price_standard"]
                p_elite = r["price_elite"] if "price_elite" in r.keys() else r["price_premium"]
                p_recliner = r["price_recliner"]

                show_obj = Show(
                    id=r["id"],
                    movie_id=r["movie_id"],
                    screen_id=r["screen_id"],
                    theatre_id=r["theatre_id"],
                    screen_name=r["scr_name"],
                    theatre_name=r["theatre_name"],
                    city_name=r["city_name"],
                    screen_type=r["screen_type"],
                    show_date=r["show_date"],
                    show_time=r["show_time"],
                    price_classic=p_classic,
                    price_elite=p_elite,
                    price_recliner=p_recliner,
                    price_standard=p_classic,
                    price_premium=p_elite,
                    total_seats=r["total_seats"],
                    movie_title=r["movie_title"],
                    movie_genre=r["movie_genre"],
                    movie_duration=r["movie_duration"],
                    movie_language=r["movie_language"]
                )
                theatres_map[t_name]["screens"][scr_label].append(show_obj)

            return theatres_map

    def get_shows_for_movie(
        self,
        movie_id: int,
        show_date: Optional[str] = None,
        city_name: Optional[str] = None
    ) -> List[Show]:
        """Fetch all shows for a movie with full relational screen and theatre context."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            query = """
                SELECT s.*,
                       scr.screen_name as scr_name, scr.screen_type,
                       t.id as theatre_id, t.name as theatre_name,
                       c.name as city_name,
                       m.title as movie_title, m.genre as movie_genre, m.duration as movie_duration, m.language as movie_language
                FROM shows s
                LEFT JOIN screens scr ON s.screen_id = scr.id
                LEFT JOIN theatres t ON scr.theatre_id = t.id
                LEFT JOIN cities c ON t.city_id = c.id
                JOIN movies m ON s.movie_id = m.id
                WHERE s.movie_id = ?
            """
            params: List[Any] = [movie_id]

            if city_name:
                query += " AND LOWER(c.name) = LOWER(?)"
                params.append(city_name.strip())

            if show_date:
                query += " AND s.show_date = ?"
                params.append(show_date)

            query += " ORDER BY s.show_date ASC, s.show_time ASC;"
            cursor.execute(query, params)
            rows = cursor.fetchall()

            return [
                Show(
                    id=r["id"],
                    movie_id=r["movie_id"],
                    screen_id=r["screen_id"],
                    theatre_id=r["theatre_id"],
                    screen_name=r["scr_name"] or "Audi 1",
                    theatre_name=r["theatre_name"] or "CineBook Multiplex",
                    city_name=r["city_name"] or "Chennai",
                    screen_type=r["screen_type"] or "Standard",
                    show_date=r["show_date"],
                    show_time=r["show_time"],
                    price_classic=r["price_classic"] if "price_classic" in r.keys() else r["price_standard"],
                    price_elite=r["price_elite"] if "price_elite" in r.keys() else r["price_premium"],
                    price_recliner=r["price_recliner"],
                    price_standard=r["price_standard"],
                    price_premium=r["price_premium"],
                    total_seats=r["total_seats"],
                    movie_title=r["movie_title"],
                    movie_genre=r["movie_genre"],
                    movie_duration=r["movie_duration"],
                    movie_language=r["movie_language"]
                )
                for r in rows
            ]

    def get_show_by_id(self, show_id: int) -> Optional[Show]:
        """Fetch a specific screening show by ID with full theatre and screen metadata."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT s.*,
                       scr.screen_name as scr_name, scr.screen_type,
                       t.id as theatre_id, t.name as theatre_name,
                       c.name as city_name,
                       m.title as movie_title, m.genre as movie_genre, m.duration as movie_duration, m.language as movie_language
                FROM shows s
                LEFT JOIN screens scr ON s.screen_id = scr.id
                LEFT JOIN theatres t ON scr.theatre_id = t.id
                LEFT JOIN cities c ON t.city_id = c.id
                JOIN movies m ON s.movie_id = m.id
                WHERE s.id = ?;
            """, (show_id,))
            r = cursor.fetchone()
            if not r:
                return None
            return Show(
                id=r["id"],
                movie_id=r["movie_id"],
                screen_id=r["screen_id"],
                theatre_id=r["theatre_id"],
                screen_name=r["scr_name"] or "Audi 1",
                theatre_name=r["theatre_name"] or "CineBook Multiplex",
                city_name=r["city_name"] or "Chennai",
                screen_type=r["screen_type"] or "Standard",
                show_date=r["show_date"],
                show_time=r["show_time"],
                price_classic=r["price_classic"] if "price_classic" in r.keys() else r["price_standard"],
                price_elite=r["price_elite"] if "price_elite" in r.keys() else r["price_premium"],
                price_recliner=r["price_recliner"],
                price_standard=r["price_standard"],
                price_premium=r["price_premium"],
                total_seats=r["total_seats"],
                movie_title=r["movie_title"],
                movie_genre=r["movie_genre"],
                movie_duration=r["movie_duration"],
                movie_language=r["movie_language"]
            )

    def get_sibling_shows_for_date(self, show_id: int) -> List[Show]:
        """Fetches other showtimes for the same movie, theatre, and date (used for quick-switching in SeatView)."""
        curr = self.get_show_by_id(show_id)
        if not curr:
            return []
        with self.get_connection() as conn:
            cursor = conn.cursor()
            if curr.theatre_id:
                cursor.execute("""
                    SELECT s.*,
                           scr.screen_name as scr_name, scr.screen_type,
                           t.id as theatre_id, t.name as theatre_name,
                           c.name as city_name,
                           m.title as movie_title, m.genre as movie_genre, m.duration as movie_duration, m.language as movie_language
                    FROM shows s
                    LEFT JOIN screens scr ON s.screen_id = scr.id
                    LEFT JOIN theatres t ON scr.theatre_id = t.id
                    LEFT JOIN cities c ON t.city_id = c.id
                    JOIN movies m ON s.movie_id = m.id
                    WHERE s.movie_id = ? AND t.id = ? AND s.show_date = ?
                    ORDER BY s.show_time ASC;
                """, (curr.movie_id, curr.theatre_id, curr.show_date))
            else:
                cursor.execute("""
                    SELECT s.*,
                           scr.screen_name as scr_name, scr.screen_type,
                           t.id as theatre_id, t.name as theatre_name,
                           c.name as city_name,
                           m.title as movie_title, m.genre as movie_genre, m.duration as movie_duration, m.language as movie_language
                    FROM shows s
                    LEFT JOIN screens scr ON s.screen_id = scr.id
                    LEFT JOIN theatres t ON scr.theatre_id = t.id
                    LEFT JOIN cities c ON t.city_id = c.id
                    JOIN movies m ON s.movie_id = m.id
                    WHERE s.movie_id = ? AND s.show_date = ?
                    ORDER BY s.show_time ASC;
                """, (curr.movie_id, curr.show_date))
            rows = cursor.fetchall()
            return [
                Show(
                    id=r["id"],
                    movie_id=r["movie_id"],
                    screen_id=r["screen_id"],
                    theatre_id=r["theatre_id"],
                    screen_name=r["scr_name"] or "Audi 1",
                    theatre_name=r["theatre_name"] or "CineBook Multiplex",
                    city_name=r["city_name"] or "Chennai",
                    screen_type=r["screen_type"] or "Standard",
                    show_date=r["show_date"],
                    show_time=r["show_time"],
                    price_classic=r["price_classic"] if "price_classic" in r.keys() else r["price_standard"],
                    price_elite=r["price_elite"] if "price_elite" in r.keys() else r["price_premium"],
                    price_recliner=r["price_recliner"],
                    price_standard=r["price_standard"],
                    price_premium=r["price_premium"],
                    total_seats=r["total_seats"],
                    movie_title=r["movie_title"],
                    movie_genre=r["movie_genre"],
                    movie_duration=r["movie_duration"],
                    movie_language=r["movie_language"]
                )
                for r in rows
            ]

    def _seed_seats_for_single_show(self, conn: sqlite3.Connection, show_id: int) -> None:
        """Helper to ensure all 96 seats (Rows A-L) exist in show_seats for a show."""
        cursor = conn.cursor()
        cursor.execute("SELECT price_classic, price_elite, price_recliner FROM shows WHERE id = ?;", (show_id,))
        show_row = cursor.fetchone()
        if not show_row:
            return
        p_classic = show_row["price_classic"] or 150.0
        p_elite = show_row["price_elite"] or 220.0
        p_recliner = show_row["price_recliner"] or 300.0

        rows_layout = [
            ("A", "RECLINER", 8),
            ("B", "RECLINER", 8),
            ("C", "ELITE", 8),
            ("D", "ELITE", 8),
            ("E", "ELITE", 8),
            ("F", "ELITE", 8),
            ("G", "CLASSIC", 8),
            ("H", "CLASSIC", 8),
            ("I", "CLASSIC", 8),
            ("J", "CLASSIC", 8),
            ("K", "CLASSIC", 8),
            ("L", "CLASSIC", 8),
        ]
        seat_batch = []
        for r_letter, tier_name, count in rows_layout:
            tier_price = p_recliner if tier_name == "RECLINER" else (p_elite if tier_name == "ELITE" else p_classic)
            for num in range(1, count + 1):
                seat_batch.append((show_id, f"{r_letter}{num}", tier_name, tier_price, "AVAILABLE"))

        cursor.executemany("""
            INSERT OR IGNORE INTO show_seats (show_id, seat_number, tier, price, status)
            VALUES (?, ?, ?, ?, ?);
        """, seat_batch)
        conn.commit()

    def get_seats_for_show(self, show_id: int) -> List[Seat]:
        """Fetch current seat statuses for a given show, including prime bestseller tags."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT ss.*, scr.screen_name, t.name as theatre_name
                FROM show_seats ss
                LEFT JOIN shows s ON ss.show_id = s.id
                LEFT JOIN screens scr ON s.screen_id = scr.id
                LEFT JOIN theatres t ON scr.theatre_id = t.id
                WHERE ss.show_id = ?
                ORDER BY SUBSTR(ss.seat_number, 1, 1) ASC, CAST(SUBSTR(ss.seat_number, 2) AS INTEGER) ASC;
            """, (show_id,))
            rows = cursor.fetchall()
            if not rows:
                self._seed_seats_for_single_show(conn, show_id)
                cursor.execute("""
                    SELECT ss.*, scr.screen_name, t.name as theatre_name
                    FROM show_seats ss
                    LEFT JOIN shows s ON ss.show_id = s.id
                    LEFT JOIN screens scr ON s.screen_id = scr.id
                    LEFT JOIN theatres t ON scr.theatre_id = t.id
                    WHERE ss.show_id = ?
                    ORDER BY SUBSTR(ss.seat_number, 1, 1) ASC, CAST(SUBSTR(ss.seat_number, 2) AS INTEGER) ASC;
                """, (show_id,))
                rows = cursor.fetchall()

            seats = []
            for row in rows:
                code = row["seat_number"]
                row_char = code[0]
                num = int(code[1:]) if code[1:].isdigit() else 0
                is_best = (row_char in ("D", "E") and num in (3, 4, 5, 6))

                seats.append(
                    Seat(
                        id=row["id"],
                        show_id=row["show_id"],
                        seat_number=code,
                        tier=row["tier"],
                        price=row["price"],
                        status=row["status"],
                        booking_id=row["booking_id"],
                        theatre_name=row["theatre_name"],
                        screen_name=row["screen_name"],
                        is_bestseller=is_best
                    )
                )
            return seats


    def generate_booking_reference(self) -> str:
        """Generate a clean, professional, unique booking reference string."""
        chars = string.ascii_uppercase + string.digits
        token = "".join(random.choices(chars, k=6))
        year = datetime.now().year
        return f"CB-{year}-{token}"

    def create_booking(
        self,
        show_id: int,
        customer_name: str,
        customer_phone: str,
        customer_email: Optional[str],
        seat_numbers: List[str],
        convenience_fee: float = 25.0
    ) -> Booking:
        """
        Atomically reserve seats and create a new booking using SQLite transactions.
        Guarantees zero double-booking and full ACID rollback on contention.
        """
        if not seat_numbers:
            raise ValueError("At least one seat must be selected for booking.")

        conn = self.get_connection()
        try:
            with conn:
                cursor = conn.cursor()

                # Verify show exists
                cursor.execute("""
                    SELECT s.*, scr.screen_name as scr_name, t.name as theatre_name, c.name as city_name, m.title as movie_title
                    FROM shows s
                    LEFT JOIN screens scr ON s.screen_id = scr.id
                    LEFT JOIN theatres t ON scr.theatre_id = t.id
                    LEFT JOIN cities c ON t.city_id = c.id
                    JOIN movies m ON s.movie_id = m.id
                    WHERE s.id = ?;
                """, (show_id,))
                show_row = cursor.fetchone()
                if not show_row:
                    raise DatabaseError(f"Show ID {show_id} not found.")

                # Check seat availability
                placeholders = ",".join("?" for _ in seat_numbers)
                cursor.execute(f"""
                    SELECT id, seat_number, tier, price, status
                    FROM show_seats
                    WHERE show_id = ? AND seat_number IN ({placeholders});
                """, [show_id] + seat_numbers)
                found_seats = cursor.fetchall()

                found_dict = {row["seat_number"]: row for row in found_seats}

                # Verify all seats exist
                missing = [s for s in seat_numbers if s not in found_dict]
                if missing:
                    self._seed_seats_for_single_show(conn, show_id)
                    cursor.execute(f"""
                        SELECT id, seat_number, tier, price, status
                        FROM show_seats
                        WHERE show_id = ? AND seat_number IN ({placeholders});
                    """, [show_id] + seat_numbers)
                    found_seats = cursor.fetchall()
                    found_dict = {row["seat_number"]: row for row in found_seats}
                    missing = [s for s in seat_numbers if s not in found_dict]
                    if missing:
                        raise SeatUnavailableError(f"The following seat(s) do not exist: {', '.join(missing)}")


                # Verify all seats are AVAILABLE
                unavailable = [s for s, row in found_dict.items() if row["status"] != "AVAILABLE"]
                if unavailable:
                    raise SeatUnavailableError(
                        f"Seat(s) {', '.join(unavailable)} were just booked by another patron. "
                        "Please choose different seats."
                    )

                # Calculate subtotal
                subtotal = sum(found_dict[s]["price"] for s in seat_numbers)
                total_price = subtotal + convenience_fee
                created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

                booking_ref = self.generate_booking_reference()

                # Insert booking
                cursor.execute("""
                    INSERT INTO bookings (
                        booking_ref, show_id, customer_name, customer_phone, customer_email,
                        seat_count, subtotal, convenience_fee, total_price, booking_status, created_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'CONFIRMED', ?);
                """, (
                    booking_ref, show_id, customer_name.strip(), customer_phone.strip(),
                    customer_email.strip() if customer_email else None,
                    len(seat_numbers), subtotal, convenience_fee, total_price, created_at
                ))
                booking_id = cursor.lastrowid

                # Update seats and insert items
                for s_num in seat_numbers:
                    s_data = found_dict[s_num]
                    cursor.execute("""
                        INSERT INTO booking_seats (booking_id, seat_number, tier, price)
                        VALUES (?, ?, ?, ?);
                    """, (booking_id, s_num, s_data["tier"], s_data["price"]))

                    cursor.execute("""
                        UPDATE show_seats
                        SET status = 'BOOKED', booking_id = ?
                        WHERE show_id = ? AND seat_number = ?;
                    """, (booking_id, show_id, s_num))

                return Booking(
                    id=booking_id,
                    booking_ref=booking_ref,
                    show_id=show_id,
                    customer_name=customer_name.strip(),
                    customer_phone=customer_phone.strip(),
                    customer_email=customer_email.strip() if customer_email else None,
                    seat_count=len(seat_numbers),
                    subtotal=subtotal,
                    convenience_fee=convenience_fee,
                    total_price=total_price,
                    booking_status="CONFIRMED",
                    created_at=created_at,
                    cancelled_at=None,
                    movie_title=show_row["movie_title"],
                    show_date=show_row["show_date"],
                    show_time=show_row["show_time"],
                    screen_name=show_row["scr_name"] or "Audi 1",
                    theatre_name=show_row["theatre_name"] or "CineBook Multiplex",
                    city_name=show_row["city_name"] or "Chennai",
                    seats=seat_numbers
                )
        except Exception:
            raise

    def cancel_booking(self, booking_ref_or_id: Any) -> Booking:
        """
        Cancels a booking transactionally:
        Marks booking status as CANCELLED, sets cancelled_at timestamp,
        and releases all reserved seats back to AVAILABLE.
        """
        conn = self.get_connection()
        try:
            with conn:
                cursor = conn.cursor()

                # Find booking
                if isinstance(booking_ref_or_id, int) or (isinstance(booking_ref_or_id, str) and booking_ref_or_id.isdigit()):
                    cursor.execute("SELECT * FROM bookings WHERE id = ?;", (int(booking_ref_or_id),))
                else:
                    cursor.execute("SELECT * FROM bookings WHERE booking_ref = ?;", (str(booking_ref_or_id).strip(),))

                booking_row = cursor.fetchone()
                if not booking_row:
                    raise BookingNotFoundError(f"Booking '{booking_ref_or_id}' was not found.")

                if booking_row["booking_status"] == "CANCELLED":
                    raise DatabaseError(f"Booking '{booking_row['booking_ref']}' has already been cancelled.")

                booking_id = booking_row["id"]
                cancelled_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

                # Mark booking as CANCELLED
                cursor.execute("""
                    UPDATE bookings
                    SET booking_status = 'CANCELLED', cancelled_at = ?
                    WHERE id = ?;
                """, (cancelled_at, booking_id))

                # Release seats
                cursor.execute("""
                    UPDATE show_seats
                    SET status = 'AVAILABLE', booking_id = NULL
                    WHERE booking_id = ?;
                """, (booking_id,))

                # Fetch seats for return object
                cursor.execute("SELECT seat_number FROM booking_seats WHERE booking_id = ?;", (booking_id,))
                seats = [r["seat_number"] for r in cursor.fetchall()]

                return Booking(
                    id=booking_row["id"],
                    booking_ref=booking_row["booking_ref"],
                    show_id=booking_row["show_id"],
                    customer_name=booking_row["customer_name"],
                    customer_phone=booking_row["customer_phone"],
                    customer_email=booking_row["customer_email"],
                    seat_count=booking_row["seat_count"],
                    subtotal=booking_row["subtotal"],
                    convenience_fee=booking_row["convenience_fee"],
                    total_price=booking_row["total_price"],
                    booking_status="CANCELLED",
                    created_at=booking_row["created_at"],
                    cancelled_at=cancelled_at,
                    seats=seats
                )
        except Exception:
            raise

    def get_all_bookings(
        self,
        search_query: str = "",
        status: str = "ALL",
        search_term: Optional[str] = None,
        status_filter: Optional[str] = None
    ) -> List[Booking]:
        """Fetch all bookings with optional query and status filters."""
        q = search_term if search_term is not None else search_query
        s_filt = status_filter if status_filter is not None else status

        with self.get_connection() as conn:
            cursor = conn.cursor()
            query = """
                SELECT b.*,
                       s.show_date, s.show_time,
                       scr.screen_name as scr_name,
                       t.name as theatre_name,
                       c.name as city_name,
                       m.title AS movie_title
                FROM bookings b
                JOIN shows s ON b.show_id = s.id
                LEFT JOIN screens scr ON s.screen_id = scr.id
                LEFT JOIN theatres t ON scr.theatre_id = t.id
                LEFT JOIN cities c ON t.city_id = c.id
                JOIN movies m ON s.movie_id = m.id
                WHERE 1=1
            """
            params: List[Any] = []

            if q.strip():
                query += " AND (LOWER(b.booking_ref) LIKE ? OR LOWER(b.customer_name) LIKE ? OR LOWER(m.title) LIKE ?)"
                term = f"%{q.strip().lower()}%"
                params.extend([term, term, term])

            if s_filt and s_filt.upper() != "ALL":
                query += " AND b.booking_status = ?"
                params.append(s_filt.upper())

            query += " ORDER BY b.id DESC;"
            cursor.execute(query, params)
            rows = cursor.fetchall()

            bookings = []
            for r in rows:
                b_id = r["id"]
                cursor.execute("SELECT seat_number FROM booking_seats WHERE booking_id = ? ORDER BY seat_number ASC;", (b_id,))
                seats = [s_row["seat_number"] for s_row in cursor.fetchall()]

                bookings.append(
                    Booking(
                        id=r["id"],
                        booking_ref=r["booking_ref"],
                        show_id=r["show_id"],
                        customer_name=r["customer_name"],
                        customer_phone=r["customer_phone"],
                        customer_email=r["customer_email"],
                        seat_count=r["seat_count"],
                        subtotal=r["subtotal"],
                        convenience_fee=r["convenience_fee"],
                        total_price=r["total_price"],
                        booking_status=r["booking_status"],
                        created_at=r["created_at"],
                        cancelled_at=r["cancelled_at"],
                        movie_title=r["movie_title"],
                        show_date=r["show_date"],
                        show_time=r["show_time"],
                        screen_name=r["scr_name"] or "Audi 1",
                        theatre_name=r["theatre_name"] or "CineBook Multiplex",
                        city_name=r["city_name"] or "Chennai",
                        seats=seats
                    )
                )
            return bookings

    def get_booking_by_id(self, identifier: Any) -> Optional[Booking]:
        """Fetch booking details by integer ID or booking reference string."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            if isinstance(identifier, int) or (isinstance(identifier, str) and identifier.isdigit()):
                cursor.execute("""
                    SELECT b.*,
                           s.show_date, s.show_time,
                           scr.screen_name as scr_name,
                           t.name as theatre_name,
                           c.name as city_name,
                           m.title AS movie_title
                    FROM bookings b
                    JOIN shows s ON b.show_id = s.id
                    LEFT JOIN screens scr ON s.screen_id = scr.id
                    LEFT JOIN theatres t ON scr.theatre_id = t.id
                    LEFT JOIN cities c ON t.city_id = c.id
                    JOIN movies m ON s.movie_id = m.id
                    WHERE b.id = ?;
                """, (int(identifier),))
            else:
                cursor.execute("""
                    SELECT b.*,
                           s.show_date, s.show_time,
                           scr.screen_name as scr_name,
                           t.name as theatre_name,
                           c.name as city_name,
                           m.title AS movie_title
                    FROM bookings b
                    JOIN shows s ON b.show_id = s.id
                    LEFT JOIN screens scr ON s.screen_id = scr.id
                    LEFT JOIN theatres t ON scr.theatre_id = t.id
                    LEFT JOIN cities c ON t.city_id = c.id
                    JOIN movies m ON s.movie_id = m.id
                    WHERE b.booking_ref = ?;
                """, (str(identifier).strip(),))

            r = cursor.fetchone()
            if not r:
                return None

            b_id = r["id"]
            cursor.execute("SELECT seat_number FROM booking_seats WHERE booking_id = ? ORDER BY seat_number ASC;", (b_id,))
            seats = [s_row["seat_number"] for s_row in cursor.fetchall()]

            return Booking(
                id=r["id"],
                booking_ref=r["booking_ref"],
                show_id=r["show_id"],
                customer_name=r["customer_name"],
                customer_phone=r["customer_phone"],
                customer_email=r["customer_email"],
                seat_count=r["seat_count"],
                subtotal=r["subtotal"],
                convenience_fee=r["convenience_fee"],
                total_price=r["total_price"],
                booking_status=r["booking_status"],
                created_at=r["created_at"],
                cancelled_at=r["cancelled_at"],
                movie_title=r["movie_title"],
                show_date=r["show_date"],
                show_time=r["show_time"],
                screen_name=r["scr_name"] or "Audi 1",
                theatre_name=r["theatre_name"] or "CineBook Multiplex",
                city_name=r["city_name"] or "Chennai",
                seats=seats
            )

    # Backward-compatible alias
    get_booking_by_ref_or_id = get_booking_by_id

    def get_dashboard_stats(self) -> Dict[str, Any]:
        """Calculate live statistics for the CineBook Home & Admin dashboard."""
        with self.get_connection() as conn:
            cursor = conn.cursor()

            cursor.execute("SELECT COUNT(*) AS total_movies FROM movies;")
            total_movies = cursor.fetchone()["total_movies"]

            cursor.execute("SELECT COUNT(*) AS total_shows FROM shows;")
            total_shows = cursor.fetchone()["total_shows"]

            cursor.execute("SELECT COUNT(*) AS active_bookings FROM bookings WHERE booking_status = 'CONFIRMED';")
            active_bookings = cursor.fetchone()["active_bookings"]

            cursor.execute("SELECT IFNULL(SUM(total_price), 0.0) AS total_revenue FROM bookings WHERE booking_status = 'CONFIRMED';")
            total_revenue = cursor.fetchone()["total_revenue"]

            cursor.execute("SELECT COUNT(*) AS available_seats FROM show_seats WHERE status = 'AVAILABLE';")
            available_seats = cursor.fetchone()["available_seats"]

            cursor.execute("SELECT COUNT(*) AS total_theatres FROM theatres;")
            total_theatres = cursor.fetchone()["total_theatres"]

            cursor.execute("SELECT COUNT(*) AS total_cities FROM cities;")
            total_cities = cursor.fetchone()["total_cities"]

            return {
                "total_movies": total_movies,
                "total_shows": total_shows,
                "active_bookings": active_bookings,
                "total_revenue": total_revenue,
                "available_seats": available_seats,
                "total_theatres": total_theatres,
                "total_cities": total_cities
            }

    def update_show_prices(
        self,
        show_id: int,
        price_classic: float,
        price_elite: float,
        price_recliner: float
    ) -> bool:
        """Update ticket prices for a specific show and update unsold seat prices."""
        with self.get_connection() as conn:
            with conn:
                cursor = conn.cursor()
                cursor.execute("""
                    UPDATE shows
                    SET price_classic = ?, price_elite = ?, price_recliner = ?,
                        price_standard = ?, price_premium = ?
                    WHERE id = ?;
                """, (price_classic, price_elite, price_recliner, price_classic, price_elite, show_id))

                # Update unsold seat prices accordingly
                cursor.execute("""
                    UPDATE show_seats
                    SET price = ?
                    WHERE show_id = ? AND status = 'AVAILABLE' AND (tier = 'CLASSIC' OR tier = 'STANDARD');
                """, (price_classic, show_id))
                cursor.execute("""
                    UPDATE show_seats
                    SET price = ?
                    WHERE show_id = ? AND status = 'AVAILABLE' AND (tier = 'ELITE' OR tier = 'PREMIUM');
                """, (price_elite, show_id))
                cursor.execute("""
                    UPDATE show_seats
                    SET price = ?
                    WHERE show_id = ? AND status = 'AVAILABLE' AND tier = 'RECLINER';
                """, (price_recliner, show_id))
                return True

    def add_show(
        self,
        movie_id: int,
        screen_id: int,
        show_date: str,
        show_time: str,
        price_classic: float = 150.0,
        price_elite: float = 220.0,
        price_recliner: float = 300.0
    ) -> int:
        """Add a new show schedule and populate its Rows A–L seating inventory."""
        with self.get_connection() as conn:
            with conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO shows (
                        movie_id, screen_id, show_date, show_time,
                        price_classic, price_elite, price_recliner,
                        price_standard, price_premium, total_seats
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 96);
                """, (
                    movie_id, screen_id, show_date, show_time,
                    price_classic, price_elite, price_recliner,
                    price_classic, price_elite
                ))
                show_id = cursor.lastrowid

                # Generate Rows A–L
                rows_layout = [
                    ("A", "RECLINER", 8, price_recliner),
                    ("B", "RECLINER", 8, price_recliner),
                    ("C", "ELITE", 8, price_elite),
                    ("D", "ELITE", 8, price_elite),
                    ("E", "ELITE", 8, price_elite),
                    ("F", "ELITE", 8, price_elite),
                    ("G", "CLASSIC", 8, price_classic),
                    ("H", "CLASSIC", 8, price_classic),
                    ("I", "CLASSIC", 8, price_classic),
                    ("J", "CLASSIC", 8, price_classic),
                    ("K", "CLASSIC", 8, price_classic),
                    ("L", "CLASSIC", 8, price_classic),
                ]
                seat_inserts = []
                for row_letter, tier_name, count, p_val in rows_layout:
                    for num in range(1, count + 1):
                        seat_inserts.append((show_id, f"{row_letter}{num}", tier_name, p_val, "AVAILABLE"))

                cursor.executemany("""
                    INSERT INTO show_seats (show_id, seat_number, tier, price, status)
                    VALUES (?, ?, ?, ?, ?);
                """, seat_inserts)

                return show_id

