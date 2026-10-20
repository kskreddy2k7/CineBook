"""
CineBook - Movie Details & Show Selection View (BookMyShow-Style Light Theme)
Displays comprehensive Indian movie metadata, synopsis, cast/crew,
city selection, date selection tabs, and theatres with multi-screen showtimes.
"""

from datetime import datetime
from typing import Callable, Dict, List, Optional, Any
import tkinter as tk
from tkinter import ttk, messagebox

from database import DatabaseManager
from models import Movie, Show, Theatre, City
from ui.theme import (
    BG_PAGE, BG_CARD, BG_INPUT, BORDER_COLOR, BORDER_LIGHT, BORDER_CARD,
    ACCENT_RED, ACCENT_RED_HOVER, ACCENT_RED_LIGHT, ACCENT_CYAN, ACCENT_GOLD,
    TEXT_PRIMARY, TEXT_SECONDARY, TEXT_MUTED, TEXT_DARK, TEXT_LIGHT,
    FONT_HERO, FONT_TITLE, FONT_SUBTITLE, FONT_CARD_TITLE,
    FONT_BODY, FONT_BODY_BOLD, FONT_SMALL, FONT_SMALL_BOLD, FONT_BADGE,
    TIER_RECLINER, TIER_PREMIUM, TIER_STANDARD
)
from ui.components import PosterWidget, ScrollableFrame, ModernButton


class MovieView(tk.Frame):
    """Detailed Movie Information & Multi-City/Theatre Showtime Picker View."""

    def __init__(
        self,
        master,
        db: DatabaseManager,
        movie: Movie,
        on_back: Callable[[], None],
        on_proceed_to_seats: Callable[[Show], None],
        selected_city: Optional[str] = "Chennai",
        **kwargs
    ):
        super().__init__(master, bg=BG_PAGE, **kwargs)
        self.db = db
        self.movie = movie
        self.on_back = on_back
        self.on_proceed_to_seats = on_proceed_to_seats
        self.selected_city = selected_city or "Chennai"

        self.selected_date: Optional[str] = None
        self.selected_show: Optional[Show] = None
        self.date_buttons: Dict[str, tk.Label] = {}
        self.city_buttons: Dict[str, tk.Label] = {}
        self.show_slot_buttons: Dict[int, tk.Label] = {}

        self.scroll_container = ScrollableFrame(self, bg=BG_PAGE)
        self.scroll_container.pack(fill="both", expand=True)
        self.content = self.scroll_container.scrollable_content

        # Centered container with generous horizontal margins
        self.main_wrapper = tk.Frame(self.content, bg=BG_PAGE)
        self.main_wrapper.pack(fill="x", padx=48, pady=(16, 36))

        self._build_top_bar()
        self._build_movie_banner()
        self._build_city_and_date_section()

    def _build_top_bar(self) -> None:
        """Top navigation bar with back button."""
        top_bar = tk.Frame(self.main_wrapper, bg=BG_PAGE)
        top_bar.pack(fill="x", pady=(0, 14))

        back_btn = tk.Label(
            top_bar,
            text="← Back to Indian Movies Discovery",
            font=FONT_BODY_BOLD,
            fg=ACCENT_RED,
            bg=BG_PAGE,
            cursor="hand2"
        )
        back_btn.pack(side="left")
        back_btn.bind("<Button-1>", lambda e: self.on_back())

    def _build_movie_banner(self) -> None:
        """Movie details banner with 2:3 portrait poster, synopsis, cast, and censor rating."""
        banner_card = tk.Frame(
            self.main_wrapper,
            bg=BG_CARD,
            padx=28,
            pady=24,
            highlightthickness=1,
            highlightbackground=BORDER_CARD
        )
        banner_card.pack(fill="x", pady=(0, 24))

        # 2:3 Portrait Poster
        poster = PosterWidget(
            banner_card,
            image_path=self.movie.poster_path,
            width=220,
            height=330,
            title=self.movie.title,
            genre=self.movie.genre,
            rating=self.movie.rating,
            votes=getattr(self.movie, "vote_count", "50K"),
            is_upcoming=getattr(self.movie, "is_upcoming", False),
            banner_color=self.movie.banner_color
        )
        poster.pack(side="left", padx=(0, 28), anchor="n")

        details_frame = tk.Frame(banner_card, bg=BG_CARD)
        details_frame.pack(side="left", fill="both", expand=True)

        title_lbl = tk.Label(
            details_frame,
            text=self.movie.title,
            font=FONT_HERO,
            fg=TEXT_PRIMARY,
            bg=BG_CARD,
            wraplength=780,
            justify="left"
        )
        title_lbl.pack(anchor="w")

        # Ratings & Badges Strip
        meta_row = tk.Frame(details_frame, bg=BG_CARD)
        meta_row.pack(fill="x", pady=(8, 12), anchor="w")

        # Rating badge
        if getattr(self.movie, "is_upcoming", False):
            tk.Label(
                meta_row,
                text="★ UPCOMING PREVIEW",
                font=FONT_SMALL_BOLD,
                fg=TEXT_DARK,
                bg=ACCENT_GOLD,
                padx=10,
                pady=4
            ).pack(side="left", padx=(0, 8))
        else:
            vote_str = f" ({self.movie.vote_count} Votes)" if hasattr(self.movie, "vote_count") else ""
            tk.Label(
                meta_row,
                text=f"★ {self.movie.rating:.1f}/10{vote_str}",
                font=FONT_SMALL_BOLD,
                fg=TEXT_DARK,
                bg=ACCENT_GOLD,
                padx=10,
                pady=4
            ).pack(side="left", padx=(0, 8))

        # Censor Rating
        tk.Label(
            meta_row,
            text=self.movie.censor_rating,
            font=FONT_BADGE,
            fg=TEXT_PRIMARY,
            bg="#F1F3F6",
            padx=8,
            pady=4
        ).pack(side="left", padx=(0, 8))

        # Industry & Language
        ind_txt = getattr(self.movie, "industry", "Indian Cinema")
        tk.Label(
            meta_row,
            text=f"{ind_txt} • {self.movie.language}",
            font=FONT_BADGE,
            fg=ACCENT_CYAN,
            bg="#F0F9FF",
            padx=8,
            pady=4
        ).pack(side="left", padx=(0, 8))

        # Release Year & Duration
        rel_yr = getattr(self.movie, "release_year", 2024)
        tk.Label(
            meta_row,
            text=f"{rel_yr}  •  {self.movie.duration}  •  {self.movie.genre}",
            font=FONT_BODY,
            fg=TEXT_SECONDARY,
            bg=BG_CARD
        ).pack(side="left", padx=4)

        # Demonstration Notice Banner
        demo_notice = tk.Frame(details_frame, bg="#FFFBEB", padx=10, pady=6,
                               highlightthickness=1, highlightbackground="#FCD34D")
        demo_notice.pack(fill="x", pady=(0, 12), anchor="w")
        tk.Label(
            demo_notice,
            text="ℹ Demonstration Notice: Cities, theatres, screens, and showtimes are sample data for college project evaluation.",
            font=FONT_BADGE,
            fg="#92400E",
            bg="#FFFBEB"
        ).pack(anchor="w")

        sep = tk.Frame(details_frame, bg=BORDER_COLOR, height=1)
        sep.pack(fill="x", pady=(0, 12))

        tk.Label(
            details_frame,
            text="ABOUT THE MOVIE",
            font=FONT_BADGE,
            fg=TEXT_MUTED,
            bg=BG_CARD
        ).pack(anchor="w")

        desc_lbl = tk.Label(
            details_frame,
            text=self.movie.description,
            font=FONT_BODY,
            fg=TEXT_PRIMARY,
            bg=BG_CARD,
            wraplength=780,
            justify="left"
        )
        desc_lbl.pack(anchor="w", pady=(4, 14))

        # Responsive text wrap adaptation
        def _on_details_resize(event):
            w = max(400, event.width - 24)
            title_lbl.config(wraplength=w)
            desc_lbl.config(wraplength=w)
        details_frame.bind("<Configure>", _on_details_resize)

        info_grid = tk.Frame(details_frame, bg=BG_CARD)
        info_grid.pack(fill="x", anchor="w")

        tk.Label(info_grid, text="Director:", font=FONT_SMALL_BOLD, fg=TEXT_MUTED, bg=BG_CARD).grid(row=0, column=0, sticky="w", pady=2)
        tk.Label(info_grid, text=self.movie.director, font=FONT_SMALL, fg=TEXT_PRIMARY, bg=BG_CARD).grid(row=0, column=1, sticky="w", padx=10, pady=2)

        tk.Label(info_grid, text="Starring:", font=FONT_SMALL_BOLD, fg=TEXT_MUTED, bg=BG_CARD).grid(row=1, column=0, sticky="w", pady=2)
        tk.Label(info_grid, text=self.movie.cast, font=FONT_SMALL, fg=TEXT_PRIMARY, bg=BG_CARD).grid(row=1, column=1, sticky="w", padx=10, pady=2)

    def _build_city_and_date_section(self) -> None:
        """City selector bar, date selector tabs, and theatre showtime cards."""
        self.shows_section_frame = tk.Frame(self.main_wrapper, bg=BG_PAGE)
        self.shows_section_frame.pack(fill="x", pady=(0, 24))

        # 1. City Selection Row
        city_row = tk.Frame(self.shows_section_frame, bg=BG_PAGE)
        city_row.pack(fill="x", pady=(0, 12))

        tk.Label(
            city_row,
            text="📍 SELECT CITY:",
            font=FONT_BADGE,
            fg=TEXT_MUTED,
            bg=BG_PAGE
        ).pack(side="left", padx=(0, 12))

        cities = self.db.get_cities()
        if not cities:
            sample_city_names = ["Chennai", "Hyderabad", "Bengaluru", "Mumbai", "Kochi"]
        else:
            sample_city_names = [c.name for c in cities]

        for c_name in sample_city_names:
            is_active = (c_name.lower() == self.selected_city.lower())
            btn = tk.Label(
                city_row,
                text=c_name,
                font=FONT_BODY_BOLD,
                bg=ACCENT_RED if is_active else BG_CARD,
                fg="#FFFFFF" if is_active else TEXT_PRIMARY,
                padx=14,
                pady=6,
                cursor="hand2",
                highlightthickness=1,
                highlightbackground=ACCENT_RED if is_active else BORDER_CARD
            )
            btn.pack(side="left", padx=(0, 8))
            btn.bind("<Button-1>", lambda e, cn=c_name: self._on_city_selected(cn))
            self.city_buttons[c_name] = btn

        # Price legend on the right
        price_tags = tk.Frame(city_row, bg=BG_PAGE)
        price_tags.pack(side="right")

        for name, col, price in [("Classic", TIER_STANDARD, "₹150-180"),
                                 ("Elite", TIER_PREMIUM, "₹220-260"),
                                 ("Recliner", TIER_RECLINER, "₹300-380")]:
            tag = tk.Frame(price_tags, bg=BG_CARD, padx=8, pady=4,
                           highlightthickness=1, highlightbackground=BORDER_CARD)
            tag.pack(side="left", padx=4)
            tk.Frame(tag, bg=col, width=8, height=8).pack(side="left", padx=(0, 6))
            tk.Label(tag, text=f"{name}: {price}", font=FONT_BADGE, fg=TEXT_SECONDARY, bg=BG_CARD).pack(side="left")

        # 2. Date Selection Bar
        self.date_bar = tk.Frame(self.shows_section_frame, bg=BG_PAGE)
        self.date_bar.pack(fill="x", pady=(0, 16))

        # 3. Dynamic Theatre & Screen Shows Container
        self.theatres_box = tk.Frame(self.shows_section_frame, bg=BG_PAGE)
        self.theatres_box.pack(fill="x", pady=(0, 20))

        # 4. Bottom Sticky Action Bar: Summary & Proceed
        self.bottom_bar = tk.Frame(
            self.shows_section_frame,
            bg=BG_CARD,
            padx=20,
            pady=16,
            highlightthickness=1,
            highlightbackground=BORDER_CARD
        )
        self.bottom_bar.pack(fill="x")

        self.summary_lbl = tk.Label(
            self.bottom_bar,
            text="Please select a theatre and showtime above to proceed.",
            font=FONT_BODY,
            fg=TEXT_SECONDARY,
            bg=BG_CARD
        )
        self.summary_lbl.pack(side="left")

        self.proceed_btn = ModernButton(
            self.bottom_bar,
            text="Select Seats →",
            command=self._handle_proceed,
            bg=ACCENT_RED,
            hover_bg=ACCENT_RED_HOVER,
            state="disabled"
        )
        self.proceed_btn.pack(side="right")

        self._refresh_dates_and_theatres()

    def _on_city_selected(self, city_name: str) -> None:
        """Switch current active city and reload available theatre schedules."""
        if self.selected_city == city_name:
            return
        self.selected_city = city_name
        self.selected_show = None
        self.proceed_btn.set_state("disabled")
        self.summary_lbl.config(
            text="Please select a theatre and showtime slot to proceed.",
            fg=TEXT_SECONDARY
        )

        for cn, btn in self.city_buttons.items():
            if cn.lower() == city_name.lower():
                btn.config(bg=ACCENT_RED, fg="#FFFFFF", highlightbackground=ACCENT_RED)
            else:
                btn.config(bg=BG_CARD, fg=TEXT_PRIMARY, highlightbackground=BORDER_CARD)

        self._refresh_dates_and_theatres()

    def _refresh_dates_and_theatres(self) -> None:
        """Reload available dates for movie in selected city, then render theatres."""
        for w in self.date_bar.winfo_children():
            w.destroy()
        self.date_buttons.clear()

        dates = self.db.get_show_dates_for_movie_and_city(self.movie.id, self.selected_city)
        if not dates:
            # Fallback to general dates if city specific has none
            dates = self.db.get_show_dates_for_movie(self.movie.id)

        if not dates:
            for w in self.theatres_box.winfo_children():
                w.destroy()

            empty_card = tk.Frame(
                self.theatres_box,
                bg=BG_CARD,
                padx=28,
                pady=24,
                highlightthickness=1,
                highlightbackground=BORDER_CARD
            )
            empty_card.pack(fill="x", pady=16)

            tk.Label(
                empty_card,
                text="📅 No Scheduled Showtimes Configured Yet",
                font=FONT_TITLE,
                fg=TEXT_PRIMARY,
                bg=BG_CARD
            ).pack(anchor="w")

            tk.Label(
                empty_card,
                text=f"There are currently no active demonstration showtimes in {self.selected_city} for '{self.movie.title}'. "
                     "Would you like to generate demonstration showtimes for this Indian film?",
                font=FONT_BODY,
                fg=TEXT_SECONDARY,
                bg=BG_CARD,
                wraplength=640,
                justify="left"
            ).pack(anchor="w", pady=(6, 16))

            gen_btn = ModernButton(
                empty_card,
                text="⚡ Add Demonstration Showtimes for this Movie",
                command=self._handle_generate_demo_shows,
                bg=ACCENT_RED,
                hover_bg=ACCENT_RED_HOVER
            )
            gen_btn.pack(anchor="w")
            return

        for d_str in dates:
            try:
                dt = datetime.strptime(d_str, "%Y-%m-%d")
                day_display = dt.strftime("%a, %d %b")
            except Exception:
                day_display = d_str

            btn = tk.Label(
                self.date_bar,
                text=day_display,
                font=FONT_BODY_BOLD,
                bg=BG_CARD,
                fg=TEXT_SECONDARY,
                padx=16,
                pady=8,
                cursor="hand2",
                highlightthickness=1,
                highlightbackground=BORDER_CARD
            )
            btn.pack(side="left", padx=(0, 8))
            btn.bind("<Button-1>", lambda e, d=d_str: self._on_date_selected(d))
            self.date_buttons[d_str] = btn

        self._on_date_selected(dates[0])

    def _on_date_selected(self, date_str: str) -> None:
        """Select a date tab and populate the theatres for that date."""
        self.selected_date = date_str
        self.selected_show = None
        self.proceed_btn.set_state("disabled")
        self.summary_lbl.config(
            text="Please click a showtime slot to proceed.",
            fg=TEXT_SECONDARY
        )

        for d, btn in self.date_buttons.items():
            if d == date_str:
                btn.config(bg=ACCENT_RED, fg="#FFFFFF", highlightbackground=ACCENT_RED)
            else:
                btn.config(bg=BG_CARD, fg=TEXT_SECONDARY, highlightbackground=BORDER_CARD)

        self._render_theatres_for_date()

    def _render_theatres_for_date(self) -> None:
        """Populates theatre cards, each containing its screens and clickable showtime slots."""
        for w in self.theatres_box.winfo_children():
            w.destroy()
        self.show_slot_buttons.clear()

        theatres_map = self.db.get_shows_grouped_by_theatre(
            self.movie.id,
            city_name=self.selected_city,
            show_date=self.selected_date
        )

        if not theatres_map:
            empty_card = tk.Frame(
                self.theatres_box,
                bg=BG_CARD,
                padx=24,
                pady=20,
                highlightthickness=1,
                highlightbackground=BORDER_CARD
            )
            empty_card.pack(fill="x", pady=16)

            tk.Label(
                empty_card,
                text=f"No shows scheduled in {self.selected_city} on this date.",
                font=FONT_SUBTITLE,
                fg=TEXT_PRIMARY,
                bg=BG_CARD
            ).pack(anchor="w")

            tk.Label(
                empty_card,
                text="Click below to add instant demonstration showtimes across screens for this date:",
                font=FONT_BODY,
                fg=TEXT_SECONDARY,
                bg=BG_CARD
            ).pack(anchor="w", pady=(4, 14))

            gen_btn = ModernButton(
                empty_card,
                text="⚡ Add Demonstration Showtimes",
                command=self._handle_generate_demo_shows,
                bg=ACCENT_RED,
                hover_bg=ACCENT_RED_HOVER
            )
            gen_btn.pack(anchor="w")
            return

        for t_name, t_info in theatres_map.items():
            theatre_obj: Theatre = t_info["theatre"]
            screens_dict: Dict[str, List[Show]] = t_info["screens"]

            # Theatre Card
            t_card = tk.Frame(
                self.theatres_box,
                bg=BG_CARD,
                padx=22,
                pady=18,
                highlightthickness=1,
                highlightbackground=BORDER_CARD
            )
            t_card.pack(fill="x", pady=8)

            # Theatre Header Row
            t_head = tk.Frame(t_card, bg=BG_CARD)
            t_head.pack(fill="x", pady=(0, 12))

            t_title_box = tk.Frame(t_head, bg=BG_CARD)
            t_title_box.pack(side="left")

            tk.Label(
                t_title_box,
                text=f"🏛 {theatre_obj.name}",
                font=FONT_CARD_TITLE,
                fg=TEXT_PRIMARY,
                bg=BG_CARD
            ).pack(anchor="w")

            loc_text = f"{theatre_obj.location} • {theatre_obj.address}" if theatre_obj.address else theatre_obj.location
            tk.Label(
                t_title_box,
                text=f"📍 {loc_text}",
                font=FONT_SMALL,
                fg=TEXT_MUTED,
                bg=BG_CARD
            ).pack(anchor="w", pady=(2, 0))

            # Amenities badges on right
            amenities_box = tk.Frame(t_head, bg=BG_CARD)
            amenities_box.pack(side="right")

            tk.Label(
                amenities_box,
                text="📱 M-Ticket  •  🍿 F&B  •  🅿️ Parking",
                font=FONT_BADGE,
                fg=ACCENT_CYAN,
                bg="#F0F9FF",
                padx=8,
                pady=4
            ).pack(side="right")

            tk.Frame(t_card, bg=BORDER_COLOR, height=1).pack(fill="x", pady=(0, 12))

            # Render Screens inside Theatre
            for scr_label, shows_list in screens_dict.items():
                scr_row = tk.Frame(t_card, bg=BG_CARD)
                scr_row.pack(fill="x", pady=4)

                scr_info = tk.Frame(scr_row, bg=BG_CARD, width=280)
                scr_info.pack(side="left", fill="y", padx=(0, 16))
                scr_info.pack_propagate(False)

                first_show = shows_list[0]
                tk.Label(
                    scr_info,
                    text=f"🎬 {scr_label}",
                    font=FONT_BODY_BOLD,
                    fg=TEXT_PRIMARY,
                    bg=BG_CARD
                ).pack(anchor="w")

                price_summary = f"Classic ₹{int(first_show.price_classic)} | Elite ₹{int(first_show.price_elite)} | Recliner ₹{int(first_show.price_recliner)}"
                tk.Label(
                    scr_info,
                    text=price_summary,
                    font=FONT_BADGE,
                    fg=TEXT_MUTED,
                    bg=BG_CARD
                ).pack(anchor="w", pady=(2, 0))

                # Showtime pill buttons
                slots_frame = tk.Frame(scr_row, bg=BG_CARD)
                slots_frame.pack(side="left", fill="x", expand=True)

                for show_obj in shows_list:
                    slot_btn = tk.Label(
                        slots_frame,
                        text=f"🕒 {show_obj.show_time}",
                        font=FONT_BODY_BOLD,
                        bg="#F5F5FA",
                        fg=TEXT_PRIMARY,
                        padx=14,
                        pady=7,
                        cursor="hand2",
                        highlightthickness=1,
                        highlightbackground=BORDER_CARD
                    )
                    slot_btn.pack(side="left", padx=(0, 10), pady=2)
                    slot_btn.bind("<Button-1>", lambda e, s=show_obj: self._on_show_selected(s))
                    slot_btn.bind("<Double-Button-1>", lambda e, s=show_obj: self._direct_proceed(s))
                    slot_btn.bind("<Enter>", lambda e, sid=show_obj.id: self._on_slot_enter(sid))
                    slot_btn.bind("<Leave>", lambda e, sid=show_obj.id: self._on_slot_leave(sid))
                    self.show_slot_buttons[show_obj.id] = slot_btn

        self.scroll_container.bind_mouse_wheel(self.theatres_box)

    def _on_slot_enter(self, show_id: int) -> None:
        if not (self.selected_show and self.selected_show.id == show_id):
            btn = self.show_slot_buttons.get(show_id)
            if btn:
                btn.config(bg="#FFF1F2", highlightbackground=ACCENT_RED)

    def _on_slot_leave(self, show_id: int) -> None:
        if not (self.selected_show and self.selected_show.id == show_id):
            btn = self.show_slot_buttons.get(show_id)
            if btn:
                btn.config(bg="#F5F5FA", highlightbackground=BORDER_CARD)

    def _on_show_selected(self, show: Show) -> None:
        """User clicked a showtime slot."""
        was_already_selected = (self.selected_show is not None and self.selected_show.id == show.id)
        self.selected_show = show

        for s_id, btn in self.show_slot_buttons.items():
            if s_id == show.id:
                btn.config(bg=ACCENT_RED, fg="#FFFFFF", highlightbackground=ACCENT_RED)
            else:
                btn.config(bg="#F5F5FA", fg=TEXT_PRIMARY, highlightbackground=BORDER_CARD)

        theatre_name = getattr(show, "theatre_name", "Cinema")
        screen_name = getattr(show, "screen_name", "Audi")
        self.summary_lbl.config(
            text=f"Selected: {theatre_name} — {screen_name} on {show.formatted_datetime}",
            fg=TEXT_PRIMARY
        )
        self.proceed_btn.set_state("normal")

        if was_already_selected:
            self._handle_proceed()

    def _direct_proceed(self, show: Show) -> None:
        """Directly proceed to seat layout on double click."""
        self.selected_show = show
        self._handle_proceed()

    def _handle_proceed(self) -> None:
        """Navigate to seat selection for selected show."""
        if not self.selected_show:
            messagebox.showwarning("Select Showtime", "Please select a showtime slot before proceeding.")
            return
        self.on_proceed_to_seats(self.selected_show)


    def _handle_generate_demo_shows(self) -> None:
        """Dynamically add demo showtimes for this movie and refresh view."""
        count = self.db.generate_demo_shows_for_movie(self.movie.id, self.selected_city)
        if count > 0:
            messagebox.showinfo(
                "Demo Showtimes Added",
                f"Successfully generated {count} demonstration showtime slots for '{self.movie.title}' in {self.selected_city}!"
            )
        else:
            messagebox.showinfo("Showtimes Ready", "Demonstration showtimes are configured and available.")
        self._refresh_dates_and_theatres()
