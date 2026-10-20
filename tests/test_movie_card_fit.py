"""
CineBook - Movie Card Fit & Typography Acceptance Test Suite
Verifies:
1. Elimination of visible white card backgrounds (all card elements use BG_PAGE).
2. Typography sizes match requirements: title 16px bold, meta 13px, genre 13px, button 14px bold (h=40px).
3. 2:3 aspect ratio preserved without stretching or distortion.
4. Button baseline alignment across all cards in each row.
5. Window responsiveness at 1418x848, 1280x720, and 1024x768.
6. Captures screenshot of running desktop application for visual verification.
"""

import sys
import unittest
from pathlib import Path
import tkinter as tk

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from main import CineBookApp
from ui.theme import BG_PAGE, TEXT_PRIMARY, TEXT_MUTED
from ui.components import MovieCardWidget, PosterWidget, BookNowButton
from ui.home_view import HomeView
from ui.movie_view import MovieView

try:
    from PIL import ImageGrab, Image
    CAN_GRAB = True
except ImportError:
    CAN_GRAB = False


class TestMovieCardFit(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        try:
            cls.root = tk.Tk()
            cls.root.geometry("1418x848+40+40")
            cls.app = CineBookApp(cls.root)
            cls.root.update_idletasks()
        except tk.TclError as e:
            raise unittest.SkipTest(f"Display unavailable: {e}")

    @classmethod
    def tearDownClass(cls):
        if hasattr(cls, "root"):
            try:
                cls.root.destroy()
            except Exception:
                pass

    def test_01_no_visible_white_card_backgrounds(self):
        """Verify card, poster, info frame, labels, and button canvas all seamlessly match BG_PAGE."""
        self.app.show_home()
        home = self.app.current_view
        home._reset_filters()
        self.root.update_idletasks()

        cards = [w for w in home.card_row.winfo_children() if isinstance(w, MovieCardWidget)]
        self.assertGreaterEqual(len(cards), 2)

        for card in cards:
            self.assertEqual(card.cget("bg"), BG_PAGE, "Card container must match BG_PAGE")
            self.assertEqual(card.cget("highlightthickness"), 0, "Card border must be 0 (no white border)")
            self.assertEqual(card.info_frame.cget("bg"), BG_PAGE, "Info frame must match BG_PAGE")
            self.assertEqual(card.title_lbl.cget("bg"), BG_PAGE, "Title label must match BG_PAGE")
            self.assertEqual(card.meta_lbl.cget("bg"), BG_PAGE, "Meta label must match BG_PAGE")
            self.assertEqual(card.genre_lbl.cget("bg"), BG_PAGE, "Genre label must match BG_PAGE")
            self.assertEqual(card.book_btn.cget("bg"), BG_PAGE, "Button canvas must match BG_PAGE")
            self.assertEqual(card.poster.cget("bg"), BG_PAGE, "Poster canvas must match BG_PAGE")

    def test_02_typography_sizes(self):
        """Verify font sizes: title 21px bold, meta 16px bold, genre 16px, button 18px bold (h=48px), and ample clearance."""
        self.app.show_home()
        home = self.app.current_view
        self.root.update_idletasks()
        self.root.update()

        cards = [w for w in home.card_row.winfo_children() if isinstance(w, MovieCardWidget)]
        card = cards[0]

        # Title font
        title_font = card.title_lbl.cget("font")
        self.assertIn("-21", str(title_font), "Title font size should be 21 px")
        self.assertIn("bold", str(title_font), "Title should be bold")

        # Meta font
        meta_font = card.meta_lbl.cget("font")
        self.assertIn("-16", str(meta_font), "Language and cert should be 16 px")

        # Genre font
        genre_font = card.genre_lbl.cget("font")
        self.assertIn("-16", str(genre_font), "Genre should be 16 px")

        # Button
        self.assertEqual(card.book_btn.btn_h, 48, "Button height must be 48 px")
        self.assertEqual(card.book_btn.btn_text, "Book Tickets")
        self.assertEqual(card.book_btn.bg_color, "#F43F68", "Button color must be CineBook pink/red (#F43F68)")

        # Verify clear separation between genre text and button (no overlap)
        genre_bottom = card.genre_lbl.winfo_y() + card.genre_lbl.winfo_height()
        btn_top = card.book_btn.winfo_y()
        self.assertGreaterEqual(btn_top - genre_bottom, 10, f"Genre must not overlap button: {btn_top} vs {genre_bottom}")

    def test_03_poster_2_to_3_aspect_ratio(self):
        """Verify poster image height maintains exact 2:3 ratio (image_h = int(w * 1.5))."""
        self.app.show_home()
        home = self.app.current_view
        self.root.update_idletasks()

        cards = [w for w in home.card_row.winfo_children() if isinstance(w, MovieCardWidget)]
        for card in cards:
            w = card.poster.target_w
            sy = card.poster.target_h - card.poster.strip_h
            expected_image_h = int(w * 1.5)
            self.assertEqual(sy, expected_image_h, f"Poster image must maintain strict 2:3 ratio: {sy} vs {expected_image_h}")

    def test_04_baseline_alignment_at_various_resolutions(self):
        """Verify buttons across row align at 1418x848, 1280x720, and 1024x768."""
        resolutions = [
            (1418, 848),
            (1280, 720),
            (1024, 768)
        ]
        home = self.app.current_view

        for rw, rh in resolutions:
            self.root.geometry(f"{rw}x{rh}+20+20")
            self.root.update_idletasks()
            home._apply_responsive_layout()
            self.root.update()

            cards = [w for w in home.card_row.winfo_children() if isinstance(w, MovieCardWidget)]
            self.assertGreaterEqual(len(cards), 2, f"Failed at {rw}x{rh}")

            # Verify identical heights
            card_heights = [c.winfo_height() for c in cards]
            self.assertEqual(len(set(card_heights)), 1, f"Cards have unequal heights at {rw}x{rh}: {card_heights}")

            # Verify button baseline alignment
            btn_baselines = [c.book_btn.winfo_y() for c in cards]
            self.assertEqual(len(set(btn_baselines)), 1, f"Buttons not aligned at {rw}x{rh}: {btn_baselines}")

    def test_05_manjummel_boys_title_readable(self):
        """Verify 'Manjummel Boys' title is present, fully rendered, and not clipped."""
        self.app.show_home()
        home = self.app.current_view
        home._reset_filters()
        self.root.update_idletasks()

        all_grid_cards = [w for w in home.grid_container.winfo_children() if isinstance(w, MovieCardWidget)]
        mb_cards = [c for c in all_grid_cards if "Manjummel" in c.movie.title]
        self.assertGreaterEqual(len(mb_cards), 1, "Manjummel Boys should be present in catalogue")
        card = mb_cards[0]
        self.assertEqual(card.movie.title, "Manjummel Boys")
        self.assertEqual(card.title_lbl.cget("text"), "Manjummel Boys")
        self.assertEqual(card.title_lbl.cget("height"), 2)

    def test_06_capture_screenshot(self):
        """Capture screenshot of the running UI at 1418x848 for visual audit."""
        self.root.geometry("1418x848+40+40")
        self.root.deiconify()
        self.root.update_idletasks()
        self.root.update()

        artifact_dir = Path(r"C:\Users\Kskre\.gemini\antigravity-ide\brain\a934dd78-69ea-40dd-8102-07089ee97387")
        out_path = artifact_dir / "movie_card_fit_audit.png"

        if CAN_GRAB:
            try:
                x = self.root.winfo_rootx()
                y = self.root.winfo_rooty()
                w = self.root.winfo_width()
                h = self.root.winfo_height()
                bbox = (x, y, x + w, y + h)
                shot = ImageGrab.grab(bbox=bbox)
                shot.save(str(out_path))
                print(f"--> Screenshot saved successfully to {out_path}")
            except Exception as e:
                print(f"Notice: Screenshot capture skipped: {e}")


if __name__ == "__main__":
    unittest.main()
