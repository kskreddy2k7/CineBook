"""
CineBook — Premium Indian Movie Discovery Home Screen
Inspired by BookMyShow (https://in.bookmyshow.com/explore/movies-hyderabad)

Architecture & Features:
- Native desktop responsive layout expanding across the full available window width.
- Movie discovery toolbar with Category (Now Showing / Upcoming / All), Genre, and Language pills.
- Curated Recommended Movies horizontal carousel with 2:3 portrait cards, ratings strip, and baseline-aligned buttons.
- Full-width CineBook Stream promotional cinema banner.
- Explore All Movies complete catalogue grid (all 20 Indian Cinema titles) with adaptive multi-column responsive layout.
- Debounced resize engine maintaining exact 2:3 poster aspect ratios and baseline button alignment at all resolutions.
- Direct integration with CineBook ACID booking engine: every Book Tickets button opens the real booking flow.
"""

from typing import Callable, List, Optional
import tkinter as tk
from tkinter import ttk

from database import DatabaseManager
from models import Movie
from ui.theme import (
    BG_PAGE, BG_CARD, BG_INPUT, BORDER_COLOR, BORDER_LIGHT, BORDER_CARD,
    ACCENT_RED, ACCENT_RED_HOVER, ACCENT_RED_LIGHT, ACCENT_CYAN, ACCENT_GOLD,
    TEXT_PRIMARY, TEXT_SECONDARY, TEXT_MUTED, TEXT_DARK, TEXT_LIGHT,
    FONT_HERO, FONT_TITLE, FONT_SUBTITLE, FONT_CARD_TITLE,
    FONT_BODY, FONT_BODY_BOLD, FONT_SMALL, FONT_SMALL_BOLD, FONT_BADGE,
    MAX_CONTENT_WIDTH, PAD_DESKTOP, PAD_TABLET, PAD_COMPACT,
    CARD_GAP_DEFAULT, CARD_WIDTH_MIN, CARD_WIDTH_MAX, CARD_ASPECT_RATIO,
    SECTION_SPACING, BANNER_HEIGHT
)
from ui.components import (
    MovieCardWidget, PromotionalBannerWidget, ScrollableFrame, ModernButton
)


class HomeView(tk.Frame):
    """Premium BookMyShow-style Indian Cinema Discovery Screen."""

    def __init__(
        self,
        master,
        db: DatabaseManager,
        on_select_movie: Callable[[Movie], None],
        on_view_bookings: Callable[[], None],
        search_query_var: Optional[tk.StringVar] = None,
        **kwargs
    ):
        super().__init__(master, bg=BG_PAGE, **kwargs)
        self.db = db
        self.on_select_movie = on_select_movie
        self.on_view_bookings = on_view_bookings

        # State management
        self.current_category = "Now Showing"   # "Now Showing", "Upcoming", "All"
        self.current_genre = "All"
        self.current_language = "All"
        self.carousel_start_idx = 0
        self.cards_per_view = 4
        self.current_card_w = 300
        self.current_poster_h = int(300 * 1.5) + 44
        self.current_card_h = self.current_poster_h + 210
        self._resize_timer = None

        # Search variable trace
        self.search_var = search_query_var if search_query_var is not None else tk.StringVar()
        self._search_trace_id = self.search_var.trace_add("write", self._safe_search_changed)
        self.bind("<Destroy>", self._cleanup_trace)

        # Main scrollable canvas container
        self.scroll_container = ScrollableFrame(self, bg=BG_PAGE)
        self.scroll_container.pack(fill="both", expand=True)
        self.content = self.scroll_container.scrollable_content

        # Full-width content wrapper
        self.main_wrapper = tk.Frame(self.content, bg=BG_PAGE)
        self.main_wrapper.pack(fill="x", padx=PAD_DESKTOP, pady=(14, 36))

        # Build primary discovery sections
        self._build_toolbar_section()
        self._build_recommended_section()
        self._build_stream_banner_section()
        self._build_all_movies_section()

        # Bind debounced window resize
        self.bind("<Configure>", self._on_window_resize)

    def _cleanup_trace(self, event=None) -> None:
        if event and event.widget == self:
            if self._resize_timer is not None:
                try:
                    self.after_cancel(self._resize_timer)
                except Exception:
                    pass
            try:
                self.search_var.trace_remove("write", self._search_trace_id)
            except Exception:
                pass

    def _safe_search_changed(self, *args) -> None:
        if not self.winfo_exists():
            return
        self.carousel_start_idx = 0
        self._refresh_all_views()

    # ==========================================================================
    # RESPONSIVE FULL-WIDTH LAYOUT ENGINE
    # ==========================================================================
    def _on_window_resize(self, event=None) -> None:
        """Debounced responsive layout calculation to prevent resize-event loops."""
        if event and event.widget != self:
            return
        if self._resize_timer is not None:
            try:
                self.after_cancel(self._resize_timer)
            except Exception:
                pass
        self._resize_timer = self.after(35, self._apply_responsive_layout)

    def _apply_responsive_layout(self) -> None:
        """Calculates dynamic margins, grid column counts, and proportional card dimensions."""
        if not self.winfo_exists():
            return
        w = self.winfo_width()
        if w < 100:
            return

        # 1. Responsive horizontal padding policy
        if w >= 1280:
            pad = PAD_DESKTOP  # 28 px
        elif w >= 768:
            pad = PAD_TABLET   # 18 px
        else:
            pad = PAD_COMPACT  # 12 px

        try:
            self.main_wrapper.pack_configure(padx=pad)
        except Exception:
            pass

        # 2. Available content width accounting for scrollbar and side margins
        available_w = max(280, w - 2 * pad - 18)

        # 3. Adaptive column calculation matching BookMyShow breakpoint targets
        if available_w >= 1550:
            cols = 5
        elif available_w >= 1150:
            cols = 4
        elif available_w >= 780:
            cols = 3
        elif available_w >= 500:
            cols = 2
        else:
            cols = 1

        # 4. Proportional card width that distributes evenly across available width
        gap = 18  # Consistent 18 px inter-card gap

        raw_card_w = (available_w - (cols - 1) * gap) // cols
        card_w = max(260, min(420, raw_card_w))
        poster_w = card_w
        image_h = int(poster_w * 1.5)  # Strict 2:3 portrait ratio
        strip_h = 44
        poster_h = image_h + strip_h
        info_h = 210
        card_h = poster_h + info_h

        changed = (cols != self.cards_per_view or card_w != self.current_card_w)
        self.cards_per_view = cols
        self.current_card_w = card_w
        self.current_card_h = card_h
        self.current_poster_h = poster_h

        if changed:
            self._render_carousel()
            self._render_all_movies_grid()

    # ==========================================================================
    # SECTION 1: MOVIE DISCOVERY TOOLBAR (CATEGORY, GENRE & LANGUAGE PILLS)
    # ==========================================================================
    def _build_toolbar_section(self) -> None:
        """BookMyShow-style discovery filter toolbar with status, genre, and language pills."""
        toolbar_card = tk.Frame(self.main_wrapper, bg=BG_PAGE)
        toolbar_card.pack(fill="x", pady=(0, 22))

        # --- Row 1: Release Status Pills + Clear Action ---
        row1 = tk.Frame(toolbar_card, bg=BG_PAGE)
        row1.pack(fill="x", pady=(0, 10))

        # Status Tabs (Now Showing, Upcoming, All)
        status_frame = tk.Frame(row1, bg=BG_PAGE)
        status_frame.pack(side="left")

        self.cat_buttons = {}
        for cat in ["Now Showing", "Upcoming", "All"]:
            is_active = (cat == self.current_category)
            btn = tk.Label(
                status_frame,
                text=cat,
                font=FONT_BODY_BOLD,
                bg=ACCENT_RED if is_active else BG_CARD,
                fg="#FFFFFF" if is_active else TEXT_PRIMARY,
                padx=16,
                pady=7,
                cursor="hand2",
                highlightthickness=1,
                highlightbackground=ACCENT_RED if is_active else BORDER_CARD
            )
            btn.pack(side="left", padx=(0, 6))
            btn.bind("<Button-1>", lambda e, c=cat: self._on_category_clicked(c))
            self.cat_buttons[cat] = btn

        # Language Pills (Hindi, Telugu, Tamil, Malayalam, Kannada)
        lang_frame = tk.Frame(row1, bg=BG_PAGE)
        lang_frame.pack(side="left", padx=(18, 0))

        tk.Label(
            lang_frame,
            text="LANGUAGES:",
            font=FONT_BADGE,
            fg=TEXT_MUTED,
            bg=BG_PAGE
        ).pack(side="left", padx=(0, 8))

        languages = ["All", "Telugu", "Hindi", "Tamil", "Malayalam", "Kannada"]
        self.lang_buttons = {}
        for lang in languages:
            is_act = (lang == self.current_language)
            btn = tk.Label(
                lang_frame,
                text=lang,
                font=FONT_SMALL_BOLD,
                bg=ACCENT_RED if is_act else BG_CARD,
                fg="#FFFFFF" if is_act else TEXT_SECONDARY,
                padx=10,
                pady=5,
                cursor="hand2",
                highlightthickness=1,
                highlightbackground=ACCENT_RED if is_act else BORDER_CARD
            )
            btn.pack(side="left", padx=2)
            btn.bind("<Button-1>", lambda e, l=lang: self._on_language_clicked(l))
            self.lang_buttons[lang] = btn

        # Clear Filters Button (Right)
        self.reset_btn = tk.Label(
            row1,
            text="Reset Filters ✖",
            font=FONT_SMALL_BOLD,
            bg="#F1F5F9",
            fg=TEXT_MUTED,
            padx=12,
            pady=5,
            cursor="hand2",
            highlightthickness=1,
            highlightbackground="#CBD5E1"
        )
        self.reset_btn.pack(side="right")
        self.reset_btn.bind("<Button-1>", lambda e: self._reset_filters())

        # --- Row 2: Genre Filter Chips ---
        row2 = tk.Frame(toolbar_card, bg=BG_PAGE)
        row2.pack(fill="x")

        tk.Label(
            row2,
            text="GENRES:",
            font=FONT_BADGE,
            fg=TEXT_MUTED,
            bg=BG_PAGE
        ).pack(side="left", padx=(0, 8))

        genres = ["All", "Action", "Drama", "Crime", "Comedy", "Thriller", "Sci-Fi", "Animation", "Fantasy", "Biography"]
        self.genre_buttons = {}
        for g in genres:
            is_act = (g == self.current_genre)
            btn = tk.Label(
                row2,
                text=g,
                font=FONT_SMALL,
                bg=ACCENT_RED if is_act else BG_CARD,
                fg="#FFFFFF" if is_act else TEXT_SECONDARY,
                padx=11,
                pady=4,
                cursor="hand2",
                highlightthickness=1,
                highlightbackground=ACCENT_RED if is_act else BORDER_CARD
            )
            btn.pack(side="left", padx=2)
            btn.bind("<Button-1>", lambda e, genre=g: self._on_genre_clicked(genre))
            self.genre_buttons[g] = btn

    def _on_category_clicked(self, cat: str) -> None:
        self.current_category = cat
        for c, btn in self.cat_buttons.items():
            if c == cat:
                btn.config(bg=ACCENT_RED, fg="#FFFFFF", highlightbackground=ACCENT_RED)
            else:
                btn.config(bg=BG_CARD, fg=TEXT_PRIMARY, highlightbackground=BORDER_CARD)
        self.carousel_start_idx = 0
        self._refresh_all_views()

    def _on_language_clicked(self, lang: str) -> None:
        self.current_language = lang
        for l, btn in self.lang_buttons.items():
            if l == lang:
                btn.config(bg=ACCENT_RED, fg="#FFFFFF", highlightbackground=ACCENT_RED)
            else:
                btn.config(bg=BG_CARD, fg=TEXT_SECONDARY, highlightbackground=BORDER_CARD)
        self.carousel_start_idx = 0
        self._refresh_all_views()

    def _on_genre_clicked(self, genre: str) -> None:
        self.current_genre = genre
        for g, btn in self.genre_buttons.items():
            if g == genre:
                btn.config(bg=ACCENT_RED, fg="#FFFFFF", highlightbackground=ACCENT_RED)
            else:
                btn.config(bg=BG_CARD, fg=TEXT_SECONDARY, highlightbackground=BORDER_CARD)
        self.carousel_start_idx = 0
        self._refresh_all_views()

    # ==========================================================================
    # SECTION 2: RECOMMENDED MOVIES (CURATED HORIZONTAL CAROUSEL)
    # ==========================================================================
    def _build_recommended_section(self) -> None:
        """Curated Recommended Movies Section with adaptive horizontal carousel."""
        self.rec_section = tk.Frame(self.main_wrapper, bg=BG_PAGE)
        self.rec_section.pack(fill="x", pady=(0, SECTION_SPACING))

        # Header: Title on left, "See All ›" and carousel arrows on right
        sec_header = tk.Frame(self.rec_section, bg=BG_PAGE)
        sec_header.pack(fill="x", pady=(0, 14))

        title_frame = tk.Frame(sec_header, bg=BG_PAGE)
        title_frame.pack(side="left")

        self.sec_title_lbl = tk.Label(
            title_frame,
            text="Recommended Movies",
            font=("Segoe UI", 24, "bold"),
            fg=TEXT_PRIMARY,
            bg=BG_PAGE
        )
        self.sec_title_lbl.pack(side="left")

        self.sec_sub_lbl = tk.Label(
            title_frame,
            text="Curated blockbuster & critical hits in Indian cinema",
            font=("Segoe UI", 13, "normal"),
            fg="#64748B",
            bg=BG_PAGE
        )
        self.sec_sub_lbl.pack(side="left", padx=(14, 0))

        # Right Action Area: See All Link + Nav Arrows
        right_actions = tk.Frame(sec_header, bg=BG_PAGE)
        right_actions.pack(side="right")

        see_all_lbl = tk.Label(
            right_actions,
            text="See All ›",
            font=("Segoe UI", 15, "bold"),
            fg=ACCENT_RED,
            bg=BG_PAGE,
            cursor="hand2"
        )
        see_all_lbl.pack(side="left", padx=(0, 16))
        see_all_lbl.bind("<Button-1>", lambda e: self._on_see_all_clicked())

        # Side Arrows (‹ and ›)
        self.prev_btn = tk.Label(
            right_actions,
            text="‹",
            font=("Segoe UI", 24, "bold"),
            fg="#CBD5E1",
            bg=BG_PAGE,
            cursor="arrow",
            padx=4
        )
        self.prev_btn.pack(side="left", padx=2)
        self.prev_btn.bind("<Button-1>", lambda e: self._carousel_prev())

        self.next_btn = tk.Label(
            right_actions,
            text="›",
            font=("Segoe UI", 24, "bold"),
            fg=TEXT_PRIMARY,
            bg=BG_PAGE,
            cursor="hand2",
            padx=4
        )
        self.next_btn.pack(side="left", padx=2)
        self.next_btn.bind("<Button-1>", lambda e: self._carousel_next())

        # Carousel Card Row Frame
        carousel_container = tk.Frame(self.rec_section, bg=BG_PAGE)
        carousel_container.pack(fill="x")

        self.card_row = tk.Frame(carousel_container, bg=BG_PAGE)
        self.card_row.pack(fill="x", expand=True)

        self._render_carousel()

    def _render_carousel(self) -> None:
        """Renders the visible window of recommended movie cards."""
        if not self.winfo_exists() or not self.card_row.winfo_exists():
            return
        for w in self.card_row.winfo_children():
            w.destroy()

        rec_movies = self._get_recommended_movies()
        total_movies = len(rec_movies)

        if total_movies == 0:
            empty_lbl = tk.Label(
                self.card_row,
                text="No recommended titles match the active filters.",
                font=FONT_BODY,
                fg=TEXT_MUTED,
                bg=BG_PAGE,
                pady=20
            )
            empty_lbl.pack()
            self.prev_btn.config(fg="#CBD5E1", cursor="arrow")
            self.next_btn.config(fg="#CBD5E1", cursor="arrow")
            return

        cols = self.cards_per_view
        start = self.carousel_start_idx
        end = min(start + cols, total_movies)
        visible = rec_movies[start:end]

        for col in range(cols):
            self.card_row.columnconfigure(col, weight=1, uniform="rec_col")

        gap = 18

        for col_idx, movie in enumerate(visible):
            card = MovieCardWidget(
                self.card_row,
                movie=movie,
                on_select=self.on_select_movie,
                width=self.current_card_w,
                height=self.current_card_h,
                poster_w=self.current_card_w,
                poster_h=self.current_poster_h,
                promoted=(col_idx == 0 and self.carousel_start_idx == 0 and self.current_genre == "All")
            )
            card.grid(row=0, column=col_idx, padx=gap // 2, pady=0, sticky="nsew")

        # Arrow state updates
        has_prev = self.carousel_start_idx > 0
        self.prev_btn.config(
            fg=TEXT_PRIMARY if has_prev else "#CBD5E1",
            cursor="hand2" if has_prev else "arrow"
        )
        has_next = end < total_movies
        self.next_btn.config(
            fg=TEXT_PRIMARY if has_next else "#CBD5E1",
            cursor="hand2" if has_next else "arrow"
        )

    def _carousel_prev(self) -> None:
        if self.carousel_start_idx > 0:
            self.carousel_start_idx -= 1
            self._render_carousel()

    def _carousel_next(self) -> None:
        rec_movies = self._get_recommended_movies()
        if self.carousel_start_idx + self.cards_per_view < len(rec_movies):
            self.carousel_start_idx += 1
            self._render_carousel()

    # ==========================================================================
    # SECTION 3: PROMOTIONAL STREAM CINEMA BANNER
    # ==========================================================================
    def _build_stream_banner_section(self) -> None:
        """Full-width promotional cinema banner (CineBook Stream & Premiere Releases)."""
        banner_wrap = tk.Frame(self.main_wrapper, bg=BG_PAGE)
        banner_wrap.pack(fill="x", pady=(0, SECTION_SPACING))

        self.promo_banner = PromotionalBannerWidget(
            banner_wrap,
            height=BANNER_HEIGHT,
            on_click=self._on_see_all_clicked
        )
        self.promo_banner.pack(fill="x")

    # ==========================================================================
    # SECTION 4: EXPLORE ALL MOVIES (FULL CATALOGUE RESPONSIVE GRID)
    # ==========================================================================
    def _build_all_movies_section(self) -> None:
        """Full Movie Catalogue with Adaptive Responsive Grid."""
        self.all_section = tk.Frame(self.main_wrapper, bg=BG_PAGE)
        self.all_section.pack(fill="x", pady=(0, 20))

        # Title & Count Badge
        sec_header = tk.Frame(self.all_section, bg=BG_PAGE)
        sec_header.pack(fill="x", pady=(0, 14))

        self.catalog_title_lbl = tk.Label(
            sec_header,
            text="Explore All Movies",
            font=("Segoe UI", 24, "bold"),
            fg=TEXT_PRIMARY,
            bg=BG_PAGE
        )
        self.catalog_title_lbl.pack(side="left")

        self.count_lbl = tk.Label(
            sec_header,
            text="",
            font=("Segoe UI", 13, "normal"),
            fg="#64748B",
            bg=BG_PAGE
        )
        self.count_lbl.pack(side="left", padx=(12, 0))

        # Grid Container
        self.grid_container = tk.Frame(self.all_section, bg=BG_PAGE)
        self.grid_container.pack(fill="x")

        self._render_all_movies_grid()

    def _render_all_movies_grid(self) -> None:
        """Renders all matching catalogue entries in an adaptive responsive grid."""
        if not self.winfo_exists() or not self.grid_container.winfo_exists():
            return
        for w in self.grid_container.winfo_children():
            w.destroy()

        movies = self._get_filtered_movies()
        self.count_lbl.config(text=f"({len(movies)} Titles Available)")

        if not movies:
            empty_box = tk.Frame(
                self.grid_container,
                bg=BG_CARD,
                padx=30,
                pady=40,
                highlightthickness=1,
                highlightbackground=BORDER_CARD
            )
            empty_box.pack(fill="x", expand=True, pady=16)

            tk.Label(empty_box, text="🎬", font=("Segoe UI", 36), bg=BG_CARD, fg=TEXT_MUTED).pack()
            tk.Label(empty_box, text="No Movies Found", font=FONT_TITLE, bg=BG_CARD, fg=TEXT_PRIMARY).pack(pady=(6, 2))
            tk.Label(
                empty_box,
                text="Try searching for another movie title, or reset genre/language filters.",
                font=FONT_BODY,
                bg=BG_CARD,
                fg=TEXT_SECONDARY
            ).pack(pady=(0, 16))

            clear_btn = ModernButton(empty_box, text="Reset Search & Filters", command=self._reset_filters)
            clear_btn.pack()
            return

        gap = 18
        cols = self.cards_per_view

        for col in range(cols):
            self.grid_container.columnconfigure(col, weight=1, uniform="all_col")

        for idx, movie in enumerate(movies):
            row = idx // cols
            col = idx % cols

            card = MovieCardWidget(
                self.grid_container,
                movie=movie,
                on_select=self.on_select_movie,
                width=self.current_card_w,
                height=self.current_card_h,
                poster_w=self.current_card_w,
                poster_h=self.current_poster_h,
                promoted=(idx == 0 and self.current_genre == "All" and self.current_language == "All")
            )
            card.grid(row=row, column=col, padx=gap // 2, pady=(0, 20), sticky="nsew")

        # Recompute canvas scroll region so the entire catalogue is scrollable without clipping
        self.scroll_container._on_frame_configure()

    # ==========================================================================
    # DATA RETRIEVAL & FILTER LOGIC
    # ==========================================================================
    def _get_recommended_movies(self) -> List[Movie]:
        """
        Curated selection of top-rated blockbuster recommended Indian films.
        Distinct from the full Explore All catalogue.
        """
        all_matches = self._get_filtered_movies(language="All")
        # Curated recommendations prioritize top-rated titles
        sorted_by_rating = sorted(
            all_matches,
            key=lambda m: m.rating,
            reverse=True
        )
        return sorted_by_rating[:10]

    def _get_filtered_movies(self, language: Optional[str] = None) -> List[Movie]:
        """Queries the full movie catalogue with search term, genre, language, and category filtering."""
        query = self.search_var.get().strip()
        genre_filter = self.current_genre if self.current_genre != "All" else None
        cat_filter = self.current_category if self.current_category != "All" else None
        lang_filter = language if language is not None else self.current_language

        movies = self.db.get_all_movies(
            search_query=query,
            genre=genre_filter,
            category=cat_filter
        )

        if lang_filter and lang_filter != "All":
            movies = [
                m for m in movies
                if lang_filter.lower() in getattr(m, "language", "").lower()
                or lang_filter.lower() in getattr(m, "industry", "").lower()
            ]

        return movies

    def _refresh_all_views(self) -> None:
        if not self.winfo_exists():
            return
        self._render_carousel()
        self._render_all_movies_grid()

    def _on_see_all_clicked(self) -> None:
        """Scroll down smoothly to the All Movies section."""
        self._reset_filters()
        self.scroll_container.canvas.yview_moveto(0.48)

    def _reset_filters(self) -> None:
        """Reset search and all filter pills to default state."""
        self.search_var.set("")
        self.current_category = "Now Showing"
        self.current_genre = "All"
        self.current_language = "All"

        for c, btn in self.cat_buttons.items():
            btn.config(
                bg=ACCENT_RED if c == "Now Showing" else BG_CARD,
                fg="#FFFFFF" if c == "Now Showing" else TEXT_PRIMARY,
                highlightbackground=ACCENT_RED if c == "Now Showing" else BORDER_CARD
            )
        for g, btn in self.genre_buttons.items():
            btn.config(
                bg=ACCENT_RED if g == "All" else BG_CARD,
                fg="#FFFFFF" if g == "All" else TEXT_SECONDARY,
                highlightbackground=ACCENT_RED if g == "All" else BORDER_CARD
            )
        for lang, btn in self.lang_buttons.items():
            btn.config(
                bg=ACCENT_RED if lang == "All" else BG_CARD,
                fg="#FFFFFF" if lang == "All" else TEXT_SECONDARY,
                highlightbackground=ACCENT_RED if lang == "All" else BORDER_CARD
            )
        self.carousel_start_idx = 0
        self._refresh_all_views()
