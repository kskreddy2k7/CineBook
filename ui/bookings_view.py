"""
CineBook - My Bookings View (BookMyShow-Style Light Theme)
Interactive booking history table using ttk.Treeview, horizontal & vertical scrolling,
responsive pinned action toolbar, alternating row styles, live search & status filters,
informative empty state, and transactional ticket cancellation.
"""

from typing import Callable, Optional
import tkinter as tk
from tkinter import ttk, messagebox

from database import DatabaseManager, DatabaseError, BookingNotFoundError
from models import Booking
from ui.theme import (
    BG_PAGE, BG_CARD, BG_INPUT, BORDER_COLOR, BORDER_LIGHT, BORDER_CARD,
    ACCENT_RED, ACCENT_RED_HOVER, ACCENT_RED_LIGHT, ACCENT_CYAN, ACCENT_GOLD,
    COLOR_SUCCESS, COLOR_DANGER,
    TEXT_PRIMARY, TEXT_SECONDARY, TEXT_MUTED, TEXT_DARK, TEXT_LIGHT,
    FONT_HERO, FONT_TITLE, FONT_SUBTITLE, FONT_CARD_TITLE,
    FONT_BODY, FONT_BODY_BOLD, FONT_SMALL, FONT_SMALL_BOLD, FONT_BADGE,
    FONT_TABLE, FONT_TABLE_BOLD, FONT_TABLE_HEAD, FONT_BTN
)
from ui.components import ModernButton


class BookingsView(tk.Frame):
    """Booking management, search, ticket inspection, and cancellation interface."""

    def __init__(
        self,
        master,
        db: DatabaseManager,
        on_view_ticket: Callable[[Booking], None],
        on_go_home: Callable[[], None],
        **kwargs
    ):
        super().__init__(master, bg=BG_PAGE, **kwargs)
        self.db = db
        self.on_view_ticket = on_view_ticket
        self.on_go_home = on_go_home

        self.current_filter = "ALL"
        self.search_var = tk.StringVar()
        self.search_var.trace_add("write", lambda *args: self._on_search_changed())

        # Centered container with generous horizontal margins & responsive padding
        self.main_wrapper = tk.Frame(self, bg=BG_PAGE)
        self.main_wrapper.pack(fill="both", expand=True, padx=32, pady=(14, 18))

        self._build_header()
        self._build_toolbar()
        # Action toolbar pinned to bottom FIRST so it is NEVER clipped or hidden
        self._build_action_bar()
        # Table expands into all remaining vertical space
        self._build_table()
        self._refresh_table()

    def _build_header(self) -> None:
        """Top banner and navigation."""
        top_bar = tk.Frame(self.main_wrapper, bg=BG_PAGE)
        top_bar.pack(side="top", fill="x", pady=(0, 12))

        title_col = tk.Frame(top_bar, bg=BG_PAGE)
        title_col.pack(side="left")

        tk.Label(
            title_col,
            text="My Bookings & Reservations",
            font=FONT_HERO,
            fg=TEXT_PRIMARY,
            bg=BG_PAGE
        ).pack(anchor="w")

        tk.Label(
            title_col,
            text="Review digital ticket passes, check booking status, export tickets, or cancel reservations.",
            font=FONT_BODY,
            fg=TEXT_SECONDARY,
            bg=BG_PAGE
        ).pack(anchor="w", pady=(2, 0))

        home_btn = tk.Label(
            top_bar,
            text="← Back to Discovery",
            font=FONT_BODY_BOLD,
            fg=ACCENT_RED,
            bg=BG_PAGE,
            cursor="hand2"
        )
        home_btn.pack(side="right")
        home_btn.bind("<Button-1>", lambda e: self.on_go_home())

    def _build_toolbar(self) -> None:
        """Search bar and status filter buttons."""
        bar_card = tk.Frame(
            self.main_wrapper,
            bg=BG_CARD,
            padx=16,
            pady=10,
            highlightthickness=1,
            highlightbackground=BORDER_CARD
        )
        bar_card.pack(side="top", fill="x", pady=(0, 12))

        # Search box
        search_frame = tk.Frame(
            bar_card,
            bg="#F8F9FA",
            padx=10,
            pady=6,
            highlightthickness=1,
            highlightbackground=BORDER_CARD
        )
        search_frame.pack(side="left", fill="x", expand=True, padx=(0, 16))

        tk.Label(search_frame, text="🔍", font=FONT_BODY, bg="#F8F9FA", fg=TEXT_MUTED).pack(side="left", padx=(0, 6))

        search_entry = tk.Entry(
            search_frame,
            textvariable=self.search_var,
            font=FONT_BODY,
            bg="#F8F9FA",
            fg=TEXT_PRIMARY,
            insertbackground=TEXT_PRIMARY,
            relief="flat",
            bd=0
        )
        search_entry.pack(side="left", fill="x", expand=True)

        clear_btn = tk.Label(search_frame, text="✖", font=FONT_SMALL, fg=TEXT_MUTED, bg="#F8F9FA", cursor="hand2")
        clear_btn.pack(side="right")
        clear_btn.bind("<Button-1>", lambda e: self.search_var.set(""))

        # Status filter tabs
        filter_box = tk.Frame(bar_card, bg=BG_CARD)
        filter_box.pack(side="right")

        tk.Label(filter_box, text="STATUS:", font=FONT_BADGE, fg=TEXT_MUTED, bg=BG_CARD).pack(side="left", padx=(0, 8))

        self.filter_buttons = {}
        for f_key, f_label in [("ALL", "All"), ("CONFIRMED", "Confirmed"), ("CANCELLED", "Cancelled")]:
            is_active = (f_key == self.current_filter)
            btn = tk.Label(
                filter_box,
                text=f_label,
                font=FONT_SMALL_BOLD,
                bg=ACCENT_RED if is_active else "#F8F9FA",
                fg="#FFFFFF" if is_active else TEXT_SECONDARY,
                padx=12,
                pady=6,
                cursor="hand2",
                highlightthickness=1,
                highlightbackground=BORDER_CARD
            )
            btn.pack(side="left", padx=3)
            btn.bind("<Button-1>", lambda e, k=f_key: self._on_filter_clicked(k))
            self.filter_buttons[f_key] = btn

    def _on_filter_clicked(self, filter_key: str) -> None:
        self.current_filter = filter_key
        for k, btn in self.filter_buttons.items():
            if k == filter_key:
                btn.config(bg=ACCENT_RED, fg="#FFFFFF", highlightbackground=ACCENT_RED)
            else:
                btn.config(bg="#F8F9FA", fg=TEXT_SECONDARY, highlightbackground=BORDER_CARD)
        self._refresh_table()

    def _on_search_changed(self) -> None:
        self._refresh_table()

    def _build_action_bar(self) -> None:
        """
        Dedicated persistent action toolbar pinned to the bottom of the page.
        Guaranteed to remain completely visible at any resolution (1366x768, 1920x1080)
        and never pushed off-screen by table rows.
        """
        self.action_card = tk.Frame(
            self.main_wrapper,
            bg=BG_CARD,
            padx=18,
            pady=12,
            highlightthickness=1,
            highlightbackground=BORDER_CARD
        )
        self.action_card.pack(side="bottom", fill="x", pady=(12, 0))

        # Left action buttons
        left_actions = tk.Frame(self.action_card, bg=BG_CARD)
        left_actions.pack(side="left")

        self.view_btn = ModernButton(
            left_actions,
            text="🔍 View Full Ticket",
            command=self._handle_view_ticket,
            bg=ACCENT_RED,
            hover_bg=ACCENT_RED_HOVER,
            font=FONT_BTN,
            padx=16,
            pady=8,
            state="disabled"
        )
        self.view_btn.pack(side="left", padx=(0, 10))

        self.cancel_btn = ModernButton(
            left_actions,
            text="❌ Cancel Selected Booking",
            command=self._handle_cancel_booking,
            bg="#FFFFFF",
            hover_bg="#FEE2E2",
            fg=COLOR_DANGER,
            font=FONT_BTN,
            padx=16,
            pady=8,
            state="disabled",
            highlightthickness=1,
            highlightbackground="#FECACA"
        )
        self.cancel_btn.pack(side="left", padx=(0, 10))

        self.refresh_btn = ModernButton(
            left_actions,
            text="🔄 Refresh Data",
            command=self._refresh_table,
            bg="#F8F9FA",
            hover_bg="#E2E8F0",
            fg=TEXT_PRIMARY,
            font=FONT_BODY_BOLD,
            padx=14,
            pady=8
        )
        self.refresh_btn.pack(side="left")

        # Right selection metadata status readout
        self.selection_status_lbl = tk.Label(
            self.action_card,
            text="Click a booking row above to inspect pass or cancel reservation",
            font=FONT_BODY,
            fg=TEXT_MUTED,
            bg=BG_CARD
        )
        self.selection_status_lbl.pack(side="right")

    def _build_table(self) -> None:
        """
        Constructs ttk.Treeview with both horizontal and vertical scrolling,
        10 readable columns with sufficient padding and alternating rows.
        """
        self.table_container = tk.Frame(
            self.main_wrapper,
            bg=BG_CARD,
            highlightthickness=1,
            highlightbackground=BORDER_CARD
        )
        self.table_container.pack(side="top", fill="both", expand=True)

        columns = (
            "ref", "customer", "movie", "theatre", "date",
            "time", "screen", "seats", "total", "status"
        )

        self.tree = ttk.Treeview(
            self.table_container,
            columns=columns,
            show="headings",
            selectmode="browse"
        )

        # 10 Columns: Reference, Customer, Movie Title, Theatre, Show Date, Time, Screen, Seats, Total, Status
        self.tree.heading("ref", text="Reference", anchor="w")
        self.tree.heading("customer", text="Customer", anchor="w")
        self.tree.heading("movie", text="Movie Title", anchor="w")
        self.tree.heading("theatre", text="Theatre", anchor="w")
        self.tree.heading("date", text="Show Date", anchor="center")
        self.tree.heading("time", text="Time", anchor="center")
        self.tree.heading("screen", text="Screen", anchor="w")
        self.tree.heading("seats", text="Seats", anchor="center")
        self.tree.heading("total", text="Total (₹)", anchor="e")
        self.tree.heading("status", text="Status", anchor="center")

        # Generous readable column widths
        self.tree.column("ref", width=125, minwidth=110, anchor="w")
        self.tree.column("customer", width=140, minwidth=120, anchor="w")
        self.tree.column("movie", width=180, minwidth=140, anchor="w")
        self.tree.column("theatre", width=165, minwidth=135, anchor="w")
        self.tree.column("date", width=100, minwidth=90, anchor="center")
        self.tree.column("time", width=85, minwidth=75, anchor="center")
        self.tree.column("screen", width=130, minwidth=110, anchor="w")
        self.tree.column("seats", width=90, minwidth=75, anchor="center")
        self.tree.column("total", width=95, minwidth=85, anchor="e")
        self.tree.column("status", width=115, minwidth=100, anchor="center")

        # Scrollbars (Vertical + Horizontal)
        v_scroll = ttk.Scrollbar(self.table_container, orient="vertical", command=self.tree.yview)
        h_scroll = ttk.Scrollbar(self.table_container, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=v_scroll.set, xscrollcommand=h_scroll.set)

        # Grid placement inside table_container ensures proper responsive sizing
        self.tree.grid(row=0, column=0, sticky="nsew")
        v_scroll.grid(row=0, column=1, sticky="ns")
        h_scroll.grid(row=1, column=0, sticky="ew")

        self.table_container.grid_rowconfigure(0, weight=1)
        self.table_container.grid_columnconfigure(0, weight=1)

        # Event bindings
        self.tree.bind("<<TreeviewSelect>>", self._on_tree_selection_changed)
        self.tree.bind("<Double-1>", lambda e: self._handle_view_ticket())

        # Tag configurations for alternating rows & high-contrast statuses
        self.tree.tag_configure("even_row", background="#FFFFFF")
        self.tree.tag_configure("odd_row", background="#F8FAFC")
        self.tree.tag_configure("CONFIRMED", foreground=COLOR_SUCCESS)
        self.tree.tag_configure("CANCELLED", foreground=COLOR_DANGER)

        # Empty state overlay container
        self.empty_frame = tk.Frame(self.table_container, bg=BG_CARD)

    def _on_tree_selection_changed(self, event=None) -> None:
        """Updates action toolbar when user selects a booking row."""
        selected = self.tree.selection()
        if not selected:
            self.selection_status_lbl.config(
                text="Click a booking row above to inspect pass or cancel reservation",
                fg=TEXT_MUTED
            )
            self.view_btn.set_state("disabled")
            self.cancel_btn.set_state("disabled")
            return

        b_id = int(selected[0])
        booking = self.db.get_booking_by_ref_or_id(b_id)
        if booking:
            status_txt = "● CONFIRMED" if booking.booking_status == "CONFIRMED" else "✕ CANCELLED"
            status_color = COLOR_SUCCESS if booking.booking_status == "CONFIRMED" else COLOR_DANGER
            self.selection_status_lbl.config(
                text=f"Selected: {booking.booking_ref}  |  {booking.movie_title} ({booking.seats_display})  |  ₹{booking.total_price:.2f} [{status_txt}]",
                fg=TEXT_PRIMARY
            )
            self.view_btn.set_state("normal")
            if booking.booking_status == "CONFIRMED":
                self.cancel_btn.set_state("normal")
                self.cancel_btn.label.config(text="❌ Cancel Selected Booking")
            else:
                self.cancel_btn.set_state("disabled")
                self.cancel_btn.label.config(text="✕ Already Cancelled")

    def _refresh_table(self) -> None:
        """Fetch matching records from database and populate Treeview with alternating colors."""
        for item in self.tree.get_children():
            self.tree.delete(item)

        bookings = self.db.get_all_bookings(
            search_term=self.search_var.get(),
            status_filter=self.current_filter
        )

        if not bookings:
            self._render_empty_state()
            self.view_btn.set_state("disabled")
            self.cancel_btn.set_state("disabled")
            self.selection_status_lbl.config(
                text="0 bookings found matching current criteria",
                fg=TEXT_MUTED
            )
            return

        # Hide empty frame if previously shown
        self.empty_frame.grid_forget()

        for idx, b in enumerate(bookings):
            row_tag = "even_row" if idx % 2 == 0 else "odd_row"
            status_tag = b.booking_status
            status_display = f"● {b.booking_status}" if b.booking_status == "CONFIRMED" else f"✕ {b.booking_status}"

            self.tree.insert(
                "",
                "end",
                iid=str(b.id),
                values=(
                    b.booking_ref,
                    b.customer_name,
                    b.movie_title or "N/A",
                    b.theatre_name or "CineBook Cinemas",
                    b.show_date or "N/A",
                    b.show_time or "N/A",
                    b.screen_name or "Audi 1",
                    b.seats_display,
                    f"₹{b.total_price:.2f}",
                    status_display
                ),
                tags=(row_tag, status_tag)
            )

        # Reset selection state
        self.view_btn.set_state("disabled")
        self.cancel_btn.set_state("disabled")
        self.selection_status_lbl.config(
            text=f"Total: {len(bookings)} reservation{'s' if len(bookings) > 1 else ''} found. Click any row to view pass.",
            fg=TEXT_MUTED
        )

    def _render_empty_state(self) -> None:
        """Renders a helpful empty state when no bookings exist or match search."""
        for w in self.empty_frame.winfo_children():
            w.destroy()

        self.empty_frame.grid(row=0, column=0, sticky="nsew")
        self.empty_frame.lift()

        center_box = tk.Frame(self.empty_frame, bg=BG_CARD)
        center_box.place(relx=0.5, rely=0.5, anchor="center")

        tk.Label(
            center_box,
            text="🎟️",
            font=("Segoe UI", 36),
            bg=BG_CARD,
            fg=TEXT_MUTED
        ).pack(pady=(0, 8))

        is_filtered = bool(self.search_var.get().strip() or self.current_filter != "ALL")

        title_text = "No Reservations Match Filters" if is_filtered else "No Bookings Recorded Yet"
        tk.Label(
            center_box,
            text=title_text,
            font=FONT_TITLE,
            fg=TEXT_PRIMARY,
            bg=BG_CARD
        ).pack(pady=(0, 4))

        if is_filtered:
            desc_text = f"No bookings found for search '{self.search_var.get()}' with status '{self.current_filter}'. Try resetting filters."
            tk.Label(
                center_box,
                text=desc_text,
                font=FONT_BODY,
                fg=TEXT_SECONDARY,
                bg=BG_CARD,
                wraplength=460,
                justify="center"
            ).pack(pady=(0, 16))

            reset_btn = ModernButton(
                center_box,
                text="Reset Search & Filters",
                command=self._reset_search_and_filters,
                bg=ACCENT_RED,
                hover_bg=ACCENT_RED_HOVER,
                font=FONT_BODY_BOLD
            )
            reset_btn.pack()
        else:
            desc_text = "You haven't booked any movie tickets yet. Browse our Indian cinema catalogue, select showtimes, and book tickets!"
            tk.Label(
                center_box,
                text=desc_text,
                font=FONT_BODY,
                fg=TEXT_SECONDARY,
                bg=BG_CARD,
                wraplength=460,
                justify="center"
            ).pack(pady=(0, 16))

            explore_btn = ModernButton(
                center_box,
                text="🎬 Explore Indian Movies Now",
                command=self.on_go_home,
                bg=ACCENT_RED,
                hover_bg=ACCENT_RED_HOVER,
                font=FONT_BODY_BOLD
            )
            explore_btn.pack()

    def _reset_search_and_filters(self) -> None:
        """Clears search input and sets filter back to ALL."""
        self.search_var.set("")
        self._on_filter_clicked("ALL")

    def _get_selected_booking_id(self) -> Optional[int]:
        selected = self.tree.selection()
        if not selected:
            messagebox.showinfo("Select Booking", "Please click a booking row from the table first.")
            return None
        return int(selected[0])

    def _handle_view_ticket(self) -> None:
        b_id = self._get_selected_booking_id()
        if b_id is None:
            return
        booking = self.db.get_booking_by_ref_or_id(b_id)
        if booking:
            self.on_view_ticket(booking)
        else:
            messagebox.showerror("Error", "Booking details could not be loaded.")

    def _handle_cancel_booking(self) -> None:
        b_id = self._get_selected_booking_id()
        if b_id is None:
            return

        booking = self.db.get_booking_by_ref_or_id(b_id)
        if not booking:
            messagebox.showerror("Error", "Booking record could not be found.")
            return

        if booking.booking_status == "CANCELLED":
            messagebox.showinfo("Already Cancelled", f"Booking {booking.booking_ref} is already cancelled.")
            return

        confirmed = messagebox.askyesno(
            "Confirm Cancellation",
            f"Are you sure you want to cancel booking {booking.booking_ref}?\n\n"
            f"Movie: {booking.movie_title}\n"
            f"Theatre: {booking.theatre_name}\n"
            f"Seats: {booking.seats_display}\n"
            f"Refund Amount: ₹{booking.total_price:.2f}\n\n"
            "This will release the reserved seats back into inventory."
        )

        if not confirmed:
            return

        try:
            self.db.cancel_booking(booking.booking_ref)
            messagebox.showinfo(
                "Booking Cancelled",
                f"Booking {booking.booking_ref} has been successfully cancelled.\n"
                f"Seats ({booking.seats_display}) have been restored to available inventory."
            )
            self._refresh_table()
        except DatabaseError as e:
            messagebox.showerror("Cancellation Failed", f"Could not cancel booking: {e}")
