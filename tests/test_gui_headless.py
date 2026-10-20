"""
CineBook - Headless GUI Integration Test
Instantiates the full Tkinter GUI, exercises view switching,
validates that all widgets mount without error, and tests ticket exports.
"""

import sys
import unittest
from pathlib import Path
import tkinter as tk

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from main import CineBookApp
from database import DatabaseManager


class TestGUIIntegration(unittest.TestCase):
    """Exercises Tkinter view lifecycle in headless/test mode."""

    @classmethod
    def setUpClass(cls):
        try:
            if tk._default_root is not None and tk._default_root.winfo_exists():
                cls.root = tk._default_root
            else:
                cls.root = tk.Tk()
                cls.root.withdraw()  # Do not display window on screen during tests
            cls.app = CineBookApp(cls.root)
        except tk.TclError as e:
            raise unittest.SkipTest(f"Display unavailable for Tkinter testing: {e}")

    @classmethod
    def tearDownClass(cls):
        pass

    def test_01_home_view_and_stats(self):
        """Verify home view mounts properly and displays movie cards."""
        self.app.show_home()
        self.assertIsNotNone(self.app.current_view)
        # Check that cards exist in home view
        movies = self.app.db.get_all_movies()
        self.assertGreater(len(movies), 0)

    def test_02_movie_view_mount(self):
        """Verify navigation to Movie Details view."""
        movies = self.app.db.get_all_movies()
        movie = movies[0]
        self.app.show_movie_details(movie)
        self.assertIsNotNone(self.app.current_view)

    def test_03_seat_view_mount(self):
        """Verify navigation to Seat Selection view."""
        movies = self.app.db.get_all_movies()
        shows = self.app.db.get_shows_for_movie(movies[0].id)
        show = shows[0]
        self.app.show_seat_selection(show)
        self.assertIsNotNone(self.app.current_view)

    def test_04_bookings_view_mount(self):
        """Verify navigation to My Bookings table."""
        self.app.show_bookings()
        self.assertIsNotNone(self.app.current_view)

    def test_05_about_view_mount(self):
        """Verify navigation to About / Viva Preparation view."""
        self.app.show_about()
        self.assertIsNotNone(self.app.current_view)

    def test_06_ticket_view_and_export(self):
        """Verify ticket view display and HTML/text export."""
        from unittest.mock import patch

        bookings = self.app.db.get_all_bookings()
        if not bookings:
            shows = self.app.db.get_shows_for_movie(1)
            if shows:
                seats = self.app.db.get_seats_for_show(shows[0].id)
                avail = [s.seat_number for s in seats if s.status == "AVAILABLE"][:1]
                if avail:
                    self.app.db.create_booking(shows[0].id, "Test Patron", "9876543210", "test@cinebook.com", avail)
            bookings = self.app.db.get_all_bookings()

        self.assertGreater(len(bookings), 0)
        booking = bookings[0]
        self.app.show_ticket(booking)
        self.assertIsNotNone(self.app.current_view)

        # Exercise export method with mocked messagebox
        with patch("tkinter.messagebox.showinfo") as mock_info:
            self.app.current_view._export_ticket()
            self.assertTrue(mock_info.called)

        exports_dir = PROJECT_ROOT / "exports"
        self.assertTrue(exports_dir.exists())

        ref_clean = booking.booking_ref.replace("-", "_")
        html_file = exports_dir / f"ticket_{ref_clean}.html"
        txt_file = exports_dir / f"ticket_{ref_clean}.txt"

        self.assertTrue(html_file.exists(), f"Expected {html_file} to exist")
        self.assertTrue(txt_file.exists(), f"Expected {txt_file} to exist")

        # Verify content
        txt_content = txt_file.read_text(encoding="utf-8")
        self.assertIn(booking.booking_ref, txt_content)
        self.assertIn("CINEBOOK", txt_content)


if __name__ == "__main__":
    unittest.main()
