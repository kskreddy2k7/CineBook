"""
CineBook - Models Module
Data classes and domain models for Movie Ticket Booking System.
Supports complete multi-city & theatre hierarchy:
City → Theatre → Screen → Movie → Show → Seat → Booking.
"""

from dataclasses import dataclass, field
from typing import List, Optional
from datetime import datetime


@dataclass
class City:
    id: int
    name: str
    state: str
    is_active: bool = True


@dataclass
class Theatre:
    id: int
    city_id: int
    name: str
    location: str
    address: str = ""
    city_name: Optional[str] = None


@dataclass
class Screen:
    id: int
    theatre_id: int
    screen_name: str
    screen_type: str  # e.g., 'IMAX Laser 3D', 'Dolby Atmos 4K', 'Luxe Cinema Lounge'
    total_seats: int = 96
    rows_count: int = 12
    seats_per_row: int = 8
    theatre_name: Optional[str] = None


@dataclass
class Movie:
    id: int
    title: str
    genre: str
    duration: str
    rating: float
    censor_rating: str
    language: str
    description: str
    director: str
    cast: str
    poster_path: str
    banner_color: str = "#1E293B"
    industry: str = "Indian Cinema"
    release_year: int = 2024
    vote_count: str = "50K"
    is_upcoming: bool = False

    @property
    def rating_stars(self) -> str:
        """Return formatted rating string with star symbol."""
        if self.rating > 0:
            return f"★ {self.rating:.1f}/10"
        return "★ UPCOMING"

    @property
    def meta_display(self) -> str:
        """Compact metadata string: e.g. Telugu • U/A • 187 min"""
        parts = []
        if self.language:
            parts.append(self.language.split("/")[0].strip())
        if self.censor_rating:
            parts.append(self.censor_rating)
        if self.duration:
            parts.append(self.duration)
        return " • ".join(parts)


@dataclass
class Show:
    id: int
    movie_id: int
    screen_name: str = "Audi 1"
    show_date: str = ""  # YYYY-MM-DD
    show_time: str = ""  # e.g., '10:30 AM'
    price_classic: float = 150.0
    price_elite: float = 220.0
    price_recliner: float = 300.0
    price_standard: float = 150.0  # Backward-compatibility alias
    price_premium: float = 220.0   # Backward-compatibility alias
    total_seats: int = 96
    screen_id: Optional[int] = None
    theatre_id: Optional[int] = None
    theatre_name: Optional[str] = None
    city_name: Optional[str] = None
    screen_type: str = "Standard"
    movie_title: Optional[str] = None
    movie_genre: Optional[str] = None
    movie_duration: Optional[str] = None
    movie_language: Optional[str] = None

    def __post_init__(self):
        # Sync standard/premium with classic/elite if needed
        if self.price_classic and not self.price_standard:
            self.price_standard = self.price_classic
        elif self.price_standard and not self.price_classic:
            self.price_classic = self.price_standard

        if self.price_elite and not self.price_premium:
            self.price_premium = self.price_elite
        elif self.price_premium and not self.price_elite:
            self.price_elite = self.price_premium

    @property
    def formatted_datetime(self) -> str:
        """Formatted human readable date and time."""
        try:
            dt = datetime.strptime(self.show_date, "%Y-%m-%d")
            return f"{dt.strftime('%a, %d %b %Y')} at {self.show_time}"
        except Exception:
            return f"{self.show_date} at {self.show_time}"


@dataclass
class Seat:
    id: int
    show_id: int
    seat_number: str  # e.g., 'A1', 'C4', 'L8'
    tier: str         # 'RECLINER', 'ELITE', 'CLASSIC' (or 'PREMIUM', 'STANDARD')
    price: float
    status: str       # 'AVAILABLE', 'BOOKED'
    booking_id: Optional[int] = None
    theatre_name: Optional[str] = None
    screen_name: Optional[str] = None
    is_bestseller: bool = False

    @property
    def row(self) -> str:
        return self.seat_number[0] if self.seat_number else ""

    @property
    def number(self) -> int:
        try:
            return int(self.seat_number[1:])
        except ValueError:
            return 0


@dataclass
class BookingItem:
    seat_number: str
    tier: str
    price: float


@dataclass
class Booking:
    id: int
    booking_ref: str
    show_id: int
    customer_name: str
    customer_phone: str
    customer_email: Optional[str]
    seat_count: int
    subtotal: float
    convenience_fee: float
    total_price: float
    booking_status: str  # 'CONFIRMED', 'CANCELLED'
    created_at: str
    cancelled_at: Optional[str] = None
    movie_title: Optional[str] = None
    show_date: Optional[str] = None
    show_time: Optional[str] = None
    screen_name: Optional[str] = None
    theatre_name: Optional[str] = None
    city_name: Optional[str] = None
    seats: List[str] = field(default_factory=list)

    @property
    def seats_display(self) -> str:
        return ", ".join(self.seats) if self.seats else "N/A"

    @property
    def is_active(self) -> bool:
        return self.booking_status == "CONFIRMED"


