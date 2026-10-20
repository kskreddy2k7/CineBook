"""
CineBook — Smart Movie Ticket Booking System
Main Application Entry Point & Controller (BookMyShow-Style Desktop Application)

Features:
- BookMyShow top navigation bar with CineBook logo, global live search, location selector, and nav buttons.
- Secondary category sub-navigation strip (Movies, Stream, Events, Plays, Sports, Offers).
- Light grey Discovery canvas (#F2F4F8) with centered generous horizontal margins.
- Seamless single-window view swapping across Movie Discovery, Showtime Details,
  Interactive Seat Selection, Checkout, Digital Ticket Pass, and My Bookings.
"""

import sys
import tkinter as tk
from tkinter import ttk, messagebox
from pathlib import Path
from typing import Optional, List

# Ensure project directory is in sys.path
BASE_DIR = Path(__file__).resolve().parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

# Enable high-DPI scaling on Windows to eliminate blurry text
if sys.platform.startswith("win"):
    try:
        import ctypes
        try:
            ctypes.windll.shcore.SetProcessDpiAwareness(2)
        except Exception:
            try:
                ctypes.windll.shcore.SetProcessDpiAwareness(1)
            except Exception:
                ctypes.windll.user32.SetProcessDPIAware()
    except Exception:
        pass

from database import DatabaseManager
from models import Movie, Show, Seat, Booking

try:
    from PIL import Image, ImageTk
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False
from ui.theme import (
    apply_theme, BG_PAGE, BG_CARD, BG_INPUT, BORDER_COLOR, BORDER_LIGHT, BORDER_CARD,
    ACCENT_RED, ACCENT_RED_HOVER, ACCENT_RED_LIGHT, ACCENT_CYAN, ACCENT_GOLD,
    TEXT_PRIMARY, TEXT_SECONDARY, TEXT_MUTED, TEXT_DARK, TEXT_LIGHT,
    FONT_HERO, FONT_TITLE, FONT_SUBTITLE, FONT_CARD_TITLE,
    FONT_BODY, FONT_BODY_BOLD, FONT_SMALL, FONT_SMALL_BOLD, FONT_BADGE,
    NAV_HEIGHT, SUB_NAV_HEIGHT, MAX_CONTENT_WIDTH, PAD_DESKTOP, PAD_TABLET, PAD_COMPACT
)
from ui.home_view import HomeView
from ui.movie_view import MovieView
from ui.seat_view import SeatView, CONVENIENCE_FEE
from ui.checkout_view import CheckoutView
from ui.ticket_view import TicketView
from ui.bookings_view import BookingsView
from ui.admin_view import AdminView
from ui.about_view import AboutView


class CineBookApp:
    """Master controller managing Tkinter window lifecycle and view routing."""

    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("CineBook — Movie Tickets, Showtimes & Cinema Discovery")
        self.root.minsize(480, 520)
        self.root.configure(bg=BG_PAGE)

        # Center window on screen within safe display bounds (reference ~1418 x 848)
        self._center_window(1418, 848)

        # Initialize SQLite database
        self.db = DatabaseManager()

        # Apply ttk styles
        apply_theme(self.root)

        # State management
        self.current_view: Optional[tk.Widget] = None
        self.active_nav_key: Optional[str] = None
        self.nav_buttons = {}
        self.selected_location = tk.StringVar(value="Chennai")
        self.search_query_var = tk.StringVar()

        # Build Main Shell (Top Header Bar + Dynamic View Container)
        self._build_shell()

        # Route to default home view
        self.show_home()

        # Window closing handler
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

    def _center_window(self, width: int = 1320, height: int = 880) -> None:
        """Positions window in center of the user's desktop within safe screen bounds."""
        self.root.update_idletasks()
        screen_w = self.root.winfo_screenwidth()
        screen_h = self.root.winfo_screenheight()
        target_w = min(width, max(1000, screen_w - 60))
        target_h = min(height, max(640, screen_h - 90))
        x = max(0, (screen_w - target_w) // 2)
        y = max(0, (screen_h - target_h) // 2 - 20)
        self.root.geometry(f"{target_w}x{target_h}+{x}+{y}")


    def _build_shell(self) -> None:
        """Constructs modern BookMyShow-style top navbar and main view container."""
        # ======================================================================
        # 1. Primary Top Navigation Header (Height NAV_HEIGHT, Pure White #FFFFFF)
        # ======================================================================
        self.top_header = tk.Frame(
            self.root,
            bg="#FFFFFF",
            height=NAV_HEIGHT,
            padx=24,
            pady=6,
            highlightthickness=1,
            highlightbackground=BORDER_COLOR
        )
        self.top_header.pack(side="top", fill="x")
        self.top_header.pack_propagate(False)

        # Left: CineBook Logo (using supplied CineBooklogo.png asset)
        brand_frame = tk.Frame(self.top_header, bg="#FFFFFF", cursor="hand2")
        brand_frame.pack(side="left", padx=(0, 20))
        brand_frame.bind("<Button-1>", lambda e: self.show_home())

        self._logo_photo = None
        logo_found = False
        logo_candidates = [
            Path(__file__).resolve().parent / "assets" / "posters" / "CineBooklogo.png",
            Path(__file__).resolve().parent / "assets" / "logo.png"
        ]
        for lp in logo_candidates:
            if lp.exists() and lp.is_file() and PIL_AVAILABLE:
                try:
                    with Image.open(str(lp)) as im:
                        im_rgba = im.convert("RGBA")
                        # Proportional square logo resized to 40x40 px with LANCZOS
                        im_resized = im_rgba.resize((40, 40), Image.Resampling.LANCZOS)
                        self._logo_photo = ImageTk.PhotoImage(im_resized, master=self.root)

                        logo_img_lbl = tk.Label(
                            brand_frame,
                            image=self._logo_photo,
                            bg="#FFFFFF",
                            cursor="hand2"
                        )
                        logo_img_lbl.pack(side="left", padx=(0, 8))
                        logo_img_lbl.bind("<Button-1>", lambda e: self.show_home())
                        logo_found = True

                        # Set application window icon using supplied logo
                        try:
                            self.root.iconphoto(True, self._logo_photo)
                        except Exception:
                            pass
                        break
                except Exception as e:
                    print(f"Notice: Could not load CineBook logo {lp}: {e}")

        if not logo_found:
            # Fallback only if asset is genuinely missing
            logo_icon = tk.Label(
                brand_frame,
                text="🎬",
                font=("Segoe UI", 20),
                bg="#FFFFFF",
                fg=ACCENT_RED
            )
            logo_icon.pack(side="left", padx=(0, 6))
            logo_icon.bind("<Button-1>", lambda e: self.show_home())

        logo_title = tk.Label(
            brand_frame,
            text="CINEBOOK",
            font=("Segoe UI", 16, "bold"),
            fg=TEXT_PRIMARY,
            bg="#FFFFFF"
        )
        logo_title.pack(side="left")
        logo_title.bind("<Button-1>", lambda e: self.show_home())

        # Center: Global Live Search Input Box
        search_frame = tk.Frame(
            self.top_header,
            bg="#F5F5FA",
            padx=12,
            pady=6,
            highlightthickness=1,
            highlightbackground=BORDER_CARD
        )
        search_frame.pack(side="left", fill="x", expand=True, padx=(0, 20))

        search_icon = tk.Label(
            search_frame,
            text="🔍",
            font=FONT_SMALL,
            fg=TEXT_MUTED,
            bg="#F5F5FA"
        )
        search_icon.pack(side="left", padx=(0, 8))

        self.search_entry = tk.Entry(
            search_frame,
            textvariable=self.search_query_var,
            font=FONT_BODY,
            bg="#F5F5FA",
            fg=TEXT_PRIMARY,
            insertbackground=TEXT_PRIMARY,
            relief="flat",
            bd=0
        )
        self.search_entry.pack(side="left", fill="x", expand=True)
        # When typing in search, automatically route to Home if on another view
        self.search_query_var.trace_add("write", self._on_search_input_change)

        clear_search_btn = tk.Label(
            search_frame,
            text="✖",
            font=FONT_BADGE,
            fg=TEXT_MUTED,
            bg="#F5F5FA",
            cursor="hand2"
        )
        clear_search_btn.pack(side="right", padx=(6, 0))
        clear_search_btn.bind("<Button-1>", lambda e: self.search_query_var.set(""))

        # Right Section: Location Selector + Navigation Buttons
        right_frame = tk.Frame(self.top_header, bg="#FFFFFF")
        right_frame.pack(side="right")

        # Location Selector Pill
        self.loc_btn = tk.Label(
            right_frame,
            text=f"📍 {self.selected_location.get()} ▾",
            font=FONT_SMALL_BOLD,
            bg="#F8F9FA",
            fg=TEXT_PRIMARY,
            padx=12,
            pady=6,
            cursor="hand2",
            highlightthickness=1,
            highlightbackground=BORDER_CARD
        )
        self.loc_btn.pack(side="left", padx=(0, 12))
        self.loc_btn.bind("<Button-1>", self._show_location_picker)

        # Primary Nav Links: Movie Discovery, My Bookings, and Demo Admin
        nav_items = [
            ("home", "Movie Discovery", self.show_home),
            ("bookings", "My Bookings", self.show_bookings),
            ("admin", "⚙ Demo Admin", self.show_admin),
        ]

        for key, text, cmd in nav_items:
            btn = tk.Label(
                right_frame,
                text=text,
                font=FONT_BODY_BOLD,
                bg="#FFFFFF",
                fg=TEXT_SECONDARY,
                padx=12,
                pady=6,
                cursor="hand2"
            )
            btn.pack(side="left", padx=2)
            btn.bind("<Button-1>", lambda e, command=cmd: command())
            self.nav_buttons[key] = btn

        # ======================================================================
        # 2. Secondary Sub-Navigation Strip (BookMyShow Category Bar, Height SUB_NAV_HEIGHT)
        # ======================================================================
        self.sub_header = tk.Frame(
            self.root,
            bg="#FAFAFC",
            height=SUB_NAV_HEIGHT,
            padx=24,
            highlightthickness=1,
            highlightbackground="#EEEEEE"
        )
        self.sub_header.pack(side="top", fill="x")
        self.sub_header.pack_propagate(False)

        # Bind responsive navbar handler
        self._shell_resize_timer = None
        self.root.bind("<Configure>", self._on_root_resize)

        # Left Categories
        sub_left = tk.Frame(self.sub_header, bg="#FAFAFC")
        sub_left.pack(side="left")

        categories = ["Movies", "Stream", "Events", "Plays", "Sports"]
        for idx, cat in enumerate(categories):
            is_active = (idx == 0)
            c_lbl = tk.Label(
                sub_left,
                text=cat,
                font=FONT_SMALL_BOLD if is_active else FONT_SMALL,
                fg=ACCENT_RED if is_active else "#555555",
                bg="#FAFAFC",
                padx=12,
                pady=6,
                cursor="hand2"
            )
            c_lbl.pack(side="left")
            if cat == "Movies":
                c_lbl.bind("<Button-1>", lambda e: self.show_home())
            elif cat == "Stream":
                c_lbl.bind("<Button-1>", lambda e: self._scroll_to_stream())

        # Right Quick Links
        sub_right = tk.Frame(self.sub_header, bg="#FAFAFC")
        sub_right.pack(side="right")

        for link in ["Offers", "Gift Cards"]:
            l_lbl = tk.Label(
                sub_right,
                text=link,
                font=FONT_SMALL,
                fg="#777777",
                bg="#FAFAFC",
                padx=10,
                pady=6,
                cursor="hand2"
            )
            l_lbl.pack(side="left")
            l_lbl.bind("<Enter>", lambda e, l=l_lbl: l.config(fg=ACCENT_RED))
            l_lbl.bind("<Leave>", lambda e, l=l_lbl: l.config(fg="#777777"))

        # ======================================================================
        # 3. Dynamic Main View Container
        # ======================================================================
        self.view_container = tk.Frame(self.root, bg=BG_PAGE)
        self.view_container.pack(side="top", fill="both", expand=True)

    def _on_root_resize(self, event=None) -> None:
        """Debounced root window resize listener to adapt navigation header."""
        if event and event.widget != self.root:
            return
        if self._shell_resize_timer is not None:
            try:
                self.root.after_cancel(self._shell_resize_timer)
            except Exception:
                pass
        self._shell_resize_timer = self.root.after(35, self._apply_shell_responsive)

    def _apply_shell_responsive(self) -> None:
        """Adapts top navigation bar elements dynamically to prevent overlap on narrow displays."""
        if not self.root.winfo_exists():
            return
        w = self.root.winfo_width()
        if w < 100:
            return

        city = self.selected_location.get()
        if w < 960:
            self.loc_btn.config(text=f"📍 {city}")
            if "home" in self.nav_buttons:
                self.nav_buttons["home"].config(text="Movies", padx=8)
            if "bookings" in self.nav_buttons:
                self.nav_buttons["bookings"].config(text="Bookings", padx=8)
            if "admin" in self.nav_buttons:
                self.nav_buttons["admin"].config(text="Admin", padx=8)
        else:
            self.loc_btn.config(text=f"📍 {city} ▾")
            if "home" in self.nav_buttons:
                self.nav_buttons["home"].config(text="Movie Discovery", padx=12)
            if "bookings" in self.nav_buttons:
                self.nav_buttons["bookings"].config(text="My Bookings", padx=12)
            if "admin" in self.nav_buttons:
                self.nav_buttons["admin"].config(text="⚙ Demo Admin", padx=12)

    def _on_search_input_change(self, *args) -> None:
        """When user types in global search, ensure HomeView is active."""
        if self.search_query_var.get().strip():
            if self.active_nav_key != "home":
                self.show_home()

    def _show_location_picker(self, event=None) -> None:
        """Pops up a clean city selector menu."""
        menu = tk.Menu(self.root, tearoff=0, font=FONT_BODY, bg="#FFFFFF", fg=TEXT_PRIMARY,
                       activebackground=ACCENT_RED_LIGHT, activeforeground=ACCENT_RED)
        cities = ["Chennai", "Hyderabad", "Bengaluru", "Mumbai", "Kochi"]
        for city in cities:
            menu.add_command(
                label=f"  📍 {city}",
                command=lambda c=city: self._select_location(c)
            )
        try:
            x = self.loc_btn.winfo_rootx()
            y = self.loc_btn.winfo_rooty() + self.loc_btn.winfo_height() + 4
            menu.tk_popup(x, y)
        finally:
            menu.grab_release()

    def _select_location(self, city: str) -> None:
        self.selected_location.set(city)
        self.loc_btn.config(text=f"📍 {city} ▾")
        if isinstance(self.current_view, HomeView):
            self.show_home()
        elif isinstance(self.current_view, MovieView):
            self.current_view._on_city_selected(city)

    def _scroll_to_stream(self) -> None:
        if self.active_nav_key != "home":
            self.show_home()
        if isinstance(self.current_view, HomeView):
            self.current_view.scroll_container.canvas.yview_moveto(0.35)

    def _set_active_nav(self, active_key: Optional[str]) -> None:
        """Updates highlight on active top navigation item."""
        self.active_nav_key = active_key
        for key, btn in self.nav_buttons.items():
            if key == active_key:
                btn.config(fg=ACCENT_RED, bg="#FFF0F2")
            else:
                btn.config(fg="#4B5563", bg="#FFFFFF")

    def _switch_view(self, new_view_widget: tk.Widget, nav_key: Optional[str] = None) -> None:
        """Destroys current view and seamlessly mounts the new view container."""
        if self.current_view is not None:
            self.current_view.destroy()

        self.current_view = new_view_widget
        self.current_view.pack(fill="both", expand=True)
        self._set_active_nav(nav_key)

    # ==========================================================================
    # VIEW ROUTERS
    # ==========================================================================
    def show_home(self) -> None:
        """Route to Movie Discovery Home View."""
        view = HomeView(
            self.view_container,
            db=self.db,
            on_select_movie=self.show_movie_details,
            on_view_bookings=self.show_bookings,
            search_query_var=self.search_query_var
        )
        self._switch_view(view, nav_key="home")

    def show_movie_details(self, movie: Movie, city: Optional[str] = None) -> None:
        """Route to detailed Movie View with Showtimes and Multi-City support."""
        target_city = city or self.selected_location.get()
        view = MovieView(
            self.view_container,
            db=self.db,
            movie=movie,
            on_back=self.show_home,
            on_proceed_to_seats=self.show_seat_selection,
            selected_city=target_city
        )
        self._switch_view(view, nav_key=None)

    def show_seat_selection(self, show: Show) -> None:
        """Route to Interactive Auditorium Seat Selection."""
        view = SeatView(
            self.view_container,
            db=self.db,
            show=show,
            on_back=lambda: self.show_movie_details_by_id(show.movie_id),
            on_proceed_to_checkout=self.show_checkout
        )
        self._switch_view(view, nav_key=None)

    def show_movie_details_by_id(self, movie_id: int) -> None:
        """Helper to navigate back to movie details from seat selection."""
        movie = self.db.get_movie_by_id(movie_id)
        if movie:
            self.show_movie_details(movie)
        else:
            self.show_home()

    def show_checkout(
        self,
        show: Show,
        selected_seats: List[Seat],
        subtotal: float,
        total: float,
        convenience_fee: float = CONVENIENCE_FEE
    ) -> None:
        """Route to Customer Checkout Form."""
        view = CheckoutView(
            self.view_container,
            db=self.db,
            show=show,
            selected_seats=selected_seats,
            subtotal=subtotal,
            total=total,
            convenience_fee=convenience_fee,
            on_back=lambda: self.show_seat_selection(show),
            on_booking_confirmed=self.show_ticket
        )
        self._switch_view(view, nav_key=None)

    def show_ticket(self, booking: Booking) -> None:
        """Route to Digital Ticket Pass confirmation view."""
        view = TicketView(
            self.view_container,
            booking=booking,
            on_go_home=self.show_home,
            on_view_bookings=self.show_bookings
        )
        self._switch_view(view, nav_key=None)

    def show_bookings(self) -> None:
        """Route to My Bookings History View."""
        view = BookingsView(
            self.view_container,
            db=self.db,
            on_view_ticket=self.show_ticket,
            on_go_home=self.show_home
        )
        self._switch_view(view, nav_key="bookings")

    def show_admin(self) -> None:
        """Route to Demo Administration & Pricing View."""
        view = AdminView(
            self.view_container,
            db=self.db,
            on_go_home=self.show_home
        )
        self._switch_view(view, nav_key="admin")

    def show_about(self) -> None:
        """Route to About, Architecture, & Guide View."""
        view = AboutView(
            self.view_container,
            db=self.db,
            on_go_home=self.show_home
        )
        self._switch_view(view, nav_key=None)

    def _on_close(self) -> None:
        """Clean application shutdown."""
        self.root.destroy()


def main():
    root = tk.Tk()
    app = CineBookApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
