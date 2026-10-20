"""
CineBook - About & Help View
Comprehensive architectural reference, database schema documentation,
and built-in Viva Examination cheat-sheet for academic evaluation.
"""

from pathlib import Path
from typing import Callable
import tkinter as tk
from tkinter import ttk, messagebox

from database import DatabaseManager
from ui.theme import (
    BG_DARK, BG_CARD, BG_INPUT, BORDER_COLOR, BORDER_LIGHT,
    ACCENT_VIOLET, ACCENT_VIOLET_HOVER, ACCENT_CYAN, ACCENT_GOLD,
    COLOR_SUCCESS, COLOR_DANGER,
    TEXT_PRIMARY, TEXT_SECONDARY, TEXT_MUTED, TEXT_DARK,
    FONT_HERO, FONT_TITLE, FONT_SUBTITLE, FONT_CARD_TITLE,
    FONT_BODY, FONT_BODY_BOLD, FONT_SMALL, FONT_SMALL_BOLD, FONT_BADGE
)
from ui.components import ScrollableFrame, ModernButton


class AboutView(tk.Frame):
    """Architecture explanation, Viva guide, and system information view."""

    def __init__(
        self,
        master,
        db: DatabaseManager,
        on_go_home: Callable[[], None],
        **kwargs
    ):
        super().__init__(master, bg=BG_DARK, **kwargs)
        self.db = db
        self.on_go_home = on_go_home

        self.scroll_container = ScrollableFrame(self, bg=BG_DARK)
        self.scroll_container.pack(fill="both", expand=True)
        self.content = self.scroll_container.scrollable_content

        self._build_header()
        self._build_overview_card()
        self._build_architecture_card()
        self._build_viva_qa_card()
        self._build_database_tools_card()

    def _build_header(self) -> None:
        """Top title and navigation."""
        top_bar = tk.Frame(self.content, bg=BG_DARK)
        top_bar.pack(fill="x", padx=24, pady=(20, 12))

        title_col = tk.Frame(top_bar, bg=BG_DARK)
        title_col.pack(side="left")

        tk.Label(
            title_col,
            text="ABOUT CINEBOOK & VIVA PREPARATION",
            font=FONT_HERO,
            fg=TEXT_PRIMARY,
            bg=BG_DARK
        ).pack(anchor="w")

        tk.Label(
            title_col,
            text="Advanced Programming Practice | Python Tkinter & SQLite Cinema Reservation System",
            font=FONT_BODY,
            fg=TEXT_SECONDARY,
            bg=BG_DARK
        ).pack(anchor="w", pady=(2, 0))

        home_btn = tk.Label(
            top_bar,
            text="← Back to Home",
            font=FONT_BODY_BOLD,
            fg=ACCENT_CYAN,
            bg=BG_DARK,
            cursor="hand2"
        )
        home_btn.pack(side="right")
        home_btn.bind("<Button-1>", lambda e: self.on_go_home())

    def _build_overview_card(self) -> None:
        """Overview and system design goals."""
        card = tk.Frame(self.content, bg=BG_CARD, padx=24, pady=20,
                        highlightthickness=1, highlightbackground=BORDER_COLOR)
        card.pack(fill="x", padx=24, pady=(0, 16))

        tk.Label(card, text="PROJECT OVERVIEW & KEY HIGHLIGHTS", font=FONT_TITLE, fg=TEXT_PRIMARY, bg=BG_CARD).pack(anchor="w")

        overview_text = (
            "CineBook is a desktop movie ticket booking application developed strictly in Python Tkinter "
            "and SQLite. It simulates a modern cinema chain booking workflow featuring movie catalog discovery, "
            "interactive theatre seat reservation with tiered pricing (Standard ₹150, Premium ₹220, Recliner ₹300), "
            "client-side input validation, transactional double-booking prevention, digital ticket generation, "
            "and reservation cancellation with immediate inventory restoration."
        )
        tk.Label(card, text=overview_text, font=FONT_BODY, fg=TEXT_SECONDARY, bg=BG_CARD,
                 wraplength=840, justify="left").pack(anchor="w", pady=(6, 14))

        # Highlights Grid
        h_grid = tk.Frame(card, bg=BG_CARD)
        h_grid.pack(fill="x")

        features = [
            ("⚡ ACID SQLite Transactions", "Guarantees zero double-booking even when concurrent users pick the same seats."),
            ("🎨 Custom Dark Midnight UI", "Designed with violet/cyan accents, curved cinema screen, and clean cards."),
            ("🛡️ Strict Input Validation", "Validates 10-digit Indian phone numbers, required fields, and seat limits."),
            ("🎟️ Digital Ticket & Export", "Generates boarding-pass ticket with simulated barcode and local HTML/text export."),
        ]

        for idx, (title, desc) in enumerate(features):
            row = idx // 2
            col = idx % 2
            h_grid.columnconfigure(col, weight=1, uniform="feat_col")

            box = tk.Frame(h_grid, bg=BG_INPUT, padx=12, pady=10,
                           highlightthickness=1, highlightbackground=BORDER_COLOR)
            box.grid(row=row, column=col, sticky="nsew", padx=4, pady=4)

            tk.Label(box, text=title, font=FONT_SUBTITLE, fg=ACCENT_CYAN, bg=BG_INPUT).pack(anchor="w")
            tk.Label(box, text=desc, font=FONT_SMALL, fg=TEXT_SECONDARY, bg=BG_INPUT,
                     wraplength=380, justify="left").pack(anchor="w", pady=(2, 0))

    def _build_architecture_card(self) -> None:
        """Module structure and database schema."""
        card = tk.Frame(self.content, bg=BG_CARD, padx=24, pady=20,
                        highlightthickness=1, highlightbackground=BORDER_COLOR)
        card.pack(fill="x", padx=24, pady=(0, 16))

        tk.Label(card, text="RELATIONAL DATABASE SCHEMA (SQLite)", font=FONT_TITLE, fg=TEXT_PRIMARY, bg=BG_CARD).pack(anchor="w")

        tables_info = [
            ("movies", "Stores film title, genre, runtime, rating, director, cast, poster path, and synopsis."),
            ("shows", "Associates movie with auditorium screen, date, showtime, and tiered pricing."),
            ("show_seats", "Individual seat inventory per show. Enforces UNIQUE(show_id, seat_number) & status."),
            ("bookings", "Stores unique booking reference (CB-YYYY-XXXX), patron details, subtotal, and status."),
            ("booking_seats", "Junction table storing specific seat numbers, tiers, and prices locked to a booking.")
        ]

        for tbl, desc in tables_info:
            row = tk.Frame(card, bg=BG_CARD)
            row.pack(fill="x", pady=2)
            tk.Label(row, text=f"• {tbl}:", font=FONT_BODY_BOLD, fg=ACCENT_VIOLET, bg=BG_CARD, width=16, anchor="w").pack(side="left")
            tk.Label(row, text=desc, font=FONT_BODY, fg=TEXT_SECONDARY, bg=BG_CARD).pack(side="left")

    def _build_viva_qa_card(self) -> None:
        """Faculty Viva Examination Questions and Concise Model Answers."""
        card = tk.Frame(self.content, bg=BG_CARD, padx=24, pady=20,
                        highlightthickness=1, highlightbackground=BORDER_COLOR)
        card.pack(fill="x", padx=24, pady=(0, 16))

        tk.Label(card, text="FREQUENTLY ASKED VIVA QUESTIONS & ANSWERS", font=FONT_TITLE, fg=TEXT_PRIMARY, bg=BG_CARD).pack(anchor="w")

        qa_list = [
            (
                "Q1: How does CineBook prevent two users from reserving the same seat simultaneously?",
                "Answer: Through SQLite transactions. The `create_booking` method uses `with conn:` to run an atomic transaction. Before writing to the database, it performs a locked query on `show_seats` for all requested seat numbers with `status = 'AVAILABLE'`. If any seat is already booked or missing, the method raises `SeatUnavailableError` and rolls back the transaction, guaranteeing zero partial or duplicate bookings."
            ),
            (
                "Q2: How does the interactive seat matrix dynamically calculate prices?",
                "Answer: Each seat widget maintains its tier and price. When clicked, it toggles its presence in a Python `Set[str]` of selected seats. Whenever the set changes, `_recalculate_total()` iterates over the selected seats, aggregates counts per tier, recalculates subtotal and convenience fee, and immediately updates Tkinter labels."
            ),
            (
                "Q3: How are views switched without opening multiple messy windows?",
                "Answer: The main window (`main.py`) acts as a Single-Window Controller. It owns a central content container frame. Whenever navigation occurs (e.g. Home to Details, or Seats to Checkout), the controller removes the current frame using `pack_forget()` or `destroy()`, instantiates the new View frame, and packs it into the container."
            ),
            (
                "Q4: How does cancellation restore theatre inventory?",
                "Answer: In `cancel_booking()`, SQLite executes two operations atomically: it updates the `bookings` table to `booking_status = 'CANCELLED'` and sets `cancelled_at = CURRENT_TIMESTAMP`, while simultaneously updating `show_seats` setting `status = 'AVAILABLE'` and `booking_id = NULL` for all seats reserved under that booking ID."
            ),
            (
                "Q5: How does the program ensure it works when external poster images are absent?",
                "Answer: The `PosterWidget` class checks file existence and PIL availability. If a poster image file is missing, it falls back to a procedural canvas drawing with geometric film reels, badges, and titles rendered with native Tkinter canvas methods, ensuring zero crashes."
            ),
        ]

        for q, a in qa_list:
            box = tk.Frame(card, bg=BG_INPUT, padx=14, pady=10,
                           highlightthickness=1, highlightbackground=BORDER_COLOR)
            box.pack(fill="x", pady=6)

            tk.Label(box, text=q, font=FONT_BODY_BOLD, fg=ACCENT_CYAN, bg=BG_INPUT,
                     wraplength=820, justify="left").pack(anchor="w")
            tk.Label(box, text=a, font=FONT_BODY, fg=TEXT_SECONDARY, bg=BG_INPUT,
                     wraplength=820, justify="left").pack(anchor="w", pady=(4, 0))

    def _build_database_tools_card(self) -> None:
        """Database maintenance and reset option for demonstrations."""
        card = tk.Frame(self.content, bg=BG_CARD, padx=24, pady=20,
                        highlightthickness=1, highlightbackground=BORDER_COLOR)
        card.pack(fill="x", padx=24, pady=(0, 24))

        tk.Label(card, text="DEMONSTRATION UTILITIES", font=FONT_TITLE, fg=TEXT_PRIMARY, bg=BG_CARD).pack(anchor="w")
        tk.Label(
            card,
            text=f"Active SQLite Database File: {self.db.db_path}",
            font=FONT_SMALL,
            fg=TEXT_MUTED,
            bg=BG_CARD
        ).pack(anchor="w", pady=(2, 12))

        reset_btn = ModernButton(
            card,
            text="🔄 Reset Sample Database to Factory Defaults",
            command=self._handle_reset_db,
            bg=BG_INPUT,
            hover_bg=COLOR_DANGER,
            fg=COLOR_DANGER
        )
        reset_btn.pack(anchor="w")

    def _handle_reset_db(self) -> None:
        """Allows resetting database to clean seed state for viva demonstrations."""
        confirm = messagebox.askyesno(
            "Confirm Database Reset",
            "This will delete all current bookings and recreate fresh sample data.\n\n"
            "Do you want to proceed with factory reset?",
            icon="warning"
        )
        if not confirm:
            return

        try:
            # Delete db file and recreate
            p = Path(self.db.db_path)
            if p.exists():
                p.unlink()
            self.db._init_database()
            messagebox.showinfo("Reset Complete", "Database has been reset to initial demonstration state.")
            self.on_go_home()
        except Exception as e:
            messagebox.showerror("Reset Failed", f"Could not reset database:\n{e}")
