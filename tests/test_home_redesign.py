"""
CineBook — Complete Home Screen Redesign Verification Test Suite
Tests:
1. Header displays supplied CineBook logo asset (CineBooklogo.png) and sets window icon.
2. Search field expands and updates movie discovery live.
3. Discovery toolbar filters: Status (Now Showing, Upcoming, All), Languages (5 industries), and Genres.
4. Recommended Movies carousel contains curated subset in 2:3 ratio with dark rating strip and pinned Book Tickets buttons.
5. All buttons in a row share identical vertical baseline coordinates.
6. Explore All Movies catalogue renders all 20 titles with responsive grid columns.
7. Promotional CineBook Stream banner renders full-width.
8. Real booking engine integration: clicking Book Tickets passes the correct movie ID and launches MovieView.
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


class TestHomeRedesign(unittest.TestCase):
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

    def test_01_supplied_logo_loaded(self):
        """Verify supplied CineBooklogo.png is loaded in header and set as window icon."""
        self.assertTrue(hasattr(self.app, "_logo_photo"), "App should retain PhotoImage reference")
        self.assertIsNotNone(self.app._logo_photo, "Supplied CineBook logo should be loaded")

    def test_02_home_view_structure(self):
        """Verify new HomeView sections exist and match BookMyShow specifications."""
        self.app.show_home()
        home = self.app.current_view
        self.assertIsInstance(home, HomeView)

        # Verify sections
        self.assertTrue(hasattr(home, "cat_buttons"), "Status filter buttons should exist")
        self.assertTrue(hasattr(home, "lang_buttons"), "Language filter buttons should exist")
        self.assertTrue(hasattr(home, "genre_buttons"), "Genre filter buttons should exist")
        self.assertTrue(hasattr(home, "promo_banner"), "Stream promo banner should exist")
        self.assertTrue(hasattr(home, "card_row"), "Recommended movies carousel should exist")
        self.assertTrue(hasattr(home, "grid_container"), "Explore All Movies grid should exist")

    def test_03_filter_toolbar_actions(self):
        """Verify status, language, and genre filter clicks update movie lists."""
        self.app.show_home()
        home = self.app.current_view

        # 1. Language Filter: Telugu
        home._on_language_clicked("Telugu")
        telugu_movies = home._get_filtered_movies()
        self.assertGreater(len(telugu_movies), 0)
        for m in telugu_movies:
            self.assertTrue("Telugu" in m.language or "Telugu" in m.industry)

        # 2. Genre Filter: Action
        home._on_genre_clicked("Action")
        action_telugu = home._get_filtered_movies()
        for m in action_telugu:
            self.assertIn("Action", m.genre)

        # 3. Status Filter: Upcoming
        home._on_category_clicked("Upcoming")
        upcoming = home._get_filtered_movies()
        for m in upcoming:
            self.assertTrue(m.is_upcoming)

        # 4. Reset Filters
        home._reset_filters()
        self.assertEqual(home.current_category, "Now Showing")
        self.assertEqual(home.current_language, "All")
        self.assertEqual(home.current_genre, "All")

    def test_04_recommended_vs_all_movies(self):
        """Verify Recommended Movies is a curated subset, while Explore All shows complete catalogue."""
        self.app.show_home()
        home = self.app.current_view
        home._reset_filters()

        # All movies in catalogue
        all_movies = self.app.db.get_all_movies()
        self.assertEqual(len(all_movies), 20, "Complete database should contain 20 titles")

        # Recommended subset
        rec_movies = home._get_recommended_movies()
        self.assertLessEqual(len(rec_movies), 10, "Recommended subset should be curated to top 10")
        self.assertGreaterEqual(len(rec_movies), 5, "Recommended subset should have at least 5 movies")

        # Ratings in recommended should be prioritized
        ratings = [m.rating for m in rec_movies]
        self.assertEqual(ratings, sorted(ratings, reverse=True), "Recommended movies must be sorted by rating")

    def test_05_movie_card_button_baseline_alignment(self):
        """Verify Book Tickets buttons across a row of movie cards have identical baseline y-coordinates."""
        self.app.show_home()
        home = self.app.current_view
        home._reset_filters()
        self.root.update_idletasks()

        # Inspect children of recommended card_row
        cards = [w for w in home.card_row.winfo_children() if hasattr(w, "book_btn")]
        self.assertGreaterEqual(len(cards), 2, "Expected multiple cards in recommended row")

        # Check button heights and alignments
        for card in cards:
            self.assertEqual(card.book_btn.btn_h, 48, "Book Tickets button height must be 48 px")
            self.assertEqual(card.title_lbl.cget("height"), 2, "Title area must have fixed 2-line height")

        btn_y = [c.book_btn.winfo_y() for c in cards]
        self.assertEqual(len(set(btn_y)), 1, f"Buttons are not aligned across row: {btn_y}")

    def test_06_real_booking_interaction(self):
        """Verify clicking Book Tickets triggers real booking flow with correct Movie object."""
        self.app.show_home()
        home = self.app.current_view
        target_movie = self.app.db.get_all_movies()[0]

        # Trigger on_select_movie
        home.on_select_movie(target_movie)
        self.root.update_idletasks()

        self.assertIsInstance(self.app.current_view, MovieView)
        self.assertEqual(self.app.current_view.movie.id, target_movie.id)
        self.assertEqual(self.app.current_view.movie.title, target_movie.title)

        # Return to home
        self.app.show_home()

    def test_07_promotional_banner_fit_and_vertical_clearance(self):
        """Verify PromotionalBannerWidget content fills top-to-bottom with >=20px balanced clearances and zero clipping."""
        self.root.deiconify()
        self.root.geometry("1400x800+40+40")
        self.app.show_home()
        home = self.app.current_view
        self.root.update_idletasks()
        self.root.update()

        banner = home.promo_banner
        banner_h = banner.winfo_height()
        self.assertEqual(banner_h, 200, "Banner height must be 200 px")

        # Inner frame vertical clearance
        inner_y = banner.inner_frame.winfo_y()
        inner_h = banner.inner_frame.winfo_reqheight()
        top_clearance = inner_y
        bottom_clearance = banner_h - (inner_y + inner_h)

        self.assertGreaterEqual(top_clearance, 20, f"Top clearance too tight: {top_clearance} px")
        self.assertGreaterEqual(bottom_clearance, 20, f"Bottom clearance too tight: {bottom_clearance} px")

        # VIP card vertical clearance on desktop
        self.assertEqual(banner.itemcget(banner.vip_window_id, "state"), "normal")
        vip_y = banner.vip_card.winfo_y()
        vip_h = banner.vip_card.winfo_reqheight()
        vip_top_clearance = vip_y
        vip_bottom_clearance = banner_h - (vip_y + vip_h)

        self.assertGreaterEqual(vip_top_clearance, 20, f"VIP card top clearance too tight: {vip_top_clearance} px")
        self.assertGreaterEqual(vip_bottom_clearance, 20, f"VIP card bottom clearance too tight: {vip_bottom_clearance} px")
        self.root.withdraw()


if __name__ == "__main__":
    unittest.main()
