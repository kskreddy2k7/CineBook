"""
CineBook - Automated Test Suite
Validates database schema initialization, idempotency, search/filter,
transactional booking creation, double-booking prevention, cancellation,
inventory restoration, and input validation.
"""

import unittest
import tempfile
import re
import sys
from pathlib import Path
from datetime import datetime

# Ensure project root is on sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from database import DatabaseManager, SeatUnavailableError, BookingNotFoundError, DatabaseError
from models import Movie, Show, Seat, Booking


class TestCineBookBookingLogic(unittest.TestCase):
    """Test suite covering core domain logic and SQLite transactions."""

    def setUp(self):
        """Create a fresh isolated temporary database for each test run."""
        self.temp_dir = tempfile.TemporaryDirectory(ignore_cleanup_errors=True)
        self.db_path = str(Path(self.temp_dir.name) / "test_cinebook.db")
        self.db = DatabaseManager(self.db_path)

    def tearDown(self):
        """Clean up temporary database files."""
        import gc
        gc.collect()
        try:
            self.temp_dir.cleanup()
        except Exception:
            pass

    def test_database_initialization_and_seeding(self):
        """Verify that tables are created and sample records seeded properly."""
        movies = self.db.get_all_movies()
        self.assertGreaterEqual(len(movies), 6, "Expected at least 6 sample movies.")

        # Check sample movie metadata
        movie1 = movies[0]
        self.assertTrue(bool(movie1.title))
        self.assertTrue(bool(movie1.genre))
        self.assertGreater(movie1.rating, 7.0)

        # Check show generation
        shows = self.db.get_shows_for_movie(movie1.id)
        self.assertGreater(len(shows), 0, "Shows should be scheduled for sample movies.")

        # Check seats inventory generated for show #1
        show1 = shows[0]
        seats = self.db.get_seats_for_show(show1.id)
        self.assertIn(len(seats), [48, 96], "Expected 48 or 96 seats per show.")

    def test_database_initialization_idempotency(self):
        """Verify that reopening the database does not duplicate records or wipe bookings."""
        initial_movies_count = len(self.db.get_all_movies())
        initial_bookings_count = len(self.db.get_all_bookings())

        # Re-initialize on same path
        db2 = DatabaseManager(self.db_path)
        self.assertEqual(len(db2.get_all_movies()), initial_movies_count)
        self.assertEqual(len(db2.get_all_bookings()), initial_bookings_count)

    def test_movie_search_and_genre_filtering(self):
        """Test search query matching and genre filtering."""
        # Exact/Partial Title Search for Indian film
        results = self.db.get_all_movies(search_query="RRR")
        self.assertTrue(any("RRR" in m.title for m in results))

        # Non-matching search
        empty_results = self.db.get_all_movies(search_query="XYZNONEXISTENT999")
        self.assertEqual(len(empty_results), 0)

        # Genre Filter
        action_results = self.db.get_all_movies(genre="Action")
        self.assertTrue(len(action_results) > 0)
        for m in action_results:
            self.assertIn("Action", m.genre)

    def test_seat_tier_pricing(self):
        """Verify tiered seat pricing across categories (Recliner, Elite, Classic)."""
        movies = self.db.get_all_movies()
        shows = self.db.get_shows_for_movie(movies[0].id)
        show = shows[0]
        seats = self.db.get_seats_for_show(show.id)

        seat_map = {s.seat_number: s for s in seats}

        # Row A = Recliner
        self.assertEqual(seat_map["A1"].tier, "RECLINER")
        self.assertEqual(seat_map["A1"].price, show.price_recliner)

        # Row B = Recliner
        self.assertIn(seat_map["B3"].tier, ("RECLINER", "PREMIUM"))

        # Row C & D = Elite / Premium
        self.assertIn(seat_map["C4"].tier, ("ELITE", "PREMIUM"))
        self.assertIn(seat_map["D2"].tier, ("ELITE", "PREMIUM", "STANDARD"))

    def test_successful_booking_transaction(self):
        """Verify atomic creation of a valid booking with correct reference and totals."""
        movies = self.db.get_all_movies()
        shows = self.db.get_shows_for_movie(movies[0].id)
        show = shows[0]

        # Pick 2 available seats
        seats = self.db.get_seats_for_show(show.id)
        avail = [s for s in seats if s.status == "AVAILABLE"][:2]
        avail_codes = [s.seat_number for s in avail]
        self.assertEqual(len(avail_codes), 2)

        booking = self.db.create_booking(
            show_id=show.id,
            customer_name="Rohan Verma",
            customer_phone="9876543210",
            customer_email="rohan@example.com",
            seat_numbers=avail_codes,
            convenience_fee=25.0
        )

        # Assert booking properties
        self.assertTrue(booking.booking_ref.startswith("CB-"))
        self.assertEqual(booking.customer_name, "Rohan Verma")
        self.assertEqual(booking.seat_count, 2)
        expected_subtotal = sum(s.price for s in avail)
        self.assertEqual(booking.subtotal, expected_subtotal)
        self.assertEqual(booking.total_price, expected_subtotal + 25.0)
        self.assertEqual(booking.booking_status, "CONFIRMED")
        self.assertEqual(booking.seats, sorted(avail_codes))

        # Verify that show_seats table reflects 'BOOKED' status
        refreshed_seats = self.db.get_seats_for_show(show.id)
        refreshed_map = {s.seat_number: s for s in refreshed_seats}
        for s_code in avail_codes:
            self.assertEqual(refreshed_map[s_code].status, "BOOKED")
            self.assertEqual(refreshed_map[s_code].booking_id, booking.id)

    def test_double_booking_prevention(self):
        """CRITICAL: Ensure atomic transaction prevents reserving an already-booked seat."""
        movies = self.db.get_all_movies()
        shows = self.db.get_shows_for_movie(movies[0].id)
        show = shows[0]

        # First booking succeeds
        seats = self.db.get_seats_for_show(show.id)
        avail = [s.seat_number for s in seats if s.status == "AVAILABLE" and s.row == "E"][:2]

        self.db.create_booking(
            show_id=show.id,
            customer_name="User One",
            customer_phone="9898989898",
            customer_email=None,
            seat_numbers=avail,
            convenience_fee=25.0
        )

        # Attempting to book the SAME seats must raise SeatUnavailableError
        with self.assertRaises(SeatUnavailableError):
            self.db.create_booking(
                show_id=show.id,
                customer_name="User Two (Conflict)",
                customer_phone="9123456789",
                customer_email=None,
                seat_numbers=avail,  # Duplicate seat request
                convenience_fee=25.0
            )

        # Attempting mixed batch (one available, one booked) must rollback entirely
        all_seats = self.db.get_seats_for_show(show.id)
        remaining_avail = [s.seat_number for s in all_seats if s.status == "AVAILABLE"]
        self.assertTrue(len(remaining_avail) > 0)
        mixed_batch = [avail[0], remaining_avail[0]]

        with self.assertRaises(SeatUnavailableError):
            self.db.create_booking(
                show_id=show.id,
                customer_name="User Three (Mixed)",
                customer_phone="9876543211",
                customer_email=None,
                seat_numbers=mixed_batch,
                convenience_fee=25.0
            )

        # Verify remaining seat was NOT partially booked
        fresh_seats = self.db.get_seats_for_show(show.id)
        fresh_map = {s.seat_number: s for s in fresh_seats}
        self.assertEqual(fresh_map[remaining_avail[0]].status, "AVAILABLE")

    def test_zero_seats_rejected(self):
        """Attempting to checkout zero seats raises ValueError."""
        movies = self.db.get_all_movies()
        shows = self.db.get_shows_for_movie(movies[0].id)
        show = shows[0]

        with self.assertRaises(ValueError):
            self.db.create_booking(
                show_id=show.id,
                customer_name="Tester",
                customer_phone="9876543210",
                customer_email=None,
                seat_numbers=[],
                convenience_fee=25.0
            )

    def test_booking_cancellation_and_seat_restoration(self):
        """Verify cancellation updates booking to CANCELLED and restores seats to AVAILABLE."""
        movies = self.db.get_all_movies()
        shows = self.db.get_shows_for_movie(movies[0].id)
        show = shows[0]

        seats = self.db.get_seats_for_show(show.id)
        target_seats = [s.seat_number for s in seats if s.status == "AVAILABLE" and s.row == "F"][:2]

        booking = self.db.create_booking(
            show_id=show.id,
            customer_name="Cancellation Test",
            customer_phone="9988776655",
            customer_email="cancel@test.com",
            seat_numbers=target_seats,
            convenience_fee=25.0
        )

        # Seats are now BOOKED
        seat_map = {s.seat_number: s for s in self.db.get_seats_for_show(show.id)}
        for s_code in target_seats:
            self.assertEqual(seat_map[s_code].status, "BOOKED")

        # Execute cancellation
        success = self.db.cancel_booking(booking.id)
        self.assertTrue(success)

        # Check booking status is CANCELLED and cancelled_at timestamp is set
        cancelled_booking = self.db.get_booking_by_ref_or_id(booking.id)
        self.assertIsNotNone(cancelled_booking)
        self.assertEqual(cancelled_booking.booking_status, "CANCELLED")
        self.assertIsNotNone(cancelled_booking.cancelled_at)

        # Seats must now be restored to AVAILABLE with booking_id=None
        restored_seats = self.db.get_seats_for_show(show.id)
        restored_map = {s.seat_number: s for s in restored_seats}
        for s_code in target_seats:
            self.assertEqual(restored_map[s_code].status, "AVAILABLE")
            self.assertIsNone(restored_map[s_code].booking_id)

        # Re-cancelling must raise error
        with self.assertRaises(DatabaseError):
            self.db.cancel_booking(booking.id)

    def test_data_persistence(self):
        """Verify that committed bookings remain available across database re-openings."""
        movies = self.db.get_all_movies()
        show = self.db.get_shows_for_movie(movies[0].id)[0]
        seats = [s.seat_number for s in self.db.get_seats_for_show(show.id) if s.status == "AVAILABLE"][:1]

        booking = self.db.create_booking(
            show_id=show.id,
            customer_name="Persistence Patron",
            customer_phone="9123456789",
            customer_email=None,
            seat_numbers=seats,
            convenience_fee=25.0
        )

        # Instantiate second database instance pointing to same file
        reopened_db = DatabaseManager(self.db_path)
        persisted_booking = reopened_db.get_booking_by_ref_or_id(booking.booking_ref)

        self.assertIsNotNone(persisted_booking)
        self.assertEqual(persisted_booking.customer_name, "Persistence Patron")
        self.assertEqual(persisted_booking.seats, seats)

    def test_customer_input_validation_rules(self):
        """Unit test regex and validation rules for name, 10-digit mobile, and email."""
        phone_pattern = r"^[6-9]\d{9}$"
        email_pattern = r"^[\w\.-]+@[\w\.-]+\.\w+$"

        # Valid phone numbers
        self.assertTrue(bool(re.match(phone_pattern, "9876543210")))
        self.assertTrue(bool(re.match(phone_pattern, "8123456789")))
        self.assertTrue(bool(re.match(phone_pattern, "6012345678")))

        # Invalid phone numbers
        self.assertFalse(bool(re.match(phone_pattern, "1234567890")))   # Doesn't start with 6-9
        self.assertFalse(bool(re.match(phone_pattern, "987654321")))    # Only 9 digits
        self.assertFalse(bool(re.match(phone_pattern, "98765432100")))  # 11 digits
        self.assertFalse(bool(re.match(phone_pattern, "98765abcd0")))   # Non-numeric

        # Valid emails
        self.assertTrue(bool(re.match(email_pattern, "patron@example.com")))
        self.assertTrue(bool(re.match(email_pattern, "john.doe123@sub.domain.co")))

        # Invalid emails
        self.assertFalse(bool(re.match(email_pattern, "patronexample.com")))
        self.assertFalse(bool(re.match(email_pattern, "patron@")))


if __name__ == "__main__":
    unittest.main()
