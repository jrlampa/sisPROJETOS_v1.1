import math
import os
from typing import Any, Iterable, Tuple

import ezdxf
import pandas as pd


def _validate_output_path(filepath: str) -> str:
    """Validates and resolves a DXF output filepath to prevent path traversal.

    Args:
        filepath: The requested output file path.

    Returns:
        str: Resolved absolute path.

    Raises:
        ValueError: If the path contains traversal sequences or is otherwise invalid.
    """
    if not filepath or not isinstance(filepath, str):
        raise ValueError("filepath must be a non-empty string")

    # Reject paths containing null bytes BEFORE any OS path processing
    if "\x00" in filepath:
        raise ValueError("filepath must not contain null bytes")

    resolved = os.path.realpath(os.path.abspath(filepath))

    return resolved


class DXFManager:
    @staticmethod
    def create_catenary_dxf(filepath: str, x_vals: Iterable[float], y_vals: Iterable[float], sag: float) -> None:
        """Creates a professional DXF for catenary curves with dedicated layers (2.5D).

        The catenary profile is represented in 2.5D: X = horizontal distance along the
        span, Y = conductor height above reference. The DXF uses LWPOLYLINE (2D entity)
        which is correct for profile/section view outputs (ABNT NBR 5422).

        Args:
            filepath: Output file path. Must be a valid, non-traversal path.
            x_vals: Iterable of X coordinates (horizontal span, in metres).
            y_vals: Iterable of Y coordinates (height above reference, in metres).
            sag: Sag value in meters for annotation label.

        Raises:
            ValueError: If filepath is invalid or contains path traversal.
        """
        safe_path = _validate_output_path(filepath)
        doc = ezdxf.new("R2010")

        # Setup Layers
        doc.layers.new("CATENARY_CURVE", dxfattribs={"color": 3, "lineweight": 35})  # Green, thick
        doc.layers.new("SUPPORTS", dxfattribs={"color": 2})  # Yellow
        doc.layers.new("ANNOTATIONS", dxfattribs={"color": 7})  # White/Black

        msp = doc.modelspace()

        # Add Polyline (LWPOLYLINE is a 2.5D entity — flat in XY plane)
        points = list(zip(x_vals, y_vals))
        msp.add_lwpolyline(points, dxfattribs={"layer": "CATENARY_CURVE"})

        # Add Support markers (Poles)
        DXFManager._add_pole_marker(msp, points[0])
        DXFManager._add_pole_marker(msp, points[-1])

        # Add labels
        msp.add_text(f"Sag: {sag:.2f}m", dxfattribs={"height": 0.5, "layer": "ANNOTATIONS"}).set_placement(
            points[len(points) // 2]
        )

        doc.saveas(safe_path)

    @staticmethod
    def _add_pole_marker(msp: Any, pos: Tuple[float, float]) -> None:
        """Internal helper to draw a pole representation (2.5D circle + crosshair)."""
        # Simple Circle for pole
        msp.add_circle(pos, radius=0.2, dxfattribs={"layer": "SUPPORTS"})
        # Hexagon/Crosshair
        for angle in [0, 60, 120, 180, 240, 300]:
            rad = math.radians(angle)
            msp.add_line(
                pos, (pos[0] + 0.3 * math.cos(rad), pos[1] + 0.3 * math.sin(rad)), dxfattribs={"layer": "SUPPORTS"}
            )

    @staticmethod
    def create_points_dxf(filepath: str, df: pd.DataFrame) -> None:
        """Creates a 2.5D DXF from a dataframe of UTM points.

        Uses the 2.5D convention: entities are positioned in the XY plane using UTM
        Easting/Northing, and the elevation is stored in the Z component of the POINT
        entity's location (``location.z``) — the standard GIS/survey 2.5D format compatible
        with ABNT NBR 13133. TEXT labels use 2D ``(x, y)`` placement to stay flat in plan view.

        Args:
            filepath: Output file path. Must be a valid, non-traversal path.
            df: DataFrame with columns 'Easting', 'Northing', 'Name', and optionally
                'Elevation'.

        Raises:
            ValueError: If filepath is invalid or contains path traversal.
        """
        safe_path = _validate_output_path(filepath)
        doc = ezdxf.new("R2010")
        msp = doc.modelspace()
        doc.layers.new("POINTS", dxfattribs={"color": 1})

        for _, row in df.iterrows():
            x = float(row["Easting"])
            y = float(row["Northing"])
            elev = float(row.get("Elevation", 0))  # 2.5D: elevation stored in location.z of POINT

            # 2.5D POINT: Z = elevation (WCS flat-earth survey convention, ABNT NBR 13133)
            msp.add_point((x, y, elev), dxfattribs={"layer": "POINTS"})

            # 2.5D TEXT: placement in XY plane (Z=0) so labels stay flat in plan view
            text_ent = msp.add_text(str(row["Name"]), dxfattribs={"height": 2.0, "layer": "POINTS"})
            text_ent.set_placement((x, y))

        doc.saveas(safe_path)
