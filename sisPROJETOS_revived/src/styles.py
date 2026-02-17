"""
Design System for sisPROJETOS - Glassmorphism Light
Defines the visual language, colors, and styling tokens for the application.
"""


class DesignSystem:
    # 1. Colors - Glassmorphism Light Palette
    BG_WINDOW = "#ECF0F3"  # Soft gray-blue background

    # Glassy Frames
    FRAME_BG = "#FFFFFF"  # Pure white for contrast
    FRAME_BORDER = "#D1D9E6"  # Soft shadow border
    FRAME_TRANSLUCENT = "#F8FAFC"  # Almost white

    # Accents
    ACCENT_PRIMARY = "#4A90E2"  # Professional blue
    ACCENT_SECONDARY = "#82B1FF"  # Lighter blue
    ACCENT_SUCCESS = "#2ECC71"
    ACCENT_ERROR = "#E74C3C"
    ACCENT_WARNING = "#F1C40F"
    ACCENT_PURPLE = "#A142F4"

    # Text
    TEXT_MAIN = "#2C3E50"  # Deep dark blue-gray
    TEXT_DIM = "#7F8C8D"  # Muted silver
    TEXT_WHITE = "#FFFFFF"

    # 2. Geometry
    RADIUS_LG = 20  # Large corners for "glassy" look
    RADIUS_MD = 12
    BORDER_WIDTH = 2

    # 3. Typography
    FONT_HEAD = ("Roboto", 24, "bold")
    FONT_SUBHEAD = ("Roboto", 18, "bold")
    FONT_BODY = ("Roboto", 14)
    FONT_BUTTON = ("Roboto", 13, "bold")

    # 4. Component Styles (Dictionaries for CTK configurations)
    @classmethod
    def get_frame_style(cls):
        return {
            "fg_color": cls.FRAME_BG,
            "border_width": cls.BORDER_WIDTH,
            "border_color": cls.FRAME_BORDER,
            "corner_radius": cls.RADIUS_LG,
        }

    @classmethod
    def get_button_style(cls, accent="primary"):
        colors = {
            "primary": cls.ACCENT_PRIMARY,
            "secondary": cls.ACCENT_SECONDARY,
            "success": cls.ACCENT_SUCCESS,
            "error": cls.ACCENT_ERROR,
            "purple": cls.ACCENT_PURPLE,
            "gray": cls.TEXT_DIM,
        }
        return {
            "fg_color": colors.get(accent, cls.ACCENT_PRIMARY),
            "hover_color": "#357ABD" if accent == "primary" else None,  # Simplified for now
            "corner_radius": cls.RADIUS_MD,
            "text_color": cls.TEXT_WHITE,
            "font": cls.FONT_BUTTON,
            "border_width": 0,
        }

    @classmethod
    def get_entry_style(cls):
        return {
            "fg_color": "#F0F4F8",
            "border_color": cls.FRAME_BORDER,
            "border_width": 1,
            "corner_radius": 8,
            "text_color": cls.TEXT_MAIN,
        }
