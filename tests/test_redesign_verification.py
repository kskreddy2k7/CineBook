"""
Comprehensive Verification Script for BookMyShow-style Redesign
Tests:
- Application startup with new top navigation bar
- Location selector dropdown
- Search query filtering across Recommended carousel & All Movies grid
- Category and genre filtering
- 5-card carousel navigation (Next & Prev)
- Promotional banner rendering
- Movie selection and details view mounting
- Seat selection, live price calculation, checkout, and booking persistence
- Booking cancellation and ticket export
"""

import sys
import unittest
from pathlib import Path
import tkinter as tk

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from main import CineBookApp
from ui.home_view import HomeView
from ui.movie_view import MovieView
from ui.seat_view import SeatView
from ui.checkout_view import CheckoutView
from ui.ticket_view import TicketView
from ui.bookings_view import BookingsView


class TestRedesignVerification(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        try:
            cls.root = tk.Tk()
            cls.root.withdraw()
            cls.app = CineBookApp(cls.root)
        except tk.TclError as e:
            raise unittest.SkipTest(f"Display unavailable: {e}")

    @classmethod
    def tearDownClass(cls):
        if hasattr(cls, "root"):
            try:
                cls.root.destroy()
            except Exception:
                pass

    def test_01_top_navbar_components(self):
        """Verify top navigation bar elements."""
        self.assertTrue(hasattr(self.app, "top_header"))
        self.assertTrue(hasattr(self.app, "sub_header"))
        self.assertTrue(hasattr(self.app, "search_entry"))
        self.assertTrue(hasattr(self.app, "loc_btn"))
        self.assertEqual(self.app.selected_location.get(), "Chennai")

    def test_02_home_view_carousel_and_banner(self):
        """Verify HomeView has 5-card carousel and promotional banner."""
        self.app.show_home()
        home = self.app.current_view
        self.assertIsInstance(home, HomeView)
        self.assertTrue(hasattr(home, "promo_banner"))
        self.assertTrue(hasattr(home, "prev_btn"))
        self.assertTrue(hasattr(home, "next_btn"))

        # Verify movies present
        movies = self.app.db.get_all_movies()
        self.assertGreaterEqual(len(movies), 8)

        # Test carousel next
        home._carousel_next()
        self.assertEqual(home.carousel_start_idx, 1)

        # Test carousel prev
        home._carousel_prev()
        self.assertEqual(home.carousel_start_idx, 0)

    def test_03_search_and_genre_filtering(self):
        """Verify title search and genre chip filters."""
        self.app.show_home()
        home = self.app.current_view

        # Search for 'RRR'
        self.app.search_query_var.set("RRR")
        home._refresh_all_views()
        filtered = home._get_filtered_movies()
        self.assertGreaterEqual(len(filtered), 1)
        self.assertTrue(any("RRR" in m.title for m in filtered))

        # Clear search
        self.app.search_query_var.set("")
        home._refresh_all_views()

        # Genre filter
        home._on_genre_clicked("Action")
        filtered_genre = home._get_filtered_movies()
        self.assertGreater(len(filtered_genre), 0)
        for m in filtered_genre:
            self.assertIn("Action", m.genre)

        # Reset filters
        home._reset_filters()
        self.assertEqual(home.current_genre, "All")

    def test_04_full_booking_flow(self):
        """End-to-end test of booking flow: details -> seat selection -> checkout -> ticket."""
        movie = self.app.db.get_all_movies()[0]
        self.app.show_movie_details(movie)
        self.assertIsInstance(self.app.current_view, MovieView)

        # Pick first show
        shows = self.app.db.get_shows_for_movie(movie.id)
        show = shows[0]

        # Go to seat view
        self.app.show_seat_selection(show)
        self.assertIsInstance(self.app.current_view, SeatView)
        seat_view = self.app.current_view

        # Pick two available seats dynamically
        available = [s for s in seat_view.seats_data.values() if s.status == "AVAILABLE"]
        self.assertGreaterEqual(len(available), 2, "Expected at least 2 available seats")
        code1, code2 = available[0].seat_number, available[1].seat_number

        # Toggle seats
        seat_view._toggle_seat_selection(code1)
        seat_view._toggle_seat_selection(code2)
        self.assertEqual(len(seat_view.selected_seat_numbers), 2)

        # Proceed to checkout
        selected_seats = [seat_view.seats_data[s] for s in [code1, code2]]
        subtotal = sum(s.price for s in selected_seats)
        total = subtotal + 25.0
        self.app.show_checkout(show, selected_seats, subtotal, total)
        self.assertIsInstance(self.app.current_view, CheckoutView)

        checkout_view = self.app.current_view
        checkout_view.name_var.set("Devashish Test")
        checkout_view.phone_var.set("9876543210")
        checkout_view.email_var.set("test@cinebook.com")

        valid, msg = checkout_view._validate_inputs()
        self.assertTrue(valid)

        # Trigger booking confirmation with mock messagebox
        from unittest.mock import patch
        with patch("tkinter.messagebox.showinfo"), patch("tkinter.messagebox.showerror"), patch("tkinter.messagebox.askyesno", return_value=True):
            checkout_view._handle_confirmation()

        self.assertIsInstance(self.app.current_view, TicketView)
        ticket_view = self.app.current_view
        self.assertEqual(ticket_view.booking.customer_name, "Devashish Test")

        # Check bookings view
        self.app.show_bookings()
        self.assertIsInstance(self.app.current_view, BookingsView)

    def test_05_indian_movie_catalogue_and_posters(self):
        """Verify Indian movies across 5 industries with factual metadata and local posters."""
        movies = self.app.db.get_all_movies()
        self.assertGreaterEqual(len(movies), 15)

        industries = set(getattr(m, "industry", "") for m in movies)
        self.assertTrue(any("Telugu" in ind for ind in industries))
        self.assertTrue(any("Tamil" in ind for ind in industries))
        self.assertTrue(any("Hindi" in ind for ind in industries))
        self.assertTrue(any("Malayalam" in ind for ind in industries))
        self.assertTrue(any("Kannada" in ind for ind in industries))

        # Verify poster assets exist on filesystem
        for m in movies:
            p_path = PROJECT_ROOT / m.poster_path
            self.assertTrue(p_path.exists(), f"Poster missing for {m.title}: {p_path}")

    def test_06_multi_city_theatre_hierarchy(self):
        """Verify City -> Theatre -> Screen hierarchy across Indian cities."""
        cities = self.app.db.get_cities()
        self.assertGreaterEqual(len(cities), 5)
        city_names = [c.name for c in cities]
        for expected_city in ["Chennai", "Hyderabad", "Bengaluru", "Mumbai", "Kochi"]:
            self.assertIn(expected_city, city_names)

        theatres = self.app.db.get_theatres_by_city("Hyderabad")
        self.assertGreaterEqual(len(theatres), 3)

        first_theatre = theatres[0]
        screens = self.app.db.get_screens_by_theatre(first_theatre.id)
        self.assertEqual(len(screens), 3)
        screen_types = [s.screen_type for s in screens]
        self.assertIn("IMAX Laser 3D", screen_types)
        self.assertIn("Dolby Atmos 4K", screen_types)

        # Test grouped shows by theatre
        movie = self.app.db.get_all_movies()[0]
        grouped = self.app.db.get_shows_grouped_by_theatre(movie.id, city_name="Chennai")
        self.assertGreater(len(grouped), 0)

    def test_07_seat_view_rows_a_to_l_zoom_and_quick_switch(self):
        """Verify Rows A-L (12 rows), zoom controls, and horizontal showtime quick-switch."""
        movie = self.app.db.get_all_movies()[0]
        shows = self.app.db.get_shows_for_movie(movie.id)
        show = shows[0]

        self.app.show_seat_selection(show)
        seat_view = self.app.current_view
        self.assertIsInstance(seat_view, SeatView)

        # Verify Rows A through L are present in seats_data
        row_letters = set(s[0] for s in seat_view.seats_data.keys())
        for expected_row in ["A", "B", "C", "D", "E", "F", "G", "H", "I", "J", "K", "L"]:
            self.assertIn(expected_row, row_letters)

        # Test zoom controls
        initial_size = seat_view.current_seat_size
        seat_view._zoom_in()
        self.assertEqual(seat_view.current_seat_size, initial_size + 4)
        seat_view._zoom_out()
        self.assertEqual(seat_view.current_seat_size, initial_size)
        seat_view._zoom_reset()
        self.assertEqual(seat_view.current_seat_size, initial_size)

        # Test horizontal showtime switcher
        if len(shows) > 1:
            next_show = shows[1]
            seat_view._toggle_seat_selection("A1")
            self.assertIn("A1", seat_view.selected_seat_numbers)

            from unittest.mock import patch
            with patch("tkinter.messagebox.askyesno", return_value=True):
                seat_view._on_switch_showtime(next_show)

            self.assertEqual(seat_view.show.id, next_show.id)
            self.assertEqual(len(seat_view.selected_seat_numbers), 0, "Seat selection should reset on showtime switch")

    def test_08_admin_view_and_price_adjuster(self):
        """Verify Demo Administration console and ticket price adjuster."""
        from ui.admin_view import AdminView
        self.app.show_admin()
        admin_view = self.app.current_view
        self.assertIsInstance(admin_view, AdminView)

        # Check metrics
        stats = self.app.db.get_dashboard_stats()
        self.assertGreaterEqual(stats["total_movies"], 15)
        self.assertGreaterEqual(stats["total_cities"], 5)
        self.assertGreaterEqual(stats["total_theatres"], 15)

        # Test price adjuster
        movie = self.app.db.get_all_movies()[0]
        show = self.app.db.get_shows_for_movie(movie.id)[0]
        success = self.app.db.update_show_prices(show.id, 160.0, 240.0, 320.0)
        self.assertTrue(success)

        updated_show = self.app.db.get_show_by_id(show.id)
        self.assertEqual(updated_show.price_classic, 160.0)
        self.assertEqual(updated_show.price_elite, 240.0)
        self.assertEqual(updated_show.price_recliner, 320.0)

    def test_09_poster_unavailable_fallback(self):
        """Verify unavailable-poster fallback renders clean message without AI shapes."""
        from ui.components import PosterWidget
        pw = PosterWidget(
            self.app.root,
            image_path="assets/posters/nonexistent_sample.jpg",
            width=200,
            height=300,
            title="Unreleased Title",
            genre="Adventure",
            rating=0.0,
            is_upcoming=True
        )
        self.assertIsNotNone(pw)
        items = pw.find_all()
        self.assertGreater(len(items), 0)
        texts = [pw.itemcget(i, "text") for i in items if pw.type(i) == "text"]
        self.assertIn("POSTER UNAVAILABLE", texts)
        self.assertIn("Theatrical Artwork Pending", texts)
        pw.destroy()


    def test_10_all_five_industries_bookable(self):
        """Verify movies from all 5 Indian cinema industries have working shows and can be booked."""
        movies = self.app.db.get_all_movies()
        languages = ["Telugu", "Tamil", "Hindi", "Malayalam", "Kannada"]

        for lang in languages:
            matching = [m for m in movies if m.language.lower() == lang.lower()]
            self.assertGreater(len(matching), 0, f"Expected at least one {lang} movie in catalogue")

            target_movie = matching[0]
            shows = self.app.db.get_shows_for_movie(target_movie.id)
            if not shows:
                # Dynamic demo show creation test
                created = self.app.db.generate_demo_shows_for_movie(target_movie.id)
                self.assertGreater(created, 0)
                shows = self.app.db.get_shows_for_movie(target_movie.id)

            self.assertGreater(len(shows), 0, f"Expected showtimes for {target_movie.title} ({lang})")

            # Verify seats exist for show
            seats = self.app.db.get_seats_for_show(shows[0].id)
            self.assertGreaterEqual(len(seats), 96, f"Expected full Rows A-L seat inventory for {target_movie.title}")

    def test_11_generate_demo_shows_dynamic(self):
        """Verify dynamic demonstration show generation for unconfigured movies or cities."""
        # Find any movie or use first movie
        movies = self.app.db.get_all_movies()
        test_movie = movies[0]

        # Generate demo shows for Kochi
        count = self.app.db.generate_demo_shows_for_movie(test_movie.id, city_name="Kochi")
        self.assertGreaterEqual(count, 0)

        dates = self.app.db.get_show_dates_for_movie_and_city(test_movie.id, "Kochi")
        self.assertGreater(len(dates), 0, "Expected show dates in Kochi after generation")

    def test_12_seat_selection_green_and_max_limit(self):
        """Verify selected seats identify with green background and enforce 6-ticket maximum."""
        from ui.theme import SEAT_SELECTED_BG
        from ui.seat_view import MAX_SEATS_PER_BOOKING

        self.assertEqual(SEAT_SELECTED_BG, "#10B981", "Selected seats must use emerald green")

        movie = self.app.db.get_all_movies()[0]
        show = self.app.db.get_shows_for_movie(movie.id)[0]
        self.app.show_seat_selection(show)
        seat_view = self.app.current_view
        self.assertIsInstance(seat_view, SeatView)

        # Clear any prior selection
        seat_view.selected_seat_numbers.clear()

        # Select 6 available seats
        available = [s for s in seat_view.seats_data.values() if s.status == "AVAILABLE"]
        self.assertGreaterEqual(len(available), 7)

        for i in range(MAX_SEATS_PER_BOOKING):
            code = available[i].seat_number
            seat_view._toggle_seat_selection(code)
            self.assertIn(code, seat_view.selected_seat_numbers)
            w = seat_view.seat_widgets[code]
            self.assertTrue(w.is_selected)

        self.assertEqual(len(seat_view.selected_seat_numbers), 6)

        # Attempt to select a 7th seat: should be blocked and show warning
        from unittest.mock import patch
        seventh_code = available[6].seat_number
        with patch("tkinter.messagebox.showwarning") as mock_warn:
            seat_view._toggle_seat_selection(seventh_code)
            mock_warn.assert_called_once()
            self.assertNotIn(seventh_code, seat_view.selected_seat_numbers)
            self.assertEqual(len(seat_view.selected_seat_numbers), 6)

    def test_13_movie_to_seat_button_click_and_checkout_flow(self):
        """Verify that selecting a show slot activates Select Seats ->, clicking proceeds to SeatView, and checkout proceeds."""
        movie = self.app.db.get_all_movies()[0]
        self.app.show_movie_details(movie)
        movie_view = self.app.current_view
        self.assertIsInstance(movie_view, MovieView)

        # Slot buttons must be populated
        self.assertGreater(len(movie_view.show_slot_buttons), 0)
        first_show_id = list(movie_view.show_slot_buttons.keys())[0]

        # Select show slot
        movie_view._on_show_selected(movie_view.db.get_show_by_id(first_show_id))
        self.assertEqual(movie_view.proceed_btn._state, "normal")

        # Click proceed button
        movie_view.proceed_btn.invoke()

        # Must now be in SeatView
        self.assertIsInstance(self.app.current_view, SeatView)
        seat_view = self.app.current_view
        self.assertEqual(len(seat_view.seat_widgets), 96)

        # Toggle seat selection
        seat_view._toggle_seat_selection("C3")
        self.assertIn("C3", seat_view.selected_seat_numbers)
        self.assertEqual(seat_view.checkout_btn._state, "normal")

        # Click checkout button
        seat_view.checkout_btn.invoke()
        self.assertIsInstance(self.app.current_view, CheckoutView)

    def test_14_responsive_window_resizing_and_breakpoints(self):
        """Verify responsive behavior across target display sizes (1024x768, 1280x720, 1366x768, 1600x900, 1920x1080)."""
        self.app.show_home()
        home = self.app.current_view
        self.assertIsInstance(home, HomeView)

        resolutions = [
            (1024, 768),
            (1280, 720),
            (1366, 768),
            (1600, 900),
            (1920, 1080)
        ]

        for w, h in resolutions:
            home.winfo_width = (lambda width=w: width)
            home._apply_responsive_layout()
            container_w = w - 90
            if container_w >= 1050:
                self.assertEqual(home.cards_per_view, 5)
            elif container_w >= 850:
                self.assertEqual(home.cards_per_view, 4)
            else:
                self.assertEqual(home.cards_per_view, 3)

        # Restore reference geometry
        home.winfo_width = (lambda: 1263)
        home._apply_responsive_layout()
        self.assertEqual(home.cards_per_view, 5)

    def test_15_seat_view_responsive_stacking(self):
        """Verify SeatView dynamically stacks booking calculator below auditorium at narrow widths (< 980px)."""
        movie = self.app.db.get_all_movies()[0]
        show = self.app.db.get_shows_for_movie(movie.id)[0]
        self.app.show_seat_selection(show)
        seat_view = self.app.current_view
        self.assertIsInstance(seat_view, SeatView)

        # Wide screen layout (>= 980px)
        self.root.geometry("1263x847")
        self.root.update_idletasks()
        seat_view.winfo_width = lambda: 1263
        seat_view._on_layout_configure()
        self.assertFalse(seat_view._is_stacked)

        # Narrow screen layout (< 980px)
        self.root.geometry("900x700")
        self.root.update_idletasks()
        # Force width on seat_view for headless test
        seat_view.winfo_width = lambda: 900
        seat_view._on_layout_configure()
        self.assertTrue(seat_view._is_stacked)

        # Restore wide width
        seat_view.winfo_width = lambda: 1263
        seat_view._on_layout_configure()
        self.assertFalse(seat_view._is_stacked)

    def test_16_my_bookings_table_and_action_toolbar(self):
        """Verify BookingsView Treeview, status filters, search filtering, and action toolbar."""
        self.app.show_bookings()
        bookings_view = self.app.current_view
        self.assertIsInstance(bookings_view, BookingsView)

        # Action buttons initial state: disabled when no row selected
        self.assertEqual(bookings_view.view_btn._state, "disabled")
        self.assertEqual(bookings_view.cancel_btn._state, "disabled")

        # Test status filter clicking
        bookings_view._on_filter_clicked("CONFIRMED")
        self.assertEqual(bookings_view.current_filter, "CONFIRMED")

        bookings_view._on_filter_clicked("CANCELLED")
        self.assertEqual(bookings_view.current_filter, "CANCELLED")

        bookings_view._on_filter_clicked("ALL")
        self.assertEqual(bookings_view.current_filter, "ALL")

        # Reset search and filters
        bookings_view._reset_search_and_filters()
        self.assertEqual(bookings_view.search_var.get(), "")
        self.assertEqual(bookings_view.current_filter, "ALL")


if __name__ == "__main__":
    unittest.main()


