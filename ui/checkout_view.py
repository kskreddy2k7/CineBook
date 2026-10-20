"""
CineBook - Customer Details & Checkout View (BookMyShow-Style Light Theme)
Customer contact input form, validation, itemized order summary,
and transactional demo booking confirmation.
"""

import re
from typing import Callable, List, Optional, Tuple
import tkinter as tk
from tkinter import ttk, messagebox

from database import DatabaseManager, SeatUnavailableError, DatabaseError
from models import Show, Seat, Booking
from ui.theme import (
    BG_PAGE, BG_CARD, BG_INPUT, BORDER_COLOR, BORDER_LIGHT, BORDER_CARD,
    ACCENT_RED, ACCENT_RED_HOVER, ACCENT_RED_LIGHT, ACCENT_CYAN, ACCENT_GOLD,
    COLOR_SUCCESS, COLOR_DANGER, COLOR_WARNING,
    TEXT_PRIMARY, TEXT_SECONDARY, TEXT_MUTED, TEXT_DARK, TEXT_LIGHT,
    FONT_HERO, FONT_TITLE, FONT_SUBTITLE, FONT_CARD_TITLE,
    FONT_BODY, FONT_BODY_BOLD, FONT_SMALL, FONT_SMALL_BOLD, FONT_BADGE
)
from ui.components import ScrollableFrame, ModernButton


class CheckoutView(tk.Frame):
    """Customer Information, Validation, and Transactional Booking Checkout."""

    def __init__(
        self,
        master,
        db: DatabaseManager,
        show: Show,
        selected_seats: List[Seat],
        subtotal: float,
        total: float,
        convenience_fee: float,
        on_back: Callable[[], None],
        on_booking_confirmed: Callable[[Booking], None],
        **kwargs
    ):
        super().__init__(master, bg=BG_PAGE, **kwargs)
        self.db = db
        self.show = show
        self.selected_seats = selected_seats
        self.subtotal = subtotal
        self.total = total
        self.convenience_fee = convenience_fee
        self.on_back = on_back
        self.on_booking_confirmed = on_booking_confirmed

        self.scroll_container = ScrollableFrame(self, bg=BG_PAGE)
        self.scroll_container.pack(fill="both", expand=True)
        self.content = self.scroll_container.scrollable_content

        # Centered container with generous horizontal margins
        self.main_wrapper = tk.Frame(self.content, bg=BG_PAGE)
        self.main_wrapper.pack(fill="x", padx=48, pady=(16, 36))

        self._build_top_bar()
        self._build_columns()

    def _build_top_bar(self) -> None:
        """Top navigation breadcrumb."""
        top_bar = tk.Frame(self.main_wrapper, bg=BG_PAGE)
        top_bar.pack(fill="x", pady=(0, 14))

        back_btn = tk.Label(
            top_bar,
            text="← Modify Seat Selection",
            font=FONT_BODY_BOLD,
            fg=ACCENT_RED,
            bg=BG_PAGE,
            cursor="hand2"
        )
        back_btn.pack(side="left")
        back_btn.bind("<Button-1>", lambda e: self.on_back())

        tk.Label(
            top_bar,
            text="Checkout & Confirmation",
            font=FONT_SUBTITLE,
            fg=TEXT_SECONDARY,
            bg=BG_PAGE
        ).pack(side="right")

    def _build_columns(self) -> None:
        """Two-column responsive layout: Form on Left, Order Summary on Right."""
        two_col_frame = tk.Frame(self.main_wrapper, bg=BG_PAGE)
        two_col_frame.pack(fill="both", expand=True)

        two_col_frame.columnconfigure(0, weight=3)
        two_col_frame.columnconfigure(1, weight=2)

        self.form_card = tk.Frame(
            two_col_frame,
            bg=BG_CARD,
            padx=28,
            pady=24,
            highlightthickness=1,
            highlightbackground=BORDER_CARD
        )
        self.form_card.grid(row=0, column=0, sticky="nsew", padx=(0, 20))

        self._build_customer_form()

        self.summary_card = tk.Frame(
            two_col_frame,
            bg=BG_CARD,
            padx=24,
            pady=24,
            highlightthickness=1,
            highlightbackground=BORDER_CARD
        )
        self.summary_card.grid(row=0, column=1, sticky="nsew")

        self._build_order_summary()

    def _build_customer_form(self) -> None:
        """Customer Details Form with visual validation state."""
        tk.Label(
            self.form_card,
            text="Contact Details",
            font=FONT_TITLE,
            fg=TEXT_PRIMARY,
            bg=BG_CARD
        ).pack(anchor="w")

        tk.Label(
            self.form_card,
            text="Your digital cinema ticket will be issued with these details.",
            font=FONT_BODY,
            fg=TEXT_SECONDARY,
            bg=BG_CARD
        ).pack(anchor="w", pady=(2, 20))

        tk.Label(self.form_card, text="FULL NAME *", font=FONT_BADGE, fg=TEXT_MUTED, bg=BG_CARD).pack(anchor="w")
        self.name_var = tk.StringVar()
        name_entry = tk.Entry(
            self.form_card,
            textvariable=self.name_var,
            font=FONT_BODY,
            bg="#F8F9FA",
            fg=TEXT_PRIMARY,
            insertbackground=TEXT_PRIMARY,
            relief="flat",
            highlightthickness=1,
            highlightbackground=BORDER_CARD
        )
        name_entry.pack(fill="x", pady=(4, 16), ipady=6)
        name_entry.focus()

        tk.Label(self.form_card, text="MOBILE NUMBER (10-Digit Indian format) *", font=FONT_BADGE, fg=TEXT_MUTED, bg=BG_CARD).pack(anchor="w")
        self.phone_var = tk.StringVar()
        phone_entry = tk.Entry(
            self.form_card,
            textvariable=self.phone_var,
            font=FONT_BODY,
            bg="#F8F9FA",
            fg=TEXT_PRIMARY,
            insertbackground=TEXT_PRIMARY,
            relief="flat",
            highlightthickness=1,
            highlightbackground=BORDER_CARD
        )
        phone_entry.pack(fill="x", pady=(4, 16), ipady=6)

        tk.Label(self.form_card, text="EMAIL ADDRESS (Optional, for digital receipt)", font=FONT_BADGE, fg=TEXT_MUTED, bg=BG_CARD).pack(anchor="w")
        self.email_var = tk.StringVar()
        email_entry = tk.Entry(
            self.form_card,
            textvariable=self.email_var,
            font=FONT_BODY,
            bg="#F8F9FA",
            fg=TEXT_PRIMARY,
            insertbackground=TEXT_PRIMARY,
            relief="flat",
            highlightthickness=1,
            highlightbackground=BORDER_CARD
        )
        email_entry.pack(fill="x", pady=(4, 20), ipady=6)

        # Demo simulation disclaimer
        notice_box = tk.Frame(
            self.form_card,
            bg=ACCENT_RED_LIGHT,
            padx=16,
            pady=12,
            highlightthickness=1,
            highlightbackground="#FCA5A5"
        )
        notice_box.pack(fill="x", pady=(10, 0))

        tk.Label(
            notice_box,
            text="ℹ️  CineBook Demo Reservation Notice",
            font=FONT_SMALL_BOLD,
            fg=ACCENT_RED,
            bg=ACCENT_RED_LIGHT
        ).pack(anchor="w")

        tk.Label(
            notice_box,
            text="This application is a demonstration cinema reservation system. "
                 "No actual payment card or banking transaction will occur. "
                 "Upon confirmation, your seats are immediately locked in SQLite.",
            font=FONT_SMALL,
            fg=TEXT_PRIMARY,
            bg=ACCENT_RED_LIGHT,
            wraplength=480,
            justify="left"
        ).pack(anchor="w", pady=(4, 0))

    def _build_order_summary(self) -> None:
        """Itemized order summary on the right card."""
        tk.Label(
            self.summary_card,
            text="Order Summary",
            font=FONT_TITLE,
            fg=TEXT_PRIMARY,
            bg=BG_CARD
        ).pack(anchor="w")

        tk.Frame(self.summary_card, bg=BORDER_COLOR, height=1).pack(fill="x", pady=(12, 16))

        tk.Label(self.summary_card, text="MOVIE:", font=FONT_BADGE, fg=TEXT_MUTED, bg=BG_CARD).pack(anchor="w")
        tk.Label(
            self.summary_card,
            text=self.show.movie_title,
            font=FONT_SUBTITLE,
            fg=TEXT_PRIMARY,
            bg=BG_CARD,
            wraplength=280,
            justify="left"
        ).pack(anchor="w", pady=(2, 10))

        tk.Label(self.summary_card, text="SCREEN & SHOWTIME:", font=FONT_BADGE, fg=TEXT_MUTED, bg=BG_CARD).pack(anchor="w")
        tk.Label(
            self.summary_card,
            text=f"{self.show.screen_name}\n{self.show.formatted_datetime}",
            font=FONT_BODY,
            fg=TEXT_SECONDARY,
            bg=BG_CARD,
            justify="left"
        ).pack(anchor="w", pady=(2, 12))

        tk.Label(self.summary_card, text="SELECTED SEATS:", font=FONT_BADGE, fg=TEXT_MUTED, bg=BG_CARD).pack(anchor="w")
        seats_frame = tk.Frame(self.summary_card, bg=BG_CARD)
        seats_frame.pack(fill="x", pady=(4, 16))

        for seat in self.selected_seats:
            lbl = tk.Label(
                seats_frame,
                text=seat.seat_number,
                font=FONT_BADGE,
                bg=ACCENT_RED,
                fg="#FFFFFF",
                padx=8,
                pady=3
            )
            lbl.pack(side="left", padx=(0, 6), pady=2)

        tk.Frame(self.summary_card, bg=BORDER_COLOR, height=1).pack(fill="x", pady=(8, 14))

        # Price breakdown
        p_row1 = tk.Frame(self.summary_card, bg=BG_CARD)
        p_row1.pack(fill="x", pady=2)
        tk.Label(p_row1, text=f"Tickets ({len(self.selected_seats)}):", font=FONT_BODY, fg=TEXT_SECONDARY, bg=BG_CARD).pack(side="left")
        tk.Label(p_row1, text=f"₹{self.subtotal:.2f}", font=FONT_BODY, fg=TEXT_PRIMARY, bg=BG_CARD).pack(side="right")

        p_row2 = tk.Frame(self.summary_card, bg=BG_CARD)
        p_row2.pack(fill="x", pady=2)
        tk.Label(p_row2, text="Convenience Fee:", font=FONT_BODY, fg=TEXT_SECONDARY, bg=BG_CARD).pack(side="left")
        tk.Label(p_row2, text=f"₹{self.convenience_fee:.2f}", font=FONT_BODY, fg=TEXT_MUTED, bg=BG_CARD).pack(side="right")

        tk.Frame(self.summary_card, bg=BORDER_COLOR, height=1).pack(fill="x", pady=12)

        total_row = tk.Frame(self.summary_card, bg=BG_CARD)
        total_row.pack(fill="x", pady=(0, 24))
        tk.Label(total_row, text="Total Payable:", font=FONT_SUBTITLE, fg=TEXT_PRIMARY, bg=BG_CARD).pack(side="left")
        tk.Label(total_row, text=f"₹{self.total:.2f}", font=FONT_TITLE, fg=ACCENT_RED, bg=BG_CARD).pack(side="right")

        self.confirm_btn = ModernButton(
            self.summary_card,
            text=f"Confirm Booking (₹{self.total:.2f})",
            command=self._handle_confirmation,
            bg=ACCENT_RED,
            hover_bg=ACCENT_RED_HOVER,
            pady=10
        )
        self.confirm_btn.pack(fill="x")

    def _validate_inputs(self) -> Tuple[bool, str]:
        """Validate patron name, phone, and optional email format."""
        name = self.name_var.get().strip()
        phone = self.phone_var.get().strip()
        email = self.email_var.get().strip()

        if not name:
            return False, "Please enter the patron's full name."

        if not phone:
            return False, "Please enter a contact phone number."

        # Normalize phone: remove spaces and hyphens
        phone_digits = re.sub(r"\D", "", phone)
        if len(phone_digits) != 10:
            return False, "Please enter a valid 10-digit mobile number."

        if email:
            email_pattern = r"^[\w\.-]+@[\w\.-]+\.\w+$"
            if not re.match(email_pattern, email):
                return False, "Please enter a valid email address or leave it blank."

        return True, ""

    def _handle_confirmation(self) -> None:
        """Validates input, calls atomic transactional database booking, and displays ticket."""
        is_valid, err_msg = self._validate_inputs()
        if not is_valid:
            messagebox.showerror("Validation Error", err_msg)
            return

        name = self.name_var.get().strip()
        phone = re.sub(r"\D", "", self.phone_var.get().strip())
        email = self.email_var.get().strip() or None
        seat_codes = [s.seat_number for s in self.selected_seats]
        seats_str = ", ".join(seat_codes)
        summary_msg = (
            f"Please verify your reservation details:\n\n"
            f"🎬 Movie: {self.show.movie_title}\n"
            f"🏛 Theatre: {getattr(self.show, 'theatre_name', 'CineBook Multiplex')}\n"
            f"🎥 Screen: {getattr(self.show, 'screen_name', 'Audi 1')}\n"
            f"📅 Date & Time: {self.show.formatted_datetime}\n"
            f"🎟 Seats: {seats_str} ({len(seat_codes)} seat{'s' if len(seat_codes) > 1 else ''})\n"
            f"👤 Customer: {name} ({phone})\n"
            f"💰 Total Amount: ₹{self.total:.2f}\n\n"
            f"Confirm and issue digital ticket?"
        )
        if not messagebox.askyesno("Confirm Cinema Reservation", summary_msg):
            return

        try:
            booking = self.db.create_booking(
                show_id=self.show.id,
                customer_name=name,
                customer_phone=phone,
                customer_email=email,
                seat_numbers=seat_codes,
                convenience_fee=self.convenience_fee
            )
            self.on_booking_confirmed(booking)
        except SeatUnavailableError as se:
            messagebox.showerror(
                "Seats Already Taken",
                f"Booking failed: {se}\n\nPlease select alternative available seats."
            )
            self.on_back()
        except DatabaseError as de:
            messagebox.showerror("Database Transaction Error", f"Could not create booking: {de}")
