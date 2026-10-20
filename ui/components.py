"""
CineBook - UI Components Module
Reusable graphical widgets, image renderers, BookMyShow-style movie card,
cinema screen indicator, seat matrix buttons, stat cards, and scrollable containers.
"""

from pathlib import Path
from typing import Callable, Optional
import tkinter as tk
from tkinter import ttk

from ui.theme import (
    BG_PAGE, BG_CARD, BG_INPUT, BORDER_COLOR, BORDER_LIGHT, BORDER_CARD,
    ACCENT_RED, ACCENT_RED_HOVER, ACCENT_RED_LIGHT, ACCENT_CYAN, ACCENT_GOLD,
    COLOR_SUCCESS, COLOR_DANGER, COLOR_WARNING,
    TEXT_PRIMARY, TEXT_SECONDARY, TEXT_MUTED, TEXT_DARK, TEXT_LIGHT,
    FONT_HERO, FONT_TITLE, FONT_SUBTITLE, FONT_CARD_TITLE, FONT_BTN,
    FONT_BODY, FONT_BODY_BOLD, FONT_SMALL, FONT_SMALL_BOLD, FONT_BADGE,
    TIER_RECLINER, TIER_PREMIUM, TIER_STANDARD,
    SEAT_SELECTED_BG, SEAT_SELECTED_BORDER, SEAT_BOOKED_BG, SEAT_BOOKED_BORDER,
    CARD_ASPECT_RATIO, CARD_WIDTH_MIN, CARD_WIDTH_MAX, BANNER_HEIGHT, BUTTON_HEIGHT
)

try:
    from PIL import Image, ImageTk, ImageOps, ImageDraw
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False

# Global in-memory cache for resized PhotoImage objects
_POSTER_CACHE = {}


class PosterWidget(tk.Canvas):
    """
    Renders movie poster with smooth PIL scaling in portrait ~2:3 aspect ratio.
    Features:
    - Aspect-preserving image scaling with LANCZOS resampling.
    - BookMyShow-style dark rating strip directly beneath the poster image (⭐ 8.6/10).
    - Optional PROMOTED tag on top-left.
    - Attractive procedural canvas fallback if image file is missing.
    """

    def __init__(
        self,
        master,
        image_path: Optional[str],
        width: int = 300,
        height: int = 494,
        title: str = "Movie",
        genre: str = "Cinema",
        rating: float = 8.5,
        votes: str = "14.2K",
        promoted: bool = False,
        is_upcoming: bool = False,
        banner_color: str = "#1E293B",
        on_click: Optional[Callable[[], None]] = None,
        corner_radius: int = 10,
        strip_height: int = 44,
        **kwargs
    ):
        super().__init__(
            master,
            width=width,
            height=height,
            bg=BG_PAGE,
            highlightthickness=0,
            cursor="hand2" if on_click else "arrow",
            **kwargs
        )
        self.target_w = width
        self.target_h = height
        self.strip_h = strip_height
        self.image_path = image_path
        self.title = title
        self.genre = genre
        self.rating = rating
        self.votes = votes
        self.promoted = promoted
        self.is_upcoming = is_upcoming
        self.banner_color = banner_color
        self.corner_radius = corner_radius
        self.on_click = on_click
        self._photo_ref = None

        if on_click:
            self.bind("<Button-1>", lambda e: on_click())

        self.bind("<Configure>", self._on_canvas_configure)
        self.render_poster()

    def _on_canvas_configure(self, event) -> None:
        """Lock portrait aspect ratio to prevent squashing into landscape."""
        pass

    def render_poster(self) -> None:
        """Attempt to load image file from cache/disk, otherwise draw professional unavailable state."""
        self.delete("all")
        strip_h = self.strip_h
        sy = max(10, self.target_h - strip_h)
        image_h = sy
        loaded = False
        if PIL_AVAILABLE and self.image_path:
            p = Path(self.image_path)
            if not p.is_absolute():
                p = Path(__file__).resolve().parent.parent / self.image_path

            # Prioritize authentic .jpg theatrical poster if present
            if p.suffix.lower() == ".png" and p.with_suffix(".jpg").exists():
                p = p.with_suffix(".jpg")
            elif not (p.exists() and p.is_file()):
                for ext in [".jpg", ".jpeg", ".png"]:
                    alt_p = p.with_suffix(ext)
                    if alt_p.exists() and alt_p.is_file():
                        p = alt_p
                        break

            if p.exists() and p.is_file():
                cache_key = (str(p), self.target_w, image_h, self.corner_radius)
                if cache_key in _POSTER_CACHE:
                    try:
                        self._photo_ref = _POSTER_CACHE[cache_key]
                        self.create_image(0, 0, anchor="nw", image=self._photo_ref)
                        loaded = True
                    except Exception:
                        _POSTER_CACHE.pop(cache_key, None)

                if not loaded:
                    try:
                        with Image.open(str(p)) as im:
                            # Preserve aspect ratio cleanly with ImageOps.fit into image_h area above strip
                            fit_img = ImageOps.fit(im, (self.target_w, image_h), method=Image.Resampling.LANCZOS).convert("RGBA")
                            # Blend rounded top corners seamlessly into BG_PAGE (#F2F4F8 -> 242, 244, 248)
                            base = Image.new("RGBA", (self.target_w, image_h), (242, 244, 248, 255))
                            mask = Image.new("L", (self.target_w, image_h), 0)
                            draw_mask = ImageDraw.Draw(mask)
                            draw_mask.rounded_rectangle(
                                (0, 0, self.target_w, image_h),
                                radius=self.corner_radius,
                                fill=255,
                                corners=(True, True, False, False)
                            )
                            base.paste(fit_img, (0, 0), mask=mask)
                            final_img = base.convert("RGB")
                            self._photo_ref = ImageTk.PhotoImage(final_img, master=self)
                            _POSTER_CACHE[cache_key] = self._photo_ref
                            self.create_image(0, 0, anchor="nw", image=self._photo_ref)
                            loaded = True
                    except Exception as e:
                        print(f"Notice: Could not load poster {p}: {e}. Using unavailable fallback.")

        if not loaded:
            self._draw_unavailable_fallback()

        # Draw BookMyShow Rating Strip directly attached to bottom of poster
        # High contrast dark rating strip background spanning full canvas width
        self.create_rectangle(0, sy, self.target_w, self.target_h, fill="#1A1C23", outline="")

        if self.rating and self.rating > 0 and not getattr(self, "is_upcoming", False):
            # Star icon (22 px bold)
            self.create_text(
                12, sy + strip_h // 2,
                text="★",
                fill="#F43F68",
                font=("Segoe UI", -22, "bold"),
                anchor="w"
            )
            # Rating value (19 px bold)
            rating_text = f"{self.rating:.1f}/10"
            self.create_text(
                42, sy + strip_h // 2,
                text=rating_text,
                fill="#FFFFFF",
                font=("Segoe UI", -19, "bold"),
                anchor="w"
            )
            # Votes count on right edge with ample clearance (15 px bold)
            votes_str = str(self.votes)
            if not votes_str.lower().endswith("votes"):
                votes_str += " Votes"
            self.create_text(
                self.target_w - 14, sy + strip_h // 2,
                text=votes_str,
                fill="#F1F5F9",
                font=("Segoe UI", -15, "bold"),
                anchor="e"
            )
        else:
            self.create_text(
                self.target_w // 2, sy + strip_h // 2,
                text="🎟️  UPCOMING PREVIEW",
                fill=ACCENT_GOLD,
                font=("Segoe UI", -16, "bold")
            )

        # Promoted Badge on top-left if applicable
        if self.promoted:
            self.create_rectangle(12, 12, 124, 40, fill="#111111", outline="")
            self.create_text(68, 26, text="PROMOTED", fill="#FFFFFF", font=("Segoe UI", 11, "bold"))

    def _draw_unavailable_fallback(self) -> None:
        """Draw a clean, clearly labeled unavailable-poster placeholder."""
        w, h = self.target_w, self.target_h

        # Solid dark cinema slate background
        self.create_rectangle(0, 0, w, h, fill="#1E293B", outline="")

        # Cinema clapper / camera symbol
        self.create_text(w // 2, h // 3 - 10, text="🎬", font=("Segoe UI", 36), fill="#94A3B8")

        # Label: THEATRICAL POSTER UNAVAILABLE
        self.create_text(w // 2, h // 2 - 10, text="POSTER UNAVAILABLE", fill="#E2E8F0", font=FONT_SMALL_BOLD)
        self.create_text(w // 2, h // 2 + 10, text="Theatrical Artwork Pending", fill="#94A3B8", font=FONT_BADGE)
        self.create_text(w // 2, h // 2 + 25, text="Awaiting Distribution", fill="#64748B", font=FONT_BADGE)

        # Movie Title & Genre
        display_title = self.title if len(self.title) <= 20 else self.title[:18] + "..."
        self.create_text(w // 2, h // 2 + 55, text=display_title, fill="#38BDF8", font=FONT_CARD_TITLE)
        self.create_text(w // 2, h // 2 + 75, text=self.genre.upper()[:24], fill="#94A3B8", font=FONT_BADGE)

    # Backward compatibility alias
    _draw_procedural_fallback = _draw_unavailable_fallback


class MovieCardWidget(tk.Frame):
    """
    BookMyShow-style Premium Movie Card Component:
    - 2:3 portrait aspect ratio poster with 10 px rounded top corners.
    - Attached dark rating strip directly at bottom of poster (★ 8.8/10 on left, Votes on right).
    - Movie title in 16 px bold dark charcoal with 2-line fixed height.
    - Censor rating & language (e.g. U • Hindi) in 13 px muted text.
    - Genre (e.g. Biography / Drama) in 13 px muted text.
    - Full-width Book Tickets button (height 40 px, #F43F68) pinned to the exact same baseline.
    - Seamless card surface matching page background (#F2F4F8) with zero white borders or strips.
    """

    def __init__(
        self,
        master,
        movie,
        on_select: Callable[[object], None],
        width: int = 300,
        height: Optional[int] = None,
        poster_w: Optional[int] = None,
        poster_h: Optional[int] = None,
        promoted: bool = False,
        **kwargs
    ):
        pw = poster_w if poster_w is not None else width
        ph = poster_h if poster_h is not None else (int(pw * 1.5) + 44)
        info_h = 210
        card_h = height if height is not None else (ph + info_h)

        super().__init__(
            master,
            bg=BG_PAGE,
            width=width,
            height=card_h,
            padx=0,
            pady=0,
            highlightthickness=0,
            cursor="hand2",
            takefocus=True,
            **kwargs
        )
        self.pack_propagate(False)
        self.movie = movie
        self.on_select = on_select
        self.card_width = width
        self.card_height = card_h

        votes_approx = getattr(movie, "vote_count", f"{int(movie.rating * 1.6 + 8):.1f}K")
        self.poster = PosterWidget(
            self,
            image_path=movie.poster_path,
            width=pw,
            height=ph,
            title=movie.title,
            genre=movie.genre,
            rating=movie.rating,
            votes=votes_approx,
            promoted=promoted,
            is_upcoming=getattr(movie, "is_upcoming", False),
            banner_color=movie.banner_color,
            corner_radius=10,
            strip_height=44,
            on_click=lambda: self.on_select(self.movie)
        )
        self.poster.pack(side="top", fill="x")

        # Info body below poster - seamless surface matching surrounding page
        self.info_frame = tk.Frame(self, bg=BG_PAGE, padx=0, pady=6)
        self.info_frame.pack(side="top", fill="both", expand=True)

        # Book Tickets Button pinned to the bottom of the card (height 48 px, #F43F68)
        self.book_btn = BookNowButton(
            self.info_frame,
            text="Book Tickets",
            command=lambda: self.on_select(self.movie),
            width=pw,
            height=48,
            corner_radius=10,
            bg_color="#F43F68",
            hover_bg="#D83552",
            pressed_bg="#BE185D",
            font=("Segoe UI", -18, "bold")
        )
        self.book_btn.pack(side="bottom", fill="x", pady=(6, 0))

        # Title: Up to 2 lines, 21 px bold, fixed 2-line height so all buttons align
        self.title_lbl = tk.Label(
            self.info_frame,
            text=movie.title,
            font=("Segoe UI", -21, "bold"),
            fg="#111827",
            bg=BG_PAGE,
            anchor="nw",
            justify="left",
            wraplength=pw,
            height=2,
            cursor="hand2"
        )
        self.title_lbl.pack(side="top", fill="x")

        # Censor Rating & Languages (BookMyShow format: "UA • Hindi", 16 px bold)
        censor = getattr(movie, "censor_rating", "UA")
        lang = getattr(movie, "language", "Indian")
        meta_txt = f"{censor} • {lang}"
        self.meta_lbl = tk.Label(
            self.info_frame,
            text=meta_txt,
            font=("Segoe UI", -16, "bold"),
            fg="#111827",
            bg=BG_PAGE,
            anchor="w",
            justify="left",
            wraplength=pw,
            cursor="hand2"
        )
        self.meta_lbl.pack(side="top", fill="x", pady=(4, 0))

        # Genre (16 px)
        genre_txt = movie.genre
        self.genre_lbl = tk.Label(
            self.info_frame,
            text=genre_txt,
            font=("Segoe UI", -16),
            fg="#374151",
            bg=BG_PAGE,
            anchor="w",
            justify="left",
            wraplength=pw,
            cursor="hand2"
        )
        self.genre_lbl.pack(side="top", fill="x", pady=(3, 0))

        # Bind hover and click across card components (except book_btn which has its own command)
        for w in (self, self.info_frame, self.title_lbl, self.meta_lbl, self.genre_lbl):
            w.bind("<Button-1>", lambda e: self.on_select(self.movie))
            w.bind("<Enter>", self._on_hover_enter)
            w.bind("<Leave>", self._on_hover_leave)

        # Keyboard accessibility
        self.bind("<FocusIn>", lambda e: self.title_lbl.config(fg="#F43F68"))
        self.bind("<FocusOut>", lambda e: self.title_lbl.config(fg=TEXT_PRIMARY))
        self.bind("<Return>", lambda e: self.on_select(self.movie))
        self.bind("<space>", lambda e: self.on_select(self.movie))

    def _on_hover_enter(self, e=None):
        self.title_lbl.config(fg="#F43F68")

    def _on_hover_leave(self, e=None):
        self.title_lbl.config(fg=TEXT_PRIMARY)


class PromotionalBannerWidget(tk.Canvas):
    """
    Big, ultra-stylish BookMyShow Stream & VIP Premiere cinema banner.
    Features:
    - 220 px cinematic height with midnight violet gradient background.
    - Prominent Stream badge with 4K HDR quality pill.
    - 24 px Bold white headline and crisp high-contrast subtitle.
    - Three feature highlight badges (4K Ultra HD & Dolby Atmos, 0% Extra Fees, VIP Access Pass).
    - Prominent coral-red action CTA button ("Explore Premieres ›").
    - Right-side VIP Premiere Pass ticket graphic on desktop displays (>= 980 px).
    - Glowing neon arcs and cinema atmosphere.
    """

    def __init__(self, master, height: int = BANNER_HEIGHT, on_click: Optional[Callable[[], None]] = None, **kwargs):
        super().__init__(
            master,
            bg="#120F24",
            height=height,
            highlightthickness=0,
            cursor="hand2" if on_click else "arrow",
            **kwargs
        )
        self.banner_height = height
        self.on_click = on_click
        banner_bg = "#120F24"

        # Content frame vertically centered inside banner
        self.inner_frame = tk.Frame(self, bg=banner_bg)
        self.window_id = self.create_window(44, height // 2, anchor="w", window=self.inner_frame)

        # Row 0: Badges
        badge_row = tk.Frame(self.inner_frame, bg=banner_bg)
        badge_row.pack(anchor="w", pady=(0, 6))

        self.badge_lbl = tk.Label(
            badge_row,
            text="★ CINEBOOK STREAM PREMIERES",
            font=("Segoe UI", -11, "bold"),
            fg="#FFFFFF",
            bg=ACCENT_RED,
            padx=12,
            pady=3
        )
        self.badge_lbl.pack(side="left", padx=(0, 8))

        self.quality_badge = tk.Label(
            badge_row,
            text="EXCLUSIVE 4K HDR",
            font=("Segoe UI", -10, "bold"),
            fg="#CBD5E1",
            bg="#2A2244",
            padx=10,
            pady=3
        )
        self.quality_badge.pack(side="left")

        # Row 1: Headline (22 px Bold)
        self.title_lbl = tk.Label(
            self.inner_frame,
            text="Endless Cinema. Anytime. Anywhere.",
            font=("Segoe UI", -22, "bold"),
            fg="#FFFFFF",
            bg=banner_bg
        )
        self.title_lbl.pack(anchor="w", pady=(0, 4))

        # Row 2: Subtitle (13 px)
        self.desc_lbl = tk.Label(
            self.inner_frame,
            text="Watch blockbuster theatrical premieres, international film festival hits & VIP director's cuts directly from home with zero convenience fees.",
            font=("Segoe UI", -13, "normal"),
            fg="#E2E8F0",
            bg=banner_bg
        )
        self.desc_lbl.pack(anchor="w", pady=(0, 10))

        # Row 3: Action Button & Feature Pills
        action_row = tk.Frame(self.inner_frame, bg=banner_bg)
        action_row.pack(anchor="w")

        self.cta_btn = ModernButton(
            action_row,
            text="Explore Premieres  ›",
            command=on_click if on_click else lambda: None,
            bg=ACCENT_RED,
            hover_bg=ACCENT_RED_HOVER,
            font=("Segoe UI", -14, "bold"),
            padx=20,
            pady=7
        )
        self.cta_btn.pack(side="left", padx=(0, 12))

        self.feat_p1 = tk.Label(
            action_row,
            text="🎬 4K Ultra HD & Dolby Atmos",
            bg="#221A38",
            fg="#CBD5E1",
            font=("Segoe UI", -11, "bold"),
            padx=11,
            pady=6
        )
        self.feat_p1.pack(side="left", padx=(0, 8))

        self.feat_p2 = tk.Label(
            action_row,
            text="⚡ 0% Extra Fees",
            bg="#221A38",
            fg="#CBD5E1",
            font=("Segoe UI", -11, "bold"),
            padx=11,
            pady=6
        )
        self.feat_p2.pack(side="left", padx=(0, 8))

        self.feat_p3 = tk.Label(
            action_row,
            text="🍿 VIP Weekend Pass",
            bg="#221A38",
            fg="#CBD5E1",
            font=("Segoe UI", -11, "bold"),
            padx=11,
            pady=6
        )
        self.feat_p3.pack(side="left")

        # Right-side VIP Card Graphic
        self.vip_card = tk.Frame(
            self,
            bg="#1E1736",
            padx=18,
            pady=14,
            highlightthickness=1,
            highlightbackground="#3B3058"
        )
        self.vip_window_id = self.create_window(1000, height // 2, anchor="e", window=self.vip_card)

        tk.Label(
            self.vip_card,
            text="👑 VIP PREMIERE PASS",
            bg="#F59E0B",
            fg="#111827",
            font=("Segoe UI", -10, "bold"),
            padx=8,
            pady=2
        ).pack(anchor="w", pady=(0, 4))

        tk.Label(
            self.vip_card,
            text="Unlimited Premieres",
            bg="#1E1736",
            fg="#FFFFFF",
            font=("Segoe UI", -15, "bold")
        ).pack(anchor="w")

        tk.Label(
            self.vip_card,
            text="Early Access • 4K HDR\nStarting from ₹149 / title",
            bg="#1E1736",
            fg="#94A3B8",
            font=("Segoe UI", -11, "normal"),
            justify="left"
        ).pack(anchor="w", pady=(3, 5))

        tk.Label(
            self.vip_card,
            text="● PREMIERES ACTIVE",
            bg="#064E3B",
            fg="#34D399",
            font=("Segoe UI", -10, "bold"),
            padx=8,
            pady=3
        ).pack(anchor="w")

        # Bind clicks to entire banner
        if on_click:
            click_targets = [
                self, self.inner_frame, self.badge_lbl, self.quality_badge,
                self.title_lbl, self.desc_lbl, action_row,
                self.feat_p1, self.feat_p2, self.feat_p3,
                self.vip_card
            ]
            for w in click_targets:
                w.bind("<Button-1>", lambda e: on_click())

        self.bind("<Configure>", self._on_resize)

    def _on_resize(self, event) -> None:
        w = max(event.width, 500)
        h = self.banner_height
        self.delete("decor")

        # Position content vertically centered
        self.coords(self.window_id, 44, h // 2)

        # Responsive behavior for right VIP card, pills, and text wrap
        if w >= 1150:
            self.itemconfigure(self.vip_window_id, state="normal")
            self.coords(self.vip_window_id, w - 44, h // 2)
            self.feat_p2.pack(side="left", padx=(0, 8))
            self.feat_p3.pack(side="left")
            self.title_lbl.config(wraplength=max(380, w - 360))
            self.desc_lbl.config(wraplength=max(450, w - 360))
        elif w >= 940:
            self.itemconfigure(self.vip_window_id, state="normal")
            self.coords(self.vip_window_id, w - 44, h // 2)
            self.feat_p2.pack(side="left", padx=(0, 8))
            self.feat_p3.pack_forget()
            self.title_lbl.config(wraplength=max(360, w - 340))
            self.desc_lbl.config(wraplength=max(400, w - 340))
        else:
            self.itemconfigure(self.vip_window_id, state="hidden")
            self.feat_p3.pack_forget()
            if w >= 680:
                self.feat_p2.pack(side="left", padx=(0, 8))
            else:
                self.feat_p2.pack_forget()
            self.title_lbl.config(wraplength=max(280, w - 88))
            self.desc_lbl.config(wraplength=max(280, w - 88))

        # Top neon line
        self.create_line(0, 0, w, 0, fill="#F84464", width=3, tags="decor")

        # Left pink curved arc
        self.create_oval(
            -140, -60, 260, h + 60,
            outline="#F84464",
            width=12,
            tags="decor"
        )
        self.create_oval(
            -120, -40, 240, h + 40,
            outline="#FB7185",
            width=3,
            tags="decor"
        )

        # Right gold curved arc
        self.create_oval(
            w - 240, -60, w + 160, h + 60,
            outline="#F59E0B",
            width=12,
            tags="decor"
        )
        self.create_oval(
            w - 220, -40, w + 140, h + 40,
            outline="#FBBF24",
            width=3,
            tags="decor"
        )

        self.tag_lower("decor")



class StatCard(tk.Frame):
    """Modern dashboard metric tile with an accent highlight."""

    def __init__(self, master, label: str, value: str, accent_color: str = ACCENT_RED, **kwargs):
        super().__init__(master, bg=BG_CARD, padx=16, pady=12, highlightthickness=1,
                         highlightbackground=BORDER_COLOR, **kwargs)

        self.columnconfigure(0, weight=1)

        accent_bar = tk.Frame(self, bg=accent_color, height=3)
        accent_bar.grid(row=0, column=0, sticky="ew", pady=(0, 8))

        self.val_label = tk.Label(self, text=value, font=FONT_TITLE,
                                  fg=TEXT_PRIMARY, bg=BG_CARD)
        self.val_label.grid(row=1, column=0, sticky="w")

        self.desc_label = tk.Label(self, text=label.upper(), font=FONT_BADGE,
                                   fg=TEXT_SECONDARY, bg=BG_CARD)
        self.desc_label.grid(row=2, column=0, sticky="w", pady=(2, 0))

    def update_value(self, new_val: str) -> None:
        self.val_label.config(text=new_val)


class CurvedScreenWidget(tk.Canvas):
    """Displays a clean cinema screen indicator with arc and text."""

    def __init__(self, master, width: int = 560, height: int = 56, bg: str = BG_CARD, **kwargs):
        super().__init__(master, width=width, height=height, bg=bg,
                         highlightthickness=0, **kwargs)
        self.target_w = width
        self.target_h = height
        self.draw_screen()

    def draw_screen(self) -> None:
        w, h = self.target_w, self.target_h

        # Screen curve arching towards audience
        self.create_arc(
            30, 4, w - 30, h + 40,
            start=25, extent=130, style="arc",
            outline="#CBD5E1", width=10
        )

        self.create_arc(
            40, 10, w - 40, h + 35,
            start=30, extent=120, style="arc",
            outline="#0EA5E9", width=2
        )

        self.create_text(
            w // 2, 40,
            text="•  ALL EYES THIS WAY PLEASE (SCREEN)  •",
            fill=TEXT_MUTED, font=FONT_BADGE
        )


class SeatWidget(tk.Canvas):
    """
    Individual interactive theatre seat with state management in clean light theme.
    States: 'AVAILABLE', 'SELECTED', 'BOOKED'.
    Tiers: RECLINER (Gold), PREMIUM (Blue), STANDARD (Emerald).
    """

    def __init__(
        self,
        master,
        seat_number: str,
        tier: str,
        price: float,
        status: str = "AVAILABLE",
        on_toggle: Optional[Callable[[str], None]] = None,
        size: int = 38,
        is_bestseller: bool = False,
        **kwargs
    ):
        super().__init__(
            master,
            width=size,
            height=size,
            bg=BG_PAGE,
            highlightthickness=0,
            cursor="hand2" if status == "AVAILABLE" else "arrow",
            **kwargs
        )
        self.seat_number = seat_number
        self.tier = tier
        self.price = price
        self.status = status
        self.is_selected = False
        self.on_toggle = on_toggle
        self.size = size
        self.is_bestseller = is_bestseller

        self.bind("<Button-1>", self._handle_click)
        self.bind("<Enter>", self._handle_hover_enter)
        self.bind("<Leave>", self._handle_hover_leave)

        self.redraw()

    def set_size(self, new_size: int) -> None:
        """Dynamically update seat dimension for zoom controls."""
        self.size = new_size
        self.config(width=new_size, height=new_size)
        self.redraw()

    def set_selected(self, selected: bool) -> None:
        self.is_selected = selected
        self.redraw()

    def _handle_click(self, event=None) -> None:
        if self.status != "AVAILABLE":
            return
        if self.on_toggle:
            self.on_toggle(self.seat_number)

    def _handle_hover_enter(self, event=None) -> None:
        if self.status == "AVAILABLE" and not self.is_selected:
            self.redraw(hover=True)

    def _handle_hover_leave(self, event=None) -> None:
        if self.status == "AVAILABLE" and not self.is_selected:
            self.redraw(hover=False)

    def redraw(self, hover: bool = False) -> None:
        self.delete("all")
        s = self.size
        pad = 2

        tier_upper = self.tier.upper()
        if "RECLINER" in tier_upper:
            tier_color = TIER_RECLINER
        elif "ELITE" in tier_upper or "PREMIUM" in tier_upper:
            tier_color = TIER_PREMIUM
        else:
            tier_color = TIER_STANDARD

        if self.status == "BOOKED":
            bg_col = "#E2E8F0"
            border_col = "#CBD5E1"
            self.create_rectangle(pad, pad, s - pad, s - pad, fill=bg_col, outline=border_col, width=1)
            self.create_line(pad + 4, pad + 4, s - pad - 4, s - pad - 4, fill="#94A3B8", width=1)
            self.create_line(s - pad - 4, pad + 4, pad + 4, s - pad - 4, fill="#94A3B8", width=1)
            self.config(cursor="arrow")
        elif self.is_selected:
            bg_col = SEAT_SELECTED_BG
            border_col = SEAT_SELECTED_BORDER
            text_col = "#FFFFFF"
            self.create_rectangle(pad, pad, s - pad, s - pad, fill=bg_col, outline=border_col, width=2)
            self.create_text(s // 2, s // 2, text=self.seat_number, fill=text_col, font=FONT_BADGE)
            self.config(cursor="hand2")
        else:
            bg_col = "#F0F9FF" if hover else "#FFFFFF"
            border_col = ACCENT_RED if hover else ("#F59E0B" if self.is_bestseller else "#CBD5E1")
            text_col = ACCENT_RED if hover else TEXT_PRIMARY

            border_w = 2 if self.is_bestseller else 1
            self.create_rectangle(pad, pad, s - pad, s - pad, fill=bg_col, outline=border_col, width=border_w)
            self.create_line(pad + 3, pad + 2, s - pad - 3, pad + 2, fill=tier_color, width=2)
            self.create_text(s // 2, s // 2 + 1, text=self.seat_number, fill=text_col, font=FONT_BADGE)

            # Tiny star badge for bestseller
            if self.is_bestseller and s >= 34:
                self.create_text(s - pad - 4, pad + 4, text="★", fill="#D97706", font=("Segoe UI", 6, "bold"))

            self.config(cursor="hand2")


class ScrollableFrame(tk.Frame):
    """
    A seamless scrollable container using Canvas + interior Frame.
    Provides responsive mouse-wheel scrolling and auto-resizing.
    """

    def __init__(self, master, bg: str = BG_PAGE, **kwargs):
        super().__init__(master, bg=bg, **kwargs)

        self.canvas = tk.Canvas(self, bg=bg, highlightthickness=0)
        self.v_scroll = ttk.Scrollbar(self, orient="vertical", command=self.canvas.yview)

        self.scrollable_content = tk.Frame(self.canvas, bg=bg)
        self.scrollable_content.bind("<Configure>", self._on_frame_configure)

        self.canvas_window = self.canvas.create_window(
            (0, 0), window=self.scrollable_content, anchor="nw"
        )
        self.canvas.configure(xscrollcommand=None, yscrollcommand=self.v_scroll.set)

        self.canvas.bind("<Configure>", self._on_canvas_configure)

        self.canvas.pack(side="left", fill="both", expand=True)
        self.v_scroll.pack(side="right", fill="y")

        self.bind_mouse_wheel(self)
        self.bind_mouse_wheel(self.canvas)
        self.bind_mouse_wheel(self.scrollable_content)

    def _on_frame_configure(self, event=None):
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def _on_canvas_configure(self, event):
        self.canvas.itemconfig(self.canvas_window, width=event.width)

    def bind_mouse_wheel(self, widget):
        widget.bind("<MouseWheel>", self._on_mousewheel, add="+")
        for child in widget.winfo_children():
            self.bind_mouse_wheel(child)

    def _on_mousewheel(self, event):
        self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")


class ModernButton(tk.Frame):
    """Custom styled button with hover colors and click callback."""

    def __init__(
        self,
        master,
        text: str,
        command: Optional[Callable[[], None]] = None,
        bg: str = ACCENT_RED,
        hover_bg: str = ACCENT_RED_HOVER,
        fg: str = "#FFFFFF",
        font=FONT_BTN,
        padx: int = 16,
        pady: int = 8,
        border_radius: int = 0,
        state: str = "normal",
        **kwargs
    ):
        ht = kwargs.pop("highlightthickness", 0)
        super().__init__(
            master,
            bg=bg if state == "normal" else "#CBD5E1",
            cursor="hand2" if state == "normal" else "arrow",
            highlightthickness=ht,
            **kwargs
        )
        self.normal_bg = bg
        self.hover_bg = hover_bg
        self.fg = fg
        self.command = command
        self._state = state

        self.label = tk.Label(
            self,
            text=text,
            bg=bg if state == "normal" else "#CBD5E1",
            fg=fg if state == "normal" else "#64748B",
            font=font,
            padx=padx,
            pady=pady,
            cursor="hand2" if state == "normal" else "arrow"
        )
        self.label.pack(fill="both", expand=True)

        # Unconditionally bind mouse events so state changes (disabled <-> normal) work reliably
        for widget in (self, self.label):
            widget.bind("<Enter>", self._on_enter)
            widget.bind("<Leave>", self._on_leave)
            widget.bind("<Button-1>", self._on_click)

    def _on_enter(self, e=None):
        if self._state == "normal":
            self.config(bg=self.hover_bg)
            self.label.config(bg=self.hover_bg)

    def _on_leave(self, e=None):
        if self._state == "normal":
            self.config(bg=self.normal_bg)
            self.label.config(bg=self.normal_bg)

    def _on_click(self, e=None):
        if self._state == "normal" and self.command:
            self.command()

    def invoke(self):
        """Programmatic trigger matching standard Tkinter button protocol."""
        if self._state == "normal" and self.command:
            self.command()

    def set_state(self, state: str):
        self._state = state
        if state == "disabled":
            self.config(bg="#CBD5E1", cursor="arrow")
            self.label.config(bg="#CBD5E1", fg="#64748B", cursor="arrow")
        else:
            self.config(bg=self.normal_bg, cursor="hand2")
            self.label.config(bg=self.normal_bg, fg=self.fg, cursor="hand2")

    def configure(self, **kwargs):
        if "text" in kwargs:
            self.label.config(text=kwargs.pop("text"))
        if "state" in kwargs:
            self.set_state(kwargs.pop("state"))
        if "command" in kwargs:
            self.command = kwargs.pop("command")
        super().configure(**kwargs)

    config = configure


# ==============================================================================
# BOOK TICKETS ACTION BUTTON WIDGET
# ==============================================================================

class BookNowButton(tk.Canvas):
    """
    Polished BookMyShow-style action button with smooth rounded corners,
    vibrant coral-red background (#F84464), white semibold text,
    and distinct hover, pressed, and keyboard-focus states.
    """

    def __init__(
        self,
        master,
        text: str = "Book Tickets",
        command: Optional[Callable[[], None]] = None,
        width: int = 200,
        height: int = 40,
        corner_radius: int = 8,
        bg_color: str = "#F43F68",
        hover_bg: str = "#D83552",
        pressed_bg: str = "#BE185D",
        text_color: str = "#FFFFFF",
        font = ("Segoe UI", -14, "bold"),
        **kwargs
    ):
        super().__init__(
            master,
            width=width,
            height=height,
            bg=BG_PAGE,
            highlightthickness=0,
            cursor="hand2",
            takefocus=True,
            **kwargs
        )
        self.btn_text = text
        self.command = command
        self.btn_w = width
        self.btn_h = height
        self.radius = corner_radius
        self.bg_color = bg_color
        self.hover_bg = hover_bg
        self.pressed_bg = pressed_bg
        self.text_color = text_color
        self.btn_font = font
        self._state = "normal"
        self._has_focus = False
        self._photo = None

        self.bind("<Configure>", self._on_configure)
        self.bind("<Enter>", self._on_enter)
        self.bind("<Leave>", self._on_leave)
        self.bind("<Button-1>", self._on_press)
        self.bind("<ButtonRelease-1>", self._on_release)
        self.bind("<FocusIn>", self._on_focus_in)
        self.bind("<FocusOut>", self._on_focus_out)
        self.bind("<Return>", self._on_return)
        self.bind("<space>", self._on_return)

        self._redraw()

    def _on_configure(self, event) -> None:
        if event.width > 1 and event.height > 1 and (event.width != self.btn_w or event.height != self.btn_h):
            self.btn_w = event.width
            self.btn_h = event.height
            self._redraw()

    def _on_enter(self, event=None) -> None:
        if self._state != "disabled":
            self._state = "hover"
            self._redraw()

    def _on_leave(self, event=None) -> None:
        if self._state != "disabled":
            self._state = "normal"
            self._redraw()

    def _on_press(self, event=None) -> str:
        if self._state != "disabled":
            self._state = "pressed"
            self._redraw()
        return "break"

    def _on_release(self, event=None) -> str:
        if self._state == "pressed":
            self._state = "hover"
            self._redraw()
            if self.command:
                self.command()
        return "break"

    def _on_focus_in(self, event=None) -> None:
        self._has_focus = True
        self._redraw()

    def _on_focus_out(self, event=None) -> None:
        self._has_focus = False
        self._redraw()

    def _on_return(self, event=None) -> str:
        if self._state != "disabled" and self.command:
            self.command()
        return "break"

    def invoke(self) -> None:
        """Programmatic trigger matching standard Tkinter button protocol."""
        if self._state != "disabled" and self.command:
            self.command()

    def _redraw(self) -> None:
        w = max(40, self.btn_w)
        h = max(20, self.btn_h)

        color = self.bg_color
        if self._state == "hover":
            color = self.hover_bg
        elif self._state == "pressed":
            color = self.pressed_bg
        elif self._state == "disabled":
            color = "#CBD5E1"

        if PIL_AVAILABLE:
            cache_key = ("rounded_btn", w, h, color, self.radius)
            if cache_key in _POSTER_CACHE:
                self._photo = _POSTER_CACHE[cache_key]
            else:
                im = Image.new("RGBA", (w, h), (255, 255, 255, 0))
                draw = ImageDraw.Draw(im)
                draw.rounded_rectangle((0, 0, w, h), radius=self.radius, fill=color)
                self._photo = ImageTk.PhotoImage(im, master=self)
                _POSTER_CACHE[cache_key] = self._photo

            self.delete("all")
            self.create_image(0, 0, anchor="nw", image=self._photo)
        else:
            self.delete("all")
            self.create_rectangle(0, 0, w, h, fill=color, outline="")

        self.create_text(
            w // 2, h // 2,
            text=self.btn_text,
            fill=self.text_color if self._state != "disabled" else "#64748B",
            font=self.btn_font
        )
        if self._has_focus:
            self.create_rectangle(2, 2, w - 2, h - 2, outline="#FFFFFF", width=1, dash=(3, 3))


