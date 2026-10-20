"""
CineBook - Interactive Theatre Seat Selection View (BookMyShow-Style Light Theme)
Real-time seat matrix across Rows A–L with central aisle, tiered pricing (Classic, Elite, Recliner),
bestseller indicators, zoom-in/zoom-out controls, horizontal sibling showtime quick-switcher,
curved screen indicator, status legend, and live itemized price calculation.
"""

from typing import Callable, Dict, List, Optional, Set
import tkinter as tk
from tkinter import messagebox

from database import DatabaseManager
from models import Show, Seat
from ui.theme import (
    BG_PAGE, BG_CARD, BG_INPUT, BORDER_COLOR, BORDER_LIGHT, BORDER_CARD,
    ACCENT_RED, ACCENT_RED_HOVER, ACCENT_RED_LIGHT, ACCENT_CYAN, ACCENT_GOLD,
    COLOR_SUCCESS, COLOR_DANGER,
    TEXT_PRIMARY, TEXT_SECONDARY, TEXT_MUTED, TEXT_DARK, TEXT_LIGHT,
    FONT_HERO, FONT_TITLE, FONT_SUBTITLE, FONT_CARD_TITLE,
    FONT_BODY, FONT_BODY_BOLD, FONT_SMALL, FONT_SMALL_BOLD, FONT_BADGE,
    TIER_RECLINER, TIER_PREMIUM, TIER_STANDARD,
    SEAT_SELECTED_BG, SEAT_SELECTED_BORDER, SEAT_BOOKED_BG, SEAT_BOOKED_BORDER
)
from ui.components import CurvedScreenWidget, SeatWidget, ScrollableFrame, ModernButton


MAX_SEATS_PER_BOOKING = 6
CONVENIENCE_FEE = 25.0
DEFAULT_SEAT_SIZE = 40


class SeatView(tk.Frame):
    """Interactive Auditorium Seating Layout & Live Booking Calculator."""

    def __init__(
        self,
        master,
        db: DatabaseManager,
        show: Show,
        on_back: Callable[[], None],
        on_proceed_to_checkout: Callable[[Show, List[Seat], float, float], None],
        **kwargs
    ):
        super().__init__(master, bg=BG_PAGE, **kwargs)
        self.db = db
        self.show = show
        self.on_back = on_back
        self.on_proceed_to_checkout = on_proceed_to_checkout

        self.current_seat_size = DEFAULT_SEAT_SIZE
        self.selected_seat_numbers: Set[str] = set()
        self.seat_widgets: Dict[str, SeatWidget] = {}
        self.seats_data: Dict[str, Seat] = {}
        self.sibling_shows: List[Show] = []
        self.showtime_tab_buttons: Dict[int, tk.Label] = {}

        self.scroll_container = ScrollableFrame(self, bg=BG_PAGE)
        self.scroll_container.pack(fill="both", expand=True)
        self.content = self.scroll_container.scrollable_content

        # Centered container with generous horizontal margins
        self.main_wrapper = tk.Frame(self.content, bg=BG_PAGE)
        self.main_wrapper.pack(fill="x", padx=48, pady=(16, 36))

        self._load_seats()
        self._load_sibling_shows()
        self._build_top_bar()
        self._build_showtimes_quick_bar()

        # Main responsive layout: Sidebar on right by default, stacks below on narrower screens (<980px)
        self._is_stacked = False
        self.main_layout = tk.Frame(self.main_wrapper, bg=BG_PAGE)
        self.main_layout.pack(fill="both", expand=True)

        self._build_sidebar_and_calculator()
        self._build_auditorium_layout()

        self.bind("<Configure>", self._on_layout_configure)

    def _on_layout_configure(self, event=None) -> None:
        """Dynamically stack calculator below auditorium on narrower screens (< 980px)."""
        w = self.winfo_width()
        if w < 100:
            return

        # Responsive horizontal margin adjustment
        if w < 840:
            try:
                self.main_wrapper.pack_configure(padx=20)
            except Exception:
                pass
        else:
            try:
                self.main_wrapper.pack_configure(padx=48)
            except Exception:
                pass

        should_stack = (w < 980)
        if should_stack != self._is_stacked:
            self._is_stacked = should_stack
            self.calc_card.pack_forget()
            self.chart_frame.pack_forget()
            if self._is_stacked:
                # Stacked layout: chart on top, calculator summary below it
                self.chart_frame.pack(side="top", fill="x", expand=True)
                self.calc_card.pack(side="top", fill="x", pady=(20, 0))
                self.selected_seats_lbl.config(wraplength=700)
            else:
                # Side-by-side layout: sidebar on right, chart on left
                self.calc_card.pack(side="right", fill="y", padx=(20, 0), anchor="n")
                self.chart_frame.pack(side="left", fill="both", expand=True)
                self.selected_seats_lbl.config(wraplength=290)

    def _load_seats(self) -> None:
        """Fetch fresh seat status inventory from SQLite."""
        seats_list = self.db.get_seats_for_show(self.show.id)
        self.seats_data = {s.seat_number: s for s in seats_list}

    def _load_sibling_shows(self) -> None:
        """Fetch sibling showtimes for this theatre and date for quick-switching."""
        self.sibling_shows = self.db.get_sibling_shows_for_date(self.show.id)

    def _build_top_bar(self) -> None:
        """Top navigation breadcrumb with movie, theatre, screen, and date metadata."""
        self.top_bar = tk.Frame(self.main_wrapper, bg=BG_PAGE)
        self.top_bar.pack(fill="x", pady=(0, 10))

        back_btn = tk.Label(
            self.top_bar,
            text="← Change Movie / Theatre",
            font=FONT_BODY_BOLD,
            fg=ACCENT_RED,
            bg=BG_PAGE,
            cursor="hand2"
        )
        back_btn.pack(side="left")
        back_btn.bind("<Button-1>", lambda e: self.on_back())

        theatre_txt = getattr(self.show, "theatre_name", "CineBook Cinemas")
        screen_txt = getattr(self.show, "screen_name", "Audi")
        city_txt = getattr(self.show, "city_name", "")
        loc_str = f" • {city_txt}" if city_txt else ""

        self.ticket_count_lbl = tk.Label(
            self.top_bar,
            text=f"🎟 0/{MAX_SEATS_PER_BOOKING} Selected",
            font=FONT_SMALL_BOLD,
            fg=COLOR_SUCCESS,
            bg="#ECFDF5",
            padx=10,
            pady=4,
            highlightthickness=1,
            highlightbackground="#A7F3D0"
        )
        self.ticket_count_lbl.pack(side="right", padx=(12, 0))

        # Pack info label with side="left" and padding so it cleanly bridges the space without pushing other widgets
        self.show_info_lbl = tk.Label(
            self.top_bar,
            text=f"{self.show.movie_title} ({getattr(self.show, 'movie_language', 'Indian')})  |  🏛 {theatre_txt}{loc_str}  |  🎬 {screen_txt}",
            font=FONT_BODY_BOLD,
            fg=TEXT_SECONDARY,
            bg=BG_PAGE
        )
        self.show_info_lbl.pack(side="left", padx=(16, 0))

    def _build_showtimes_quick_bar(self) -> None:
        """Horizontal showtime selector for instant slot switching without leaving the seat view."""
        self.quick_bar_card = tk.Frame(
            self.main_wrapper,
            bg=BG_CARD,
            padx=18,
            pady=10,
            highlightthickness=1,
            highlightbackground=BORDER_CARD
        )
        self.quick_bar_card.pack(fill="x", pady=(0, 16))

        tk.Label(
            self.quick_bar_card,
            text="📅 SHOWTIME:",
            font=FONT_BADGE,
            fg=TEXT_MUTED,
            bg=BG_CARD
        ).pack(side="left", padx=(0, 12))

        self.showtime_tab_buttons.clear()
        shows_to_display = self.sibling_shows if self.sibling_shows else [self.show]

        for s in shows_to_display:
            is_active = (s.id == self.show.id)
            btn = tk.Label(
                self.quick_bar_card,
                text=f"🕒 {s.show_time}",
                font=FONT_BODY_BOLD,
                bg=ACCENT_RED if is_active else "#F5F5FA",
                fg="#FFFFFF" if is_active else TEXT_PRIMARY,
                padx=14,
                pady=6,
                cursor="hand2",
                highlightthickness=1,
                highlightbackground=ACCENT_RED if is_active else BORDER_CARD
            )
            btn.pack(side="left", padx=(0, 8))
            btn.bind("<Button-1>", lambda e, target_show=s: self._on_switch_showtime(target_show))
            self.showtime_tab_buttons[s.id] = btn

        # Date and Screen label on right
        date_str = self.show.formatted_datetime
        tk.Label(
            self.quick_bar_card,
            text=f"Showing on: {date_str}",
            font=FONT_SMALL,
            fg=TEXT_MUTED,
            bg=BG_CARD
        ).pack(side="right")

    def _on_switch_showtime(self, new_show: Show) -> None:
        """Switch to another showtime slot, clearing previous seat selections."""
        if new_show.id == self.show.id:
            return

        if self.selected_seat_numbers:
            ans = messagebox.askyesno(
                "Change Showtime",
                "Switching showtime will clear your currently selected seats. Continue?"
            )
            if not ans:
                return

        self.show = new_show
        self.selected_seat_numbers.clear()
        self._load_seats()

        # Update show info
        theatre_txt = getattr(self.show, "theatre_name", "CineBook Cinemas")
        screen_txt = getattr(self.show, "screen_name", "Audi")
        city_txt = getattr(self.show, "city_name", "")
        loc_str = f" • {city_txt}" if city_txt else ""
        self.show_info_lbl.config(
            text=f"{self.show.movie_title} ({getattr(self.show, 'movie_language', 'Indian')})  |  🏛 {theatre_txt}{loc_str}  |  🎬 {screen_txt}"
        )

        # Update quick bar buttons
        for s_id, btn in self.showtime_tab_buttons.items():
            if s_id == new_show.id:
                btn.config(bg=ACCENT_RED, fg="#FFFFFF", highlightbackground=ACCENT_RED)
            else:
                btn.config(bg="#F5F5FA", fg=TEXT_PRIMARY, highlightbackground=BORDER_CARD)

        self._render_seat_grid()
        self._update_calculator()

    def _build_auditorium_layout(self) -> None:
        """Constructs theatre screen, zoom controls, seat grid rows, and state legend."""
        self.chart_frame = tk.Frame(
            self.main_layout,
            bg=BG_CARD,
            padx=28,
            pady=20,
            highlightthickness=1,
            highlightbackground=BORDER_CARD
        )
        self.chart_frame.pack(side="left", fill="both", expand=True)

        # Top tools row: Screen Indicator + Zoom Controls
        tools_row = tk.Frame(self.chart_frame, bg=BG_CARD)
        tools_row.pack(fill="x", pady=(0, 10))

        zoom_box = tk.Frame(tools_row, bg=BG_CARD)
        zoom_box.pack(side="right")

        tk.Label(zoom_box, text="ZOOM:", font=FONT_BADGE, fg=TEXT_MUTED, bg=BG_CARD).pack(side="left", padx=(0, 6))

        for z_label, z_cmd in [("🔍+ In", self._zoom_in), ("🔍- Out", self._zoom_out), ("↺ Reset", self._zoom_reset)]:
            btn = tk.Label(
                zoom_box,
                text=z_label,
                font=FONT_BADGE,
                bg="#F8F9FA",
                fg=TEXT_PRIMARY,
                padx=8,
                pady=4,
                cursor="hand2",
                highlightthickness=1,
                highlightbackground=BORDER_CARD
            )
            btn.pack(side="left", padx=2)
            btn.bind("<Button-1>", lambda e, cmd=z_cmd: cmd())

        # Seat Grid Rows Container
        self.matrix_frame = tk.Frame(self.chart_frame, bg=BG_CARD)
        self.matrix_frame.pack(pady=(0, 12))

        self._render_seat_grid()

        # Cinema Screen Arc Indicator at the BOTTOM
        screen_widget = CurvedScreenWidget(self.chart_frame, width=540, height=54, bg=BG_CARD)
        screen_widget.pack(pady=(10, 14))

        self._build_legend(self.chart_frame)

    def _zoom_in(self) -> None:
        """Zoom in seats layout."""
        if self.current_seat_size < 50:
            self.current_seat_size += 4
            self._apply_zoom()

    def _zoom_out(self) -> None:
        """Zoom out seats layout."""
        if self.current_seat_size > 28:
            self.current_seat_size -= 4
            self._apply_zoom()

    def _zoom_reset(self) -> None:
        """Reset zoom to standard 100% size."""
        self.current_seat_size = DEFAULT_SEAT_SIZE
        self._apply_zoom()

    def _apply_zoom(self) -> None:
        """Applies zoom level across all active seat widgets."""
        for w in self.seat_widgets.values():
            w.set_size(self.current_seat_size)

    def _render_seat_grid(self) -> None:
        """Renders Rows A through L (12 rows, 8 seats per row with central aisle)."""
        for w in self.matrix_frame.winfo_children():
            w.destroy()
        self.seat_widgets.clear()

        # Rows A to L mapping
        # Rows A, B: Recliner
        # Rows C, D, E, F: Elite
        # Rows G, H, I, J, K, L: Classic
        p_classic = getattr(self.show, "price_classic", 150.0)
        p_elite = getattr(self.show, "price_elite", 220.0)
        p_recliner = getattr(self.show, "price_recliner", 300.0)

        rows_order = ["A", "B", "C", "D", "E", "F", "G", "H", "I", "J", "K", "L"]
        row_tier_label = {
            "A": ("RECLINER", TIER_RECLINER, p_recliner),
            "B": ("RECLINER", TIER_RECLINER, p_recliner),
            "C": ("ELITE", TIER_PREMIUM, p_elite),
            "D": ("ELITE", TIER_PREMIUM, p_elite),
            "E": ("ELITE", TIER_PREMIUM, p_elite),
            "F": ("ELITE", TIER_PREMIUM, p_elite),
            "G": ("NORMAL", TIER_STANDARD, p_classic),
            "H": ("NORMAL", TIER_STANDARD, p_classic),
            "I": ("NORMAL", TIER_STANDARD, p_classic),
            "J": ("NORMAL", TIER_STANDARD, p_classic),
            "K": ("NORMAL", TIER_STANDARD, p_classic),
            "L": ("NORMAL", TIER_STANDARD, p_classic),
        }

        current_category = None

        for row_letter in rows_order:
            tier_name, tier_col, tier_price = row_tier_label.get(row_letter, ("NORMAL", TIER_STANDARD, p_classic))

            # Section separator header above each category section matching screenshot
            if tier_name != current_category:
                current_category = tier_name
                sec_header = tk.Frame(self.matrix_frame, bg=BG_CARD)
                sec_header.pack(fill="x", pady=(12, 6))

                tk.Label(
                    sec_header,
                    text=f"{tier_name} - Rs. {float(tier_price):.2f}",
                    font=FONT_BADGE,
                    fg=TEXT_MUTED,
                    bg=BG_CARD
                ).pack(side="left", padx=(10, 8))
                tk.Frame(sec_header, bg=BORDER_COLOR, height=1).pack(side="left", fill="x", expand=True, padx=(0, 10))

            row_frame = tk.Frame(self.matrix_frame, bg=BG_CARD)
            row_frame.pack(pady=2)

            lbl_left = tk.Label(
                row_frame,
                text=f"{row_letter}",
                font=FONT_SMALL_BOLD,
                fg=TEXT_MUTED,
                bg=BG_CARD,
                width=3,
                anchor="e"
            )
            lbl_left.pack(side="left", padx=(0, 10))

            for seat_num in range(1, 9):
                seat_code = f"{row_letter}{seat_num}"
                seat_obj = self.seats_data.get(seat_code)

                if not seat_obj:
                    # In case seat is not seeded in database yet, create placeholder object
                    tier_str = tier_name
                    price_val = tier_price
                    seat_obj = Seat(
                        id=0,
                        show_id=self.show.id,
                        seat_number=seat_code,
                        tier=tier_str,
                        price=price_val,
                        status="AVAILABLE",
                        is_bestseller=(row_letter in ("D", "E") and seat_num in (3, 4, 5, 6))
                    )
                    self.seats_data[seat_code] = seat_obj

                is_best = getattr(seat_obj, "is_bestseller", False) or (row_letter in ("D", "E") and seat_num in (3, 4, 5, 6))

                seat_widget = SeatWidget(
                    row_frame,
                    seat_number=seat_code,
                    tier=seat_obj.tier,
                    price=seat_obj.price,
                    status=seat_obj.status,
                    on_toggle=self._toggle_seat_selection,
                    size=self.current_seat_size,
                    is_bestseller=is_best
                )
                seat_widget.pack(side="left", padx=2)
                self.seat_widgets[seat_code] = seat_widget

                # Central aisle between seat 4 and seat 5
                if seat_num == 4:
                    aisle = tk.Frame(row_frame, bg=BG_CARD, width=28, height=self.current_seat_size)
                    aisle.pack(side="left")

            lbl_right = tk.Label(
                row_frame,
                text=row_letter,
                font=FONT_SMALL_BOLD,
                fg=TEXT_MUTED,
                bg=BG_CARD,
                width=3,
                anchor="w"
            )
            lbl_right.pack(side="left", padx=(10, 0))

        # Re-apply any previous selections
        for sc in self.selected_seat_numbers:
            if sc in self.seat_widgets:
                self.seat_widgets[sc].set_selected(True)

    def _build_legend(self, parent: tk.Widget) -> None:
        """Seat status, bestseller, and pricing legend indicators."""
        legend_frame = tk.Frame(
            parent,
            bg="#F8F9FA",
            padx=16,
            pady=10,
            highlightthickness=1,
            highlightbackground=BORDER_CARD
        )
        legend_frame.pack(fill="x", pady=(14, 0))

        p_classic = int(getattr(self.show, "price_classic", 150))
        p_elite = int(getattr(self.show, "price_elite", 220))
        p_recliner = int(getattr(self.show, "price_recliner", 300))

        items = [
            ("Available", "#FFFFFF", BORDER_LIGHT, TEXT_SECONDARY),
            ("Selected", SEAT_SELECTED_BG, SEAT_SELECTED_BORDER, "#FFFFFF"),
            ("Sold", "#E2E8F0", "#CBD5E1", TEXT_MUTED),
            ("★ Bestseller", "#FEF3C7", "#F59E0B", "#B45309"),
            (f"Recliner (₹{p_recliner})", "#F8F9FA", TIER_RECLINER, TIER_RECLINER),
            (f"Elite (₹{p_elite})", "#F8F9FA", TIER_PREMIUM, TIER_PREMIUM),
            (f"Normal (₹{p_classic})", "#F8F9FA", TIER_STANDARD, TIER_STANDARD),
        ]

        for text, fill_col, border_col, text_col in items:
            box = tk.Frame(legend_frame, bg="#F8F9FA")
            box.pack(side="left", expand=True)

            indicator = tk.Canvas(box, width=14, height=14, bg=fill_col,
                                  highlightthickness=1, highlightbackground=border_col)
            indicator.pack(side="left", padx=(0, 6))

            tk.Label(box, text=text, font=FONT_BADGE, fg=text_col, bg="#F8F9FA").pack(side="left")

    def _build_sidebar_and_calculator(self) -> None:
        """Right column: live itemized price calculation & checkout action."""
        self.calc_card = tk.Frame(
            self.main_layout,
            bg=BG_CARD,
            padx=22,
            pady=22,
            width=340,
            highlightthickness=1,
            highlightbackground=BORDER_CARD
        )
        self.calc_card.pack(side="right", fill="y", padx=(20, 0), anchor="n")

        tk.Label(
            self.calc_card,
            text="Booking Summary",
            font=FONT_TITLE,
            fg=TEXT_PRIMARY,
            bg=BG_CARD
        ).pack(anchor="w")

        tk.Label(
            self.calc_card,
            text=f"Max {MAX_SEATS_PER_BOOKING} seats per reservation",
            font=FONT_SMALL,
            fg=TEXT_MUTED,
            bg=BG_CARD
        ).pack(anchor="w", pady=(2, 16))

        tk.Label(self.calc_card, text="SELECTED SEATS:", font=FONT_BADGE,
                 fg=TEXT_MUTED, bg=BG_CARD).pack(anchor="w")

        self.selected_seats_lbl = tk.Label(
            self.calc_card,
            text="None (Click available seats)",
            font=FONT_BODY_BOLD,
            fg=ACCENT_RED,
            bg=BG_CARD,
            wraplength=290,
            justify="left"
        )
        self.selected_seats_lbl.pack(anchor="w", pady=(4, 16))

        self.itemized_frame = tk.Frame(self.calc_card, bg=BG_CARD)
        self.itemized_frame.pack(fill="x", pady=(0, 16))

        sub_row = tk.Frame(self.calc_card, bg=BG_CARD)
        sub_row.pack(fill="x", pady=2)
        tk.Label(sub_row, text="Ticket Subtotal:", font=FONT_BODY, fg=TEXT_SECONDARY, bg=BG_CARD).pack(side="left")
        self.subtotal_lbl = tk.Label(sub_row, text="₹0.00", font=FONT_BODY_BOLD, fg=TEXT_PRIMARY, bg=BG_CARD)
        self.subtotal_lbl.pack(side="right")

        fee_row = tk.Frame(self.calc_card, bg=BG_CARD)
        fee_row.pack(fill="x", pady=2)
        tk.Label(fee_row, text="Convenience Fee:", font=FONT_BODY, fg=TEXT_SECONDARY, bg=BG_CARD).pack(side="left")
        self.fee_lbl = tk.Label(fee_row, text=f"₹{CONVENIENCE_FEE:.2f}", font=FONT_BODY, fg=TEXT_MUTED, bg=BG_CARD)
        self.fee_lbl.pack(side="right")

        tk.Frame(self.calc_card, bg=BORDER_COLOR, height=1).pack(fill="x", pady=14)

        total_row = tk.Frame(self.calc_card, bg=BG_CARD)
        total_row.pack(fill="x", pady=(0, 20))
        tk.Label(total_row, text="Total Amount:", font=FONT_SUBTITLE, fg=TEXT_PRIMARY, bg=BG_CARD).pack(side="left")
        self.total_lbl = tk.Label(total_row, text="₹0.00", font=FONT_TITLE, fg=ACCENT_RED, bg=BG_CARD)
        self.total_lbl.pack(side="right")

        self.checkout_btn = ModernButton(
            self.calc_card,
            text="Proceed to Pay →",
            command=self._handle_checkout,
            bg=ACCENT_RED,
            hover_bg=ACCENT_RED_HOVER,
            state="disabled"
        )
        self.checkout_btn.pack(fill="x")

    def _toggle_seat_selection(self, seat_code: str) -> None:
        """Handle seat click selection with maximum seat constraint."""
        if seat_code in self.selected_seat_numbers:
            self.selected_seat_numbers.remove(seat_code)
            if seat_code in self.seat_widgets:
                self.seat_widgets[seat_code].set_selected(False)
        else:
            if len(self.selected_seat_numbers) >= MAX_SEATS_PER_BOOKING:
                messagebox.showwarning(
                    "Seat Selection Limit",
                    f"You can select a maximum of {MAX_SEATS_PER_BOOKING} seats per booking."
                )
                return
            self.selected_seat_numbers.add(seat_code)
            if seat_code in self.seat_widgets:
                self.seat_widgets[seat_code].set_selected(True)

        self._update_calculator()

    def _update_calculator(self) -> None:
        """Recalculates itemized total and enables/disables checkout button."""
        selected_objs = [self.seats_data[sc] for sc in sorted(self.selected_seat_numbers) if sc in self.seats_data]

        for w in self.itemized_frame.winfo_children():
            w.destroy()

        if not selected_objs:
            if hasattr(self, "ticket_count_lbl"):
                self.ticket_count_lbl.config(text=f"🎟 0/{MAX_SEATS_PER_BOOKING} Selected")
            self.selected_seats_lbl.config(text="None (Click available seats)")
            self.subtotal_lbl.config(text="₹0.00")
            self.fee_lbl.config(text="₹0.00")
            self.total_lbl.config(text="₹0.00")
            self.checkout_btn.set_state("disabled")
            return

        if hasattr(self, "ticket_count_lbl"):
            self.ticket_count_lbl.config(text=f"🎟 {len(selected_objs)}/{MAX_SEATS_PER_BOOKING} Selected")

        sorted_seat_codes = [s.seat_number for s in selected_objs]
        self.selected_seats_lbl.config(text=", ".join(sorted_seat_codes))

        for seat in selected_objs:
            row = tk.Frame(self.itemized_frame, bg=BG_CARD)
            row.pack(fill="x", pady=1)
            tk.Label(row, text=f"Seat {seat.seat_number} ({seat.tier.title()}):",
                     font=FONT_SMALL, fg=TEXT_MUTED, bg=BG_CARD).pack(side="left")
            tk.Label(row, text=f"₹{seat.price:.2f}",
                     font=FONT_SMALL, fg=TEXT_PRIMARY, bg=BG_CARD).pack(side="right")

        subtotal = sum(s.price for s in selected_objs)
        fee = CONVENIENCE_FEE
        total = subtotal + fee

        self.subtotal_lbl.config(text=f"₹{subtotal:.2f}")
        self.fee_lbl.config(text=f"₹{fee:.2f}")
        self.total_lbl.config(text=f"₹{total:.2f}")

        seat_count_str = f"({len(selected_objs)} Seat{'s' if len(selected_objs) > 1 else ''})"
        self.checkout_btn.label.config(text=f"Continue to Pay ₹{total:.2f} {seat_count_str}")
        self.checkout_btn.set_state("normal")

    def _handle_checkout(self) -> None:
        """Proceed to customer details checkout."""
        if not self.selected_seat_numbers:
            messagebox.showwarning("No Seats Selected", "Please select at least one available seat to continue.")
            return

        selected_objs = [self.seats_data[sc] for sc in sorted(self.selected_seat_numbers) if sc in self.seats_data]
        subtotal = sum(s.price for s in selected_objs)
        total = subtotal + CONVENIENCE_FEE

        self.on_proceed_to_checkout(
            self.show,
            selected_objs,
            subtotal,
            total,
            CONVENIENCE_FEE
        )
