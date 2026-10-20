"""
CineBook - Digital Cinema Ticket View (BookMyShow-Style Light Theme)
High-fidelity digital ticket pass with perforated styling,
barcode rendering, metadata summary, and file export (HTML & text).
"""

from pathlib import Path
from typing import Callable, Optional
import tkinter as tk
from tkinter import messagebox

from models import Booking
from ui.theme import (
    BG_PAGE, BG_CARD, BG_INPUT, BORDER_COLOR, BORDER_LIGHT, BORDER_CARD,
    ACCENT_RED, ACCENT_RED_HOVER, ACCENT_RED_LIGHT, ACCENT_CYAN, ACCENT_GOLD,
    COLOR_SUCCESS, COLOR_DANGER,
    TEXT_PRIMARY, TEXT_SECONDARY, TEXT_MUTED, TEXT_DARK, TEXT_LIGHT,
    FONT_HERO, FONT_TITLE, FONT_SUBTITLE, FONT_CARD_TITLE,
    FONT_BODY, FONT_BODY_BOLD, FONT_SMALL, FONT_SMALL_BOLD, FONT_BADGE,
    FONT_MONO, FONT_MONO_BOLD
)
from ui.components import ScrollableFrame, ModernButton


class TicketView(tk.Frame):
    """Digital Pass display and ticket export interface."""

    def __init__(
        self,
        master,
        booking: Booking,
        on_go_home: Callable[[], None],
        on_view_bookings: Callable[[], None],
        **kwargs
    ):
        super().__init__(master, bg=BG_PAGE, **kwargs)
        self.booking = booking
        self.on_go_home = on_go_home
        self.on_view_bookings = on_view_bookings

        self.scroll_container = ScrollableFrame(self, bg=BG_PAGE)
        self.scroll_container.pack(fill="both", expand=True)
        self.content = self.scroll_container.scrollable_content

        # Centered container with generous horizontal margins
        self.main_wrapper = tk.Frame(self.content, bg=BG_PAGE)
        self.main_wrapper.pack(fill="x", padx=48, pady=(16, 36))

        self._build_top_actions()
        self._build_ticket_card()

    def _build_top_actions(self) -> None:
        """Top action bar for returning home or saving."""
        bar = tk.Frame(self.main_wrapper, bg=BG_PAGE)
        bar.pack(fill="x", pady=(0, 14))

        home_btn = tk.Label(
            bar,
            text="🏠 Back to Discovery",
            font=FONT_BODY_BOLD,
            fg=ACCENT_RED,
            bg=BG_PAGE,
            cursor="hand2"
        )
        home_btn.pack(side="left")
        home_btn.bind("<Button-1>", lambda e: self.on_go_home())

        bookings_btn = tk.Label(
            bar,
            text="🎟 Go to My Bookings →",
            font=FONT_BODY_BOLD,
            fg=TEXT_PRIMARY,
            bg=BG_PAGE,
            cursor="hand2"
        )
        bookings_btn.pack(side="right")
        bookings_btn.bind("<Button-1>", lambda e: self.on_view_bookings())

    def _build_ticket_card(self) -> None:
        """Constructs a boarding-pass styled digital ticket."""
        center_container = tk.Frame(self.main_wrapper, bg=BG_PAGE)
        center_container.pack(fill="x", pady=(0, 24))

        # Main Ticket Frame
        self.ticket_card = tk.Frame(
            center_container,
            bg=BG_CARD,
            padx=32,
            pady=28,
            highlightthickness=1,
            highlightbackground=BORDER_CARD
        )
        self.ticket_card.pack(fill="x", expand=True, padx=40)

        # Header: Brand & Status
        header_row = tk.Frame(self.ticket_card, bg=BG_CARD)
        header_row.pack(fill="x", pady=(0, 16))

        logo_col = tk.Frame(header_row, bg=BG_CARD)
        logo_col.pack(side="left")

        tk.Label(logo_col, text="🎬 CINEBOOK CINEMAS", font=FONT_HERO, fg=TEXT_PRIMARY, bg=BG_CARD).pack(anchor="w")
        tk.Label(logo_col, text="Digital Cinema Reservation Pass", font=FONT_SMALL, fg=ACCENT_RED, bg=BG_CARD).pack(anchor="w")

        status_col = tk.Frame(header_row, bg=BG_CARD)
        status_col.pack(side="right")

        status_text = "CONFIRMED RESERVATION" if self.booking.booking_status == "CONFIRMED" else "CANCELLED"
        status_bg = COLOR_SUCCESS if self.booking.booking_status == "CONFIRMED" else COLOR_DANGER

        tk.Label(
            status_col,
            text=status_text,
            font=FONT_BADGE,
            fg="#FFFFFF",
            bg=status_bg,
            padx=12,
            pady=4
        ).pack(anchor="e")

        # Dashed perforated divider line
        self._draw_perforated_line(self.ticket_card)

        # Booking Reference Banner
        ref_box = tk.Frame(
            self.ticket_card,
            bg="#F8F9FA",
            padx=20,
            pady=12,
            highlightthickness=1,
            highlightbackground=BORDER_CARD
        )
        ref_box.pack(fill="x", pady=(14, 20))

        tk.Label(ref_box, text="BOOKING REFERENCE NUMBER", font=FONT_BADGE, fg=TEXT_MUTED, bg="#F8F9FA").pack(side="left")

        ref_lbl = tk.Label(ref_box, text=self.booking.booking_ref, font=FONT_MONO_BOLD, fg=ACCENT_RED, bg="#F8F9FA")
        ref_lbl.pack(side="left", padx=16)

        copy_btn = tk.Label(ref_box, text="📋 Copy Ref", font=FONT_SMALL_BOLD, fg=TEXT_PRIMARY, bg="#F8F9FA", cursor="hand2")
        copy_btn.pack(side="right")
        copy_btn.bind("<Button-1>", lambda e: self._copy_ref())

        # Ticket Content 2-Column Grid
        info_grid = tk.Frame(self.ticket_card, bg=BG_CARD)
        info_grid.pack(fill="x", pady=(0, 20))

        info_grid.columnconfigure(0, weight=3)
        info_grid.columnconfigure(1, weight=2)

        # Left Column: Movie & Showing
        left_info = tk.Frame(info_grid, bg=BG_CARD)
        left_info.grid(row=0, column=0, sticky="nw")

        tk.Label(left_info, text="MOVIE TITLE", font=FONT_BADGE, fg=TEXT_MUTED, bg=BG_CARD).pack(anchor="w")
        tk.Label(left_info, text=self.booking.movie_title or "Movie", font=FONT_TITLE, fg=TEXT_PRIMARY, bg=BG_CARD).pack(anchor="w", pady=(2, 12))

        tk.Label(left_info, text="AUDITORIUM / SCREEN", font=FONT_BADGE, fg=TEXT_MUTED, bg=BG_CARD).pack(anchor="w")
        tk.Label(left_info, text=self.booking.screen_name or "Audi 1", font=FONT_SUBTITLE, fg=ACCENT_CYAN, bg=BG_CARD).pack(anchor="w", pady=(2, 12))

        tk.Label(left_info, text="DATE & SHOWTIME", font=FONT_BADGE, fg=TEXT_MUTED, bg=BG_CARD).pack(anchor="w")
        tk.Label(left_info, text=f"{self.booking.show_date} at {self.booking.show_time}", font=FONT_BODY_BOLD, fg=TEXT_PRIMARY, bg=BG_CARD).pack(anchor="w", pady=(2, 0))

        # Right Column: Seats & Customer
        right_info = tk.Frame(info_grid, bg=BG_CARD)
        right_info.grid(row=0, column=1, sticky="nw")

        tk.Label(right_info, text="PATRON NAME", font=FONT_BADGE, fg=TEXT_MUTED, bg=BG_CARD).pack(anchor="w")
        tk.Label(right_info, text=self.booking.customer_name, font=FONT_BODY_BOLD, fg=TEXT_PRIMARY, bg=BG_CARD).pack(anchor="w", pady=(2, 12))

        tk.Label(right_info, text="CONTACT", font=FONT_BADGE, fg=TEXT_MUTED, bg=BG_CARD).pack(anchor="w")
        contact_str = self.booking.customer_phone
        if self.booking.customer_email:
            contact_str += f" | {self.booking.customer_email}"
        tk.Label(right_info, text=contact_str, font=FONT_SMALL, fg=TEXT_SECONDARY, bg=BG_CARD).pack(anchor="w", pady=(2, 12))

        tk.Label(right_info, text=f"CONFIRMED SEATS ({self.booking.seat_count})", font=FONT_BADGE, fg=TEXT_MUTED, bg=BG_CARD).pack(anchor="w")

        # Seats Pills
        seats_row = tk.Frame(right_info, bg=BG_CARD)
        seats_row.pack(anchor="w", pady=(4, 0))

        for seat_num in self.booking.seats:
            tk.Label(
                seats_row,
                text=seat_num,
                font=FONT_BADGE,
                fg="#FFFFFF",
                bg=ACCENT_RED,
                padx=8,
                pady=2,
                highlightthickness=1,
                highlightbackground="#FDA4AF"
            ).pack(side="left", padx=(0, 4))

        # Divider
        self._draw_perforated_line(self.ticket_card)

        # Payment & Barcode Row
        bot_row = tk.Frame(self.ticket_card, bg=BG_CARD)
        bot_row.pack(fill="x", pady=(16, 20))

        # Left side: simulated barcode
        barcode_frame = tk.Frame(bot_row, bg=BG_CARD)
        barcode_frame.pack(side="left")

        barcode_canvas = tk.Canvas(barcode_frame, width=280, height=54, bg="#FFFFFF", highlightthickness=1, highlightbackground=BORDER_CARD)
        barcode_canvas.pack(anchor="w")
        self._draw_barcode(barcode_canvas, self.booking.booking_ref)

        tk.Label(barcode_frame, text=f"PASS REF: {self.booking.booking_ref}",
                 font=FONT_MONO, fg=TEXT_MUTED, bg=BG_CARD).pack(anchor="w", pady=(4, 0))

        # Right side: Itemized price total
        price_box = tk.Frame(bot_row, bg=BG_CARD)
        price_box.pack(side="right")

        tk.Label(price_box, text=f"Subtotal: ₹{self.booking.subtotal:.2f}  |  Fee: ₹{self.booking.convenience_fee:.2f}",
                 font=FONT_SMALL, fg=TEXT_MUTED, bg=BG_CARD).pack(anchor="e")
        tk.Label(price_box, text=f"TOTAL PAID: ₹{self.booking.total_price:.2f}",
                 font=FONT_TITLE, fg=ACCENT_RED, bg=BG_CARD).pack(anchor="e", pady=(2, 0))

        # Buttons Toolbar
        btn_bar = tk.Frame(self.ticket_card, bg=BG_CARD)
        btn_bar.pack(fill="x", pady=(10, 0))

        export_html_btn = ModernButton(
            btn_bar,
            text="💾 Save Ticket (HTML & Text)",
            command=self._export_ticket,
            bg=ACCENT_RED,
            hover_bg=ACCENT_RED_HOVER
        )
        export_html_btn.pack(side="left", padx=(0, 10))

        view_all_btn = ModernButton(
            btn_bar,
            text="🎟 My Bookings",
            command=self.on_view_bookings,
            bg="#F1F3F6",
            hover_bg="#E2E8F0",
            fg=TEXT_PRIMARY
        )
        view_all_btn.pack(side="left", padx=(0, 10))

        book_more_btn = ModernButton(
            btn_bar,
            text="🎬 Book Another Movie",
            command=self.on_go_home,
            bg="#F1F3F6",
            hover_bg="#E2E8F0",
            fg=TEXT_PRIMARY
        )
        book_more_btn.pack(side="left")

    def _draw_perforated_line(self, parent: tk.Widget) -> None:
        """Draws a cinema perforated ticket border effect."""
        canvas = tk.Canvas(parent, height=12, bg=BG_CARD, highlightthickness=0)
        canvas.pack(fill="x", pady=8)

        def render_line(event=None):
            canvas.delete("all")
            w = canvas.winfo_width()
            if w <= 1:
                w = 800
            for x in range(0, w, 14):
                canvas.create_line(x, 6, x + 8, 6, fill=BORDER_LIGHT, width=1)
            canvas.create_oval(-10, -4, 10, 16, fill=BG_PAGE, outline=BORDER_COLOR)
            canvas.create_oval(w - 10, -4, w + 10, 16, fill=BG_PAGE, outline=BORDER_COLOR)

        canvas.bind("<Configure>", render_line)
        render_line()

    def _draw_barcode(self, canvas: tk.Canvas, seed_str: str) -> None:
        """Procedurally draws realistic barcode lines based on the booking ref."""
        canvas.delete("all")
        w, h = 280, 54
        x = 16
        pattern = [1, 2, 1, 3, 1, 1, 2, 1, 3, 2, 1, 2, 3, 1, 1, 2, 1, 3, 1, 2, 1, 1, 3, 2, 1, 2, 1, 3, 2, 1]

        for char in seed_str:
            c_val = ord(char) % 3 + 1
            pattern.append(c_val)

        p_idx = 0
        while x < w - 16:
            bar_w = pattern[p_idx % len(pattern)]
            canvas.create_rectangle(x, 8, x + bar_w, h - 8, fill="#1F2533", outline="")
            gap = 2 if bar_w == 1 else 3
            x += bar_w + gap
            p_idx += 1

    def _copy_ref(self) -> None:
        """Copies booking ref to clipboard."""
        self.clipboard_clear()
        self.clipboard_append(self.booking.booking_ref)
        messagebox.showinfo("Copied", f"Booking Reference '{self.booking.booking_ref}' copied to clipboard!")

    def _export_ticket(self) -> None:
        """Exports ticket to HTML and Plain Text in the exports/ directory."""
        exports_dir = Path(__file__).resolve().parent.parent / "exports"
        exports_dir.mkdir(parents=True, exist_ok=True)

        ref_clean = self.booking.booking_ref.replace("-", "_")
        txt_path = exports_dir / f"ticket_{ref_clean}.txt"
        html_path = exports_dir / f"ticket_{ref_clean}.html"

        try:
            # 1. Plain text export
            txt_content = f"""=======================================================
               CINEBOOK CINEMA DIGITAL PASS
=======================================================
Booking Reference : {self.booking.booking_ref}
Status            : {self.booking.booking_status}
-------------------------------------------------------
Movie Title       : {self.booking.movie_title or 'Cinema Feature'}
Auditorium        : {self.booking.screen_name or 'Main Screen'}
Show Date & Time  : {self.booking.show_date} at {self.booking.show_time}
Seats Reserved    : {', '.join(self.booking.seats)} (Count: {self.booking.seat_count})
-------------------------------------------------------
CUSTOMER INFORMATION:
Patron Name       : {self.booking.customer_name}
Contact Number    : {self.booking.customer_phone}
Email Address     : {self.booking.customer_email or 'N/A'}
-------------------------------------------------------
PRICE BREAKDOWN:
Ticket Subtotal   : Rs. {self.booking.subtotal:.2f}
Convenience Fee   : Rs. {self.booking.convenience_fee:.2f}
Total Paid Amount : Rs. {self.booking.total_price:.2f}
-------------------------------------------------------
Issued On         : {self.booking.created_at}
=======================================================
"""
            txt_path.write_text(txt_content, encoding="utf-8")

            # 2. Beautiful HTML Export
            seats_badges_html = "".join(
                f'<span style="background:#F84464;color:#FFF;padding:4px 10px;border-radius:4px;margin-right:6px;font-weight:bold;">{s}</span>'
                for s in self.booking.seats
            )

            html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>CineBook Pass - {self.booking.booking_ref}</title>
<style>
  body {{
    background: #F2F4F8;
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
    display: flex;
    justify-content: center;
    padding: 40px 20px;
    margin: 0;
  }}
  .ticket {{
    background: #FFFFFF;
    color: #30343B;
    border-radius: 12px;
    max-width: 580px;
    width: 100%;
    border: 1px solid #ECEEF2;
    overflow: hidden;
    box-shadow: 0 10px 30px rgba(0,0,0,0.06);
  }}
  .header {{
    background: #FFFFFF;
    padding: 24px 28px;
    border-bottom: 2px dashed #E5E7EB;
  }}
  .brand {{
    color: #F84464;
    font-size: 20px;
    font-weight: 800;
  }}
  .ref-box {{
    background: #F8F9FA;
    padding: 12px 16px;
    border-radius: 8px;
    margin: 16px 0;
    display: flex;
    justify-content: space-between;
    align-items: center;
  }}
  .content {{
    padding: 24px 28px;
  }}
  .title {{
    font-size: 22px;
    font-weight: bold;
    color: #22242A;
  }}
  .row {{
    display: flex;
    justify-content: space-between;
    margin: 10px 0;
  }}
  .footer {{
    background: #FAFAFC;
    padding: 18px 28px;
    border-top: 1px solid #ECEEF2;
    font-size: 13px;
    color: #828894;
  }}
</style>
</head>
<body>
<div class="ticket">
  <div class="header">
    <div class="brand">🎬 CINEBOOK CINEMAS</div>
    <div style="color: #666; font-size: 13px;">Official Digital Cinema Admission Pass</div>
    <div class="ref-box">
      <span style="font-size: 12px; color: #828894; font-weight: bold;">REFERENCE</span>
      <span style="font-family: monospace; font-size: 18px; color: #F84464; font-weight: bold;">{self.booking.booking_ref}</span>
    </div>
  </div>
  <div class="content">
    <div class="title">{self.booking.movie_title or 'Cinema Experience'}</div>
    <div style="color: #0284C7; font-weight: 600; margin: 4px 0 16px 0;">{self.booking.screen_name or 'Main Screen'}</div>
    <div class="row">
      <div><strong>Date & Time:</strong> {self.booking.show_date} at {self.booking.show_time}</div>
    </div>
    <div class="row">
      <div><strong>Patron:</strong> {self.booking.customer_name} ({self.booking.customer_phone})</div>
    </div>
    <div style="margin: 16px 0 8px 0;"><strong>Seats Reserved:</strong></div>
    <div style="margin-bottom: 20px;">{seats_badges_html}</div>
    <hr style="border: 0; border-top: 1px solid #ECEEF2;">
    <div class="row">
      <span>Ticket Subtotal:</span>
      <span>Rs. {self.booking.subtotal:.2f}</span>
    </div>
    <div class="row">
      <span>Convenience Fee:</span>
      <span>Rs. {self.booking.convenience_fee:.2f}</span>
    </div>
    <div class="row" style="font-size: 18px; font-weight: bold; color: #F84464; margin-top: 12px;">
      <span>Total Paid:</span>
      <span>Rs. {self.booking.total_price:.2f}</span>
    </div>
  </div>
  <div class="footer">
    Notice: Generated by CineBook Smart Booking System.
  </div>
</div>
</body>
</html>
"""
            html_path.write_text(html_content, encoding="utf-8")

            messagebox.showinfo(
                "Ticket Exported Successfully",
                f"Your digital pass has been saved in:\n\n"
                f"• {html_path.name} (Printable Web Ticket)\n"
                f"• {txt_path.name} (Plain Text Summary)\n\n"
                f"Location: exports/"
            )
        except Exception as e:
            messagebox.showerror("Export Failed", f"Could not save ticket files: {e}")
