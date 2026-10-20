"""
CineBook Theme & Styling Tokens
BookMyShow-style clean, light cinema discovery aesthetic:
Light grey page background (#F2F4F8), white cards, dark charcoal text (#30343B),
muted grey secondary text, and iconic coral-red (#F84464) booking accents.
"""

import tkinter as tk
from tkinter import ttk

# ==============================================================================
# COLOR PALETTE TOKENS (BookMyShow Light Theme)
# ==============================================================================
# Backgrounds
BG_PAGE = "#F2F4F8"          # Main page background: light grey
BG_DARK = "#F2F4F8"          # Backward compatibility alias for main background
BG_SIDEBAR = "#FFFFFF"       # Top header / sidebar background: crisp clean white
BG_CARD = "#FFFFFF"          # Card background: pure white
BG_CARD_HOVER = "#F9FAFB"    # Subtle hover on cards
BG_INPUT = "#FFFFFF"         # Input background
BG_INPUT_MUTED = "#F1F3F6"   # Search / pill background
BG_INPUT_FOCUS = "#FFFFFF"   # Active input background

# Borders & Separators
BORDER_COLOR = "#E5E7EB"     # Soft grey border
BORDER_LIGHT = "#CBD5E1"     # Light slate border
BORDER_CARD = "#ECEEF2"      # Card subtle outline
BORDER_ACCENT = "#F84464"    # Coral red active border

# Brand & Accent Colors (BookMyShow Iconic Coral-Red)
ACCENT_RED = "#F84464"        # Primary BookMyShow coral red
ACCENT_RED_HOVER = "#D83552"  # Hover state for primary buttons
ACCENT_RED_LIGHT = "#FFF0F2"  # Soft pink-red for active tags/chips
ACCENT_VIOLET = "#F84464"     # Backward compatibility alias mapped to accent red
ACCENT_VIOLET_HOVER = "#D83552"
ACCENT_CYAN = "#0284C7"       # Clean link blue
ACCENT_CYAN_HOVER = "#0369A1"
ACCENT_GOLD = "#F5A623"       # Amber gold for movie rating stars
ACCENT_GOLD_LIGHT = "#FEF3C7"

# Semantic Status Colors
COLOR_SUCCESS = "#10B981"    # Emerald green
COLOR_DANGER = "#EF4444"     # Crimson red
COLOR_WARNING = "#F59E0B"    # Amber warning
COLOR_INFO = "#0284C7"       # Ocean blue info


# Text Shades
TEXT_PRIMARY = "#30343B"     # Dark charcoal main text
TEXT_SECONDARY = "#666666"   # Muted grey secondary text
TEXT_MUTED = "#828894"       # Subtle grey captions & metadata
TEXT_DARK = "#22242A"        # Pitch charcoal
TEXT_LIGHT = "#FFFFFF"       # Crisp white for buttons and badges

# Seat State Colors
SEAT_AVAILABLE_BORDER = "#0EA5E9"
SEAT_AVAILABLE_BG = "#FFFFFF"
SEAT_SELECTED_BG = "#10B981"         # Emerald Green for selected seats
SEAT_SELECTED_BORDER = "#059669"     # Deep emerald green border
SEAT_BOOKED_BG = "#E2E8F0"
SEAT_BOOKED_BORDER = "#CBD5E1"

# Tier Accent Colors
TIER_RECLINER = "#E5A00D"    # Amber Gold
TIER_PREMIUM = "#0284C7"     # Electric Blue
TIER_STANDARD = "#10B981"    # Emerald Green

# ==============================================================================
# TYPOGRAPHY (Clear, High-Contrast, Scalable Hierarchy)
# ==============================================================================
FONT_FAMILY = "Segoe UI"
FONT_FAMILY_FALLBACK = "Helvetica"

FONT_HERO = (FONT_FAMILY, 20, "bold")          # Page heroes & main banners
FONT_TITLE = (FONT_FAMILY, 16, "bold")         # Section headings (15–18 pt)
FONT_SUBTITLE = (FONT_FAMILY, 13, "bold")      # Sub-headings & group titles
FONT_CARD_TITLE = (FONT_FAMILY, 12, "bold")    # Card headers
FONT_BTN = (FONT_FAMILY, 11, "bold")           # Important action buttons (11–12 pt)
FONT_BODY = (FONT_FAMILY, 11, "normal")        # Default body text (10–11 pt)
FONT_BODY_BOLD = (FONT_FAMILY, 11, "bold")     # Emphasized body text
FONT_SMALL = (FONT_FAMILY, 10, "normal")       # Metadata and secondary info
FONT_SMALL_BOLD = (FONT_FAMILY, 10, "bold")    # Labels & tags
FONT_BADGE = (FONT_FAMILY, 9, "bold")          # Micro badges and seat labels
FONT_TABLE = (FONT_FAMILY, 10, "normal")       # Table cells
FONT_TABLE_BOLD = (FONT_FAMILY, 10, "bold")    # Table bold cells
FONT_TABLE_HEAD = (FONT_FAMILY, 11, "bold")    # Table column headers
FONT_MONO = ("Consolas", 10, "normal")
FONT_MONO_BOLD = ("Consolas", 11, "bold")


# ==============================================================================
# RESPONSIVE LAYOUT & GEOMETRY TOKENS (Phase 2 Specifications)
# ==============================================================================
NAV_HEIGHT = 58                   # Main navigation bar height (52-60 px)
SUB_NAV_HEIGHT = 36               # Secondary category sub-navigation (34-40 px)
MAX_CONTENT_WIDTH = 1920          # Expand across full desktop displays
PAD_DESKTOP = 28                  # Desktop horizontal side padding (24-40 px)
PAD_TABLET = 18                   # Tablet horizontal side padding (12-20 px)
PAD_COMPACT = 12                  # Compact-window side padding
SECTION_SPACING = 28              # Vertical spacing between major sections (24-32 px)
CARD_GAP_DEFAULT = 16             # Inter-card horizontal gap (14-18 px)
CARD_WIDTH_MIN = 260              # Minimum readable movie card width
CARD_WIDTH_MAX = 420              # Allow cards to expand proportionally across wide displays
CARD_ASPECT_RATIO = 1.45          # 2:3 portrait aspect ratio (poster_h = card_w * 1.45)
BUTTON_HEIGHT = 48                # Booking button height (44-48 px)
BANNER_HEIGHT = 200               # Stream promotional banner height (200 px)


# ==============================================================================
# TTK STYLING CONFIGURATION
# ==============================================================================
def apply_theme(root: tk.Tk) -> None:
    """Configures ttk styles for treeviews, scrollbars, comboboxes, and tabs for clean light theme."""
    style = ttk.Style(root)

    available_themes = style.theme_names()
    if "clam" in available_themes:
        style.theme_use("clam")

    # Configure General Frame & Label
    style.configure("TFrame", background=BG_PAGE)
    style.configure("Card.TFrame", background=BG_CARD)
    style.configure("Sidebar.TFrame", background=BG_SIDEBAR)
    style.configure("TLabel", background=BG_PAGE, foreground=TEXT_PRIMARY, font=FONT_BODY)

    # Treeview (Bookings History Table)
    style.configure(
        "Treeview",
        background=BG_CARD,
        foreground=TEXT_PRIMARY,
        fieldbackground=BG_CARD,
        rowheight=42,
        font=FONT_TABLE,
        borderwidth=1,
        relief="solid"
    )
    style.configure(
        "Treeview.Heading",
        background="#F8F9FA",
        foreground=TEXT_PRIMARY,
        font=FONT_TABLE_HEAD,
        relief="flat",
        padding=(10, 10)
    )
    style.map(
        "Treeview.Heading",
        background=[("active", "#E5E7EB"), ("pressed", ACCENT_RED_LIGHT)],
        foreground=[("active", ACCENT_RED)]
    )
    style.map(
        "Treeview",
        background=[("selected", ACCENT_RED_LIGHT)],
        foreground=[("selected", ACCENT_RED)]
    )

    # Vertical & Horizontal Scrollbars (sleek minimalist)
    style.configure(
        "Vertical.TScrollbar",
        background="#CBD5E1",
        troughcolor=BG_PAGE,
        bordercolor=BG_PAGE,
        arrowcolor=TEXT_MUTED,
        relief="flat"
    )
    style.configure(
        "Horizontal.TScrollbar",
        background="#CBD5E1",
        troughcolor=BG_PAGE,
        bordercolor=BG_PAGE,
        arrowcolor=TEXT_MUTED,
        relief="flat"
    )
    style.map(
        "Vertical.TScrollbar",
        background=[("active", "#94A3B8"), ("pressed", ACCENT_RED)]
    )
    style.map(
        "Horizontal.TScrollbar",
        background=[("active", "#94A3B8"), ("pressed", ACCENT_RED)]
    )


    # Combobox
    style.configure(
        "TCombobox",
        fieldbackground=BG_INPUT,
        background=BG_INPUT,
        foreground=TEXT_PRIMARY,
        arrowcolor=ACCENT_RED,
        padding=6,
        relief="flat"
    )
    style.map(
        "TCombobox",
        fieldbackground=[("readonly", BG_INPUT)],
        selectbackground=[("readonly", ACCENT_RED_LIGHT)],
        selectforeground=[("readonly", ACCENT_RED)]
    )
