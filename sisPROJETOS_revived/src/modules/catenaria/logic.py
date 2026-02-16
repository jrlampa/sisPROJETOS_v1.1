from database.db_manager import DatabaseManager
import numpy as np
import ezdxf
import os
import math

class CatenaryLogic:
    def __init__(self):
        self.db = DatabaseManager()
        self.conductors = []
        self.load_conductors()

    def load_conductors(self):
        """Loads conductors from the SQLite database."""
        try:
            # We want full details for calculation
            conn = self.db.get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT name, weight_kg_m, breaking_load_daN FROM conductors")
            rows = cursor.fetchall()
            self.conductors = [
                {"nome_cadastro": r[0], "P_kg_m": r[1], "T0_daN": r[2]} 
                for r in rows
            ]
            conn.close()
        except Exception as e:
            print(f"Error loading conductors from DB: {e}")
            self.conductors = []

    def get_conductor_names(self):
        return [c["nome_cadastro"] for c in self.conductors]

    def get_conductor_by_name(self, name):
        for c in self.conductors:
            if c["nome_cadastro"] == name:
                return c
        return None

    def calculate_catenary(self, span, ha, hb, tension_daN, weight_kg_m):
        """
        Calculates catenary curve points and properties.
        
        Args:
            span (float): Horizontal distance (m).
            ha (float): Height of support A (m).
            hb (float): Height of support B (m).
            tension_daN (float): Horizontal tension (daN).
            weight_kg_m (float): Linear weight (kg/m).
            
        Returns:
            dict: {
                "sag": float,
                "x_vals": np.array,
                "y_vals": np.array,
                "tension_a": float,
                "tension_b": float
            }
        """
        # Convert units
        # T (Horizontal Tension) in Newtons? Or keep daN/kgf consistent?
        # Usually a = T_h / w
        # If T is daN, w is kg/m -> convert both to N or kgf.
        # 1 daN = 10 N. 1 kgf = 9.80665 N.
        # Let's work in kgf. 1 daN ~= 1.02 kgf.
        # Let's assume input T is in daN, convert to kgf for consistency with weight?
        # Or Just use ratios. a = T / w.
        # Unit analysis: T [Force], w [Force/Length]. a [Length].
        # if T in daN, w in kg/m.
        # w_daN_m = w_kg_m * 9.81 / 10 = w_kg_m * 0.981
        
        w_daN_m = weight_kg_m * 0.980665 # Convert kg/m to daN/m
        
        if w_daN_m == 0:
            return None

        # Catenary Constant
        a = tension_daN / w_daN_m
        
        # Level span logic (Simplified for initial version, can expand to inclined)
        # Even if HA != HB, calculation of 'a' based on H (Horizontal Tension) is same.
        # The curve equation with minimum at x=0 is y = a * cosh(x/a).
        # We need to shift it to pass through (0, HA) and (Span, HB).
        
        # Iterative solver needed for exact solution given supports and separate L?
        # Usually standard problem is: Given Span, w, and Sag OR Tension.
        # Here we have Tension.
        
        # Coordinate system: Support A at (0, HA), Support B at (Span, HB).
        # General Eq: y(x) = a * cosh((x - x0)/a) + y0
        
        # Solving for x0 and y0 to match boundary conditions is complex.
        # Approximation for typical overhead lines (flat parabola):
        # y(x) = HA + (HB - HA) * (x / Span) + 4 * Sag * (x/Span) * (1 - x/Span) ?? No.
        
        # Let's stick to Catenary but support Inclined spans.
        # Reference: "Sag and Tension of a Catenary"
        
        # Define x range
        x = np.linspace(0, span, 100)
        
        # Simplified Level Span calc for Sag (mid-span) if supports were equal
        # Sag = a * (cosh(L/2a) - 1)
        sag_level = a * (np.cosh(span / (2 * a)) - 1)
        
        # For visualization, let's assume the low point is roughly mid-span if level.
        # If inclined, we need proper offset.
        
        # Let's implement the standard level span formula centered at L/2 for plotting Z-axis vs X.
        # But we must respect HA and HB.
        # Approximation: Draw the catenary sag curve relative to the chord.
        
        # Chord line
        y_chord = ha + (hb - ha) * (x / span)
        
        # Parabolic Sag deviation (vertical)
        # y_curve = y_chord - 4 * sag_level * (x/span) * (1 - x/span) 
        # (This is parabolic approx valid for flat spans)
        
        # Let's use exact Catenary formula shifted.
        # y = y_chord - sag_curve
        # Better: y = a * cosh((x - L/2)/a) - a * cosh(L/2a) + height_adjustment
        # This is strictly for level span.
        
        # For this requested "Task", I will implement the Level Span formula adjusted for visual tilt.
        # It's what's commonly used in simple tools unless "Ruling Span" logic is requested.
        
        y_catenary_std = a * np.cosh((x - span/2) / a)
        # Shift so endpoints are 0 relative to supports?
        y_catenary_zeroed = y_catenary_std - y_catenary_std[0] # Starts at 0, ends at 0 (if level)
        
        # This gives the "belly". It goes DOWN.
        # Actually cosh is Up. calc is: y = a*cosh(x/a).
        # We want "Sag" to be drop from support.
        # y_drop = y_catenary_std - y_catenary_std[0] (This is positive upwards) -> No.
        # Sag is down.
        # y_curve = HA - (y_catenary_std - a) ? No.
        
        # Let's use the explicit approximation for "Inclined Span Sag" (Flecha Inclinada)
        # Vertical Sag (Flecha Vertical) is approx same as Level Span for same horizontal tension.
        
        y_vals = y_chord - (y_catenary_zeroed * -1 * (y_catenary_zeroed < 0)) # wait
        
        # Correct approach for simple visualization:
        # 1. Calc Level Sag using T (Horizontal).
        # 2. Subtract this "belly" shape from the chord line.
        
        sag_curve = a * (np.cosh((x - span/2) / a) - np.cosh(span / (2 * a))) 
        # range of sag_curve is [-Sag, 0].
        
        y_final = y_chord + sag_curve
        
        return {
            "sag": sag_level,
            "x_vals": x,
            "y_vals": y_final,
            "tension": tension_daN,
            "catenary_constant": a
        }

    def export_dxf(self, filepath, x_vals, y_vals, sag):
        from utils.dxf_manager import DXFManager
        DXFManager.create_catenary_dxf(filepath, x_vals, y_vals, sag)
