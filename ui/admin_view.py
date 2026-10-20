"""
CineBook - Demo Administration & Operations Console (BookMyShow-Style Light Theme)
Management interface for sample cities, demonstration theatres, screen formats,
movie schedules, and ticket pricing tiers (Classic, Elite, Recliner).
"""

from typing import Callable, Dict, List, Optional, Any
import tkinter as tk
from tkinter import ttk, messagebox

from database import DatabaseManager
from models import City, Theatre, Screen, Movie, Show
from ui.theme import (
    BG_PAGE, BG_CARD, BG_INPUT, BORDER_COLOR, BORDER_LIGHT, BORDER_CARD,
    ACCENT_RED, ACCENT_RED_HOVER, ACCENT_RED_LIGHT, ACCENT_CYAN, ACCENT_GOLD,
    COLOR_SUCCESS, COLOR_DANGER, COLOR_WARNING,
    TEXT_PRIMARY, TEXT_SECONDARY, TEXT_MUTED, TEXT_DARK, TEXT_LIGHT,
    TIER_STANDARD, TIER_PREMIUM, TIER_RECLINER,
    FONT_HERO, FONT_TITLE, FONT_SUBTITLE, FONT_CARD_TITLE,
    FONT_BODY, FONT_BODY_BOLD, FONT_SMALL, FONT_SMALL_BOLD, FONT_BADGE
)
from ui.components import ScrollableFrame, ModernButton, StatCard


class AdminView(tk.Frame):
    """Demo Administration & Theatre Schedule/Pricing Console."""

    def __init__(
        self,
        master,
        db: DatabaseManager,
        on_go_home: Callable[[], None],
        **kwargs
    ):
        super().__init__(master, bg=BG_PAGE, **kwargs)
        self.db = db
        self.on_go_home = on_go_home

        self.selected_city_name = "Chennai"
        self.selected_show_id: Optional[int] = None

        self.scroll_container = ScrollableFrame(self, bg=BG_PAGE)
        self.scroll_container.pack(fill="both", expand=True)
        self.content = self.scroll_container.scrollable_content

        # Centered container with generous horizontal margins
        self.main_wrapper = tk.Frame(self.content, bg=BG_PAGE)
        self.main_wrapper.pack(fill="x", padx=48, pady=(16, 36))

        self._build_header()
        self._build_metric_cards()
        self._build_admin_tabs()

    def _build_header(self) -> None:
        """Top banner and navigation."""
        top_bar = tk.Frame(self.main_wrapper, bg=BG_PAGE)
        top_bar.pack(fill="x", pady=(0, 14))

        title_col = tk.Frame(top_bar, bg=BG_PAGE)
        title_col.pack(side="left")

        tk.Label(
            title_col,
            text="🛠 Demo Administration & Operations",
            font=FONT_HERO,
            fg=TEXT_PRIMARY,
            bg=BG_PAGE
        ).pack(anchor="w")

        tk.Label(
            title_col,
            text="Manage sample cinema hierarchy: Cities → Theatres → Screens → Schedules & Tier Pricing.",
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

        # Notice
        notice_box = tk.Frame(
            self.main_wrapper,
            bg="#FFFBEB",
            padx=16,
            pady=8,
            highlightthickness=1,
            highlightbackground="#FCD34D"
        )
        notice_box.pack(fill="x", pady=(0, 16))

        tk.Label(
            notice_box,
            text="ℹ Demonstration Console: Adjust sample ticket tier rates (Classic, Elite, Recliner) or browse sample cinema networks. Changes immediately affect local SQLite inventory.",
            font=FONT_SMALL,
            fg="#92400E",
            bg="#FFFBEB"
        ).pack(anchor="w")

    def _build_metric_cards(self) -> None:
        """Dashboard overview cards."""
        stats = self.db.get_dashboard_stats()

        metrics_frame = tk.Frame(self.main_wrapper, bg=BG_PAGE)
        metrics_frame.pack(fill="x", pady=(0, 20))

        for col_idx in range(5):
            metrics_frame.columnconfigure(col_idx, weight=1)

        cards = [
            ("Indian Movies", str(stats.get("total_movies", 20)), ACCENT_RED),
            ("Active Cities", str(stats.get("total_cities", 5)), ACCENT_CYAN),
            ("Demo Theatres", str(stats.get("total_theatres", 15)), ACCENT_GOLD),
            ("Active Shows", str(stats.get("total_shows", 0)), "#8B5CF6"),
            ("Demo Revenue", f"₹{stats.get('total_revenue', 0.0):,.0f}", COLOR_SUCCESS),
        ]

        for idx, (label, val, color) in enumerate(cards):
            card = StatCard(metrics_frame, label=label, value=val, accent_color=color)
            card.grid(row=0, column=idx, sticky="ew", padx=(0 if idx == 0 else 8, 0 if idx == 4 else 8))

    def _build_admin_tabs(self) -> None:
        """Main administration panels: Theatres Browser and Show Price Adjuster."""
        panels_container = tk.Frame(self.main_wrapper, bg=BG_PAGE)
        panels_container.pack(fill="x")

        # Two columns: Left is Theatres & Screens, Right is Pricing & Schedule Editor
        left_col = tk.Frame(panels_container, bg=BG_PAGE)
        left_col.pack(side="left", fill="both", expand=True, padx=(0, 16))

        right_col = tk.Frame(panels_container, bg=BG_PAGE, width=420)
        right_col.pack(side="right", fill="both", anchor="n")
        right_col.pack_propagate(False)

        self._build_theatres_panel(left_col)
        self._build_price_editor_panel(right_col)

    def _build_theatres_panel(self, parent: tk.Widget) -> None:
        """Theatres and Screens hierarchy treeview."""
        card = tk.Frame(
            parent,
            bg=BG_CARD,
            padx=20,
            pady=18,
            highlightthickness=1,
            highlightbackground=BORDER_CARD
        )
        card.pack(fill="both", expand=True)

        head_row = tk.Frame(card, bg=BG_CARD)
        head_row.pack(fill="x", pady=(0, 12))

        tk.Label(
            head_row,
            text="Theatres & Screen Formats",
            font=FONT_TITLE,
            fg=TEXT_PRIMARY,
            bg=BG_CARD
        ).pack(side="left")

        # City Filter
        city_box = tk.Frame(head_row, bg=BG_CARD)
        city_box.pack(side="right")

        tk.Label(city_box, text="City:", font=FONT_BADGE, fg=TEXT_MUTED, bg=BG_CARD).pack(side="left", padx=(0, 6))

        self.city_combo = ttk.Combobox(city_box, values=["Chennai", "Hyderabad", "Bengaluru", "Mumbai", "Kochi"],
                                       state="readonly", width=14, font=FONT_SMALL)
        self.city_combo.set(self.selected_city_name)
        self.city_combo.pack(side="left")
        self.city_combo.bind("<<ComboboxSelected>>", self._on_admin_city_changed)

        # Treeview for Theatres & Screens
        columns = ("theatre", "location", "screens")
        self.theatre_tree = ttk.Treeview(
            card,
            columns=columns,
            show="headings",
            selectmode="browse",
            height=9
        )
        self.theatre_tree.heading("theatre", text="Theatre Name", anchor="w")
        self.theatre_tree.heading("location", text="Location & Address", anchor="w")
        self.theatre_tree.heading("screens", text="Screens Configured", anchor="center")

        self.theatre_tree.column("theatre", width=200, minwidth=160)
        self.theatre_tree.column("location", width=250, minwidth=200)
        self.theatre_tree.column("screens", width=130, minwidth=100, anchor="center")

        v_scroll = ttk.Scrollbar(card, orient="vertical", command=self.theatre_tree.yview)
        self.theatre_tree.configure(yscrollcommand=v_scroll.set)

        self.theatre_tree.pack(side="left", fill="both", expand=True, pady=(0, 8))
        v_scroll.pack(side="right", fill="y", pady=(0, 8))

        self._refresh_theatres_tree()

    def _on_admin_city_changed(self, event=None) -> None:
        self.selected_city_name = self.city_combo.get()
        self._refresh_theatres_tree()

    def _refresh_theatres_tree(self) -> None:
        """Populate theatres for selected city."""
        for item in self.theatre_tree.get_children():
            self.theatre_tree.delete(item)

        theatres = self.db.get_theatres_by_city(self.selected_city_name)
        for t in theatres:
            screens = self.db.get_screens_by_theatre(t.id)
            scr_names = ", ".join(s.screen_type for s in screens) if screens else "3 Screens"
            loc = f"{t.location}" if t.location else ""
            self.theatre_tree.insert(
                "",
                "end",
                values=(t.name, loc, f"{len(screens)} Screens ({scr_names[:25]}...)")
            )

    def _build_price_editor_panel(self, parent: tk.Widget) -> None:
        """Form to adjust ticket tier prices for any active show schedule."""
        self.editor_card = tk.Frame(
            parent,
            bg=BG_CARD,
            padx=20,
            pady=18,
            highlightthickness=1,
            highlightbackground=BORDER_CARD
        )
        self.editor_card.pack(fill="both", expand=True)

        tk.Label(
            self.editor_card,
            text="Adjust Show Tier Pricing",
            font=FONT_TITLE,
            fg=TEXT_PRIMARY,
            bg=BG_CARD
        ).pack(anchor="w")

        tk.Label(
            self.editor_card,
            text="Select a showtime to update its Classic, Elite, and Recliner ticket rates.",
            font=FONT_SMALL,
            fg=TEXT_MUTED,
            bg=BG_CARD
        ).pack(anchor="w", pady=(2, 14))

        # Show Selector Dropdown
        tk.Label(self.editor_card, text="SELECT ACTIVE SHOW:", font=FONT_BADGE, fg=TEXT_MUTED, bg=BG_CARD).pack(anchor="w")

        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT s.id, s.show_date, s.show_time, s.price_classic, s.price_elite, s.price_recliner,
                       m.title as movie_title, t.name as theatre_name, scr.screen_name
                FROM shows s
                JOIN movies m ON s.movie_id = m.id
                JOIN screens scr ON s.screen_id = scr.id
                JOIN theatres t ON scr.theatre_id = t.id
                ORDER BY s.id DESC LIMIT 40;
            """)
            self.recent_shows = cursor.fetchall()

        self.show_options = {}
        combo_values = []
        for r in self.recent_shows:
            label = f"#{r['id']} {r['movie_title'][:16]} | {r['theatre_name'][:14]} | {r['show_time']}"
            combo_values.append(label)
            self.show_options[label] = r

        self.shows_combo = ttk.Combobox(self.editor_card, values=combo_values, state="readonly", font=FONT_SMALL)
        self.shows_combo.pack(fill="x", pady=(4, 14))
        self.shows_combo.bind("<<ComboboxSelected>>", self._on_show_combo_selected)

        # Price Input Fields
        inputs_frame = tk.Frame(self.editor_card, bg=BG_CARD)
        inputs_frame.pack(fill="x", pady=(0, 16))

        # Classic
        tk.Label(inputs_frame, text="CLASSIC TIER (₹):", font=FONT_BADGE, fg=TIER_STANDARD, bg=BG_CARD).pack(anchor="w")
        self.price_classic_var = tk.StringVar(value="150")
        tk.Entry(inputs_frame, textvariable=self.price_classic_var, font=FONT_BODY, bg="#F8F9FA",
                 relief="flat", highlightthickness=1, highlightbackground=BORDER_CARD).pack(fill="x", pady=(2, 8), ipady=4)

        # Elite
        tk.Label(inputs_frame, text="ELITE TIER (₹):", font=FONT_BADGE, fg=TIER_PREMIUM, bg=BG_CARD).pack(anchor="w")
        self.price_elite_var = tk.StringVar(value="220")
        tk.Entry(inputs_frame, textvariable=self.price_elite_var, font=FONT_BODY, bg="#F8F9FA",
                 relief="flat", highlightthickness=1, highlightbackground=BORDER_CARD).pack(fill="x", pady=(2, 8), ipady=4)

        # Recliner
        tk.Label(inputs_frame, text="RECLINER TIER (₹):", font=FONT_BADGE, fg=TIER_RECLINER, bg=BG_CARD).pack(anchor="w")
        self.price_recliner_var = tk.StringVar(value="300")
        tk.Entry(inputs_frame, textvariable=self.price_recliner_var, font=FONT_BODY, bg="#F8F9FA",
                 relief="flat", highlightthickness=1, highlightbackground=BORDER_CARD).pack(fill="x", pady=(2, 16), ipady=4)

        self.save_price_btn = ModernButton(
            self.editor_card,
            text="💾 Save Updated Rates",
            command=self._handle_save_prices,
            bg=ACCENT_RED,
            hover_bg=ACCENT_RED_HOVER,
            pady=8
        )
        self.save_price_btn.pack(fill="x")

        if combo_values:
            self.shows_combo.set(combo_values[0])
            self._on_show_combo_selected()

    def _on_show_combo_selected(self, event=None) -> None:
        selected_label = self.shows_combo.get()
        show_data = self.show_options.get(selected_label)
        if show_data:
            self.selected_show_id = show_data["id"]
            self.price_classic_var.set(str(int(show_data["price_classic"])))
            self.price_elite_var.set(str(int(show_data["price_elite"])))
            self.price_recliner_var.set(str(int(show_data["price_recliner"])))

    def _handle_save_prices(self) -> None:
        """Saves new prices to SQLite database."""
        if not self.selected_show_id:
            messagebox.showwarning("Select Show", "Please select a showtime to update.")
            return

        try:
            pc = float(self.price_classic_var.get().strip())
            pe = float(self.price_elite_var.get().strip())
            pr = float(self.price_recliner_var.get().strip())
        except ValueError:
            messagebox.showerror("Invalid Input", "Please enter valid numeric prices.")
            return

        success = self.db.update_show_prices(self.selected_show_id, pc, pe, pr)
        if success:
            messagebox.showinfo(
                "Prices Updated",
                f"Successfully updated Show #{self.selected_show_id} prices:\n"
                f"Classic: ₹{int(pc)}, Elite: ₹{int(pe)}, Recliner: ₹{int(pr)}"
            )
        else:
            messagebox.showerror("Error", "Could not update prices.")
