import ezdxf
import math

class DXFManager:
    @staticmethod
    def create_catenary_dxf(filepath, x_vals, y_vals, sag):
        """Creates a professional DXF for catenary curves with dedicated layers."""
        doc = ezdxf.new('R2010')
        
        # Setup Layers
        doc.layers.new('CATENARY_CURVE', dxfattribs={'color': 3, 'lineweight': 35}) # Green, thick
        doc.layers.new('SUPPORTS', dxfattribs={'color': 2}) # Yellow
        doc.layers.new('ANNOTATIONS', dxfattribs={'color': 7}) # White/Black
        
        msp = doc.modelspace()
        
        # Add Polyline
        points = list(zip(x_vals, y_vals))
        msp.add_lwpolyline(points, dxfattribs={'layer': 'CATENARY_CURVE'})
        
        # Add Support markers (Poles)
        DXFManager._add_pole_marker(msp, points[0])
        DXFManager._add_pole_marker(msp, points[-1])
        
        # Add labels
        msp.add_text(f"Sag: {sag:.2f}m", 
                     dxfattribs={'height': 0.5, 'layer': 'ANNOTATIONS'}).set_pos(points[len(points)//2])
        
        doc.saveas(filepath)

    @staticmethod
    def _add_pole_marker(msp, pos):
        """Internal helper to draw a pole representation."""
        # Simple Circle for pole
        msp.add_circle(pos, radius=0.2, dxfattribs={'layer': 'SUPPORTS'})
        # Hexagon/Crosshair
        for angle in [0, 60, 120, 180, 240, 300]:
            rad = math.radians(angle)
            msp.add_line(pos, (pos[0] + 0.3*math.cos(rad), pos[1] + 0.3*math.sin(rad)), 
                         dxfattribs={'layer': 'SUPPORTS'})

    @staticmethod
    def create_points_dxf(filepath, df):
        """Creates DXF from a dataframe of points (UTM)."""
        doc = ezdxf.new('R2010')
        msp = doc.modelspace()
        doc.layers.new('POINTS', dxfattribs={'color': 1})
        
        for _, row in df.iterrows():
            pos = (row['Easting'], row['Northing'], row.get('Elevation', 0))
            msp.add_point(pos, dxfattribs={'layer': 'POINTS'})
            msp.add_text(str(row['Name']), dxfattribs={'height': 2.0, 'layer': 'POINTS'}).set_pos(pos)
            
        doc.saveas(filepath)
