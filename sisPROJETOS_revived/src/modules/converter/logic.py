import zipfile
import pandas as pd
import ezdxf
from pyproj import CRS, Transformer
from fastkml import kml


class ConverterLogic:
    """Lógica para conversão de arquivos KMZ/KML para coordenadas UTM.
    
    Converte placemarks do Google Earth (KMZ/KML) para coordenadas UTM
    e exporta para Excel (XLSX) ou AutoCAD (DXF).
    """
    
    def __init__(self):
        """Inicializa o conversor de coordenadas."""
        pass

    def load_file(self, filepath):
        """Loads KMZ or KML file and returns features."""
        if filepath.lower().endswith('.kmz'):
            with zipfile.ZipFile(filepath, 'r') as zf:
                # Find the KML file inside
                kml_file = [f for f in zf.namelist() if f.endswith('.kml')][0]
                content = zf.read(kml_file)
        else:
            with open(filepath, 'rb') as f:
                content = f.read()
        
        k = kml.KML()
        k.from_string(content)
        features = list(k.features)
        return self._extract_placemarks(features)

    def _extract_placemarks(self, features, placemarks=None):
        if placemarks is None:
            placemarks = []
        
        for feature in features:
            if isinstance(feature, kml.Document) or isinstance(feature, kml.Folder):
                self._extract_placemarks(list(feature.features), placemarks)
            elif isinstance(feature, kml.Placemark):
                placemarks.append(feature)
        
        return placemarks

    def convert_to_utm(self, placemarks):
        """Converts placemarks to a DataFrame with UTM coordinates."""
        data = []
        
        # Determine UTM zone from the first point (simplification)
        # Ideally should check each point or let user define
        # Using WGS84
        
        for p in placemarks:
            if hasattr(p.geometry, 'coords'): # LineString or Polygon
                 coords = list(p.geometry.coords)
            elif hasattr(p.geometry, 'x'): # Point
                 coords = [(p.geometry.x, p.geometry.y, p.geometry.z if p.geometry.has_z else 0)]
            else:
                continue

            # Auto-detect zone for the first point
            lon, lat = coords[0][0], coords[0][1]
            utm_zone = int((lon + 180) / 6) + 1
            is_southern = lat < 0
            res_crs = CRS.from_dict({
                'proj': 'utm',
                'zone': utm_zone,
                'south': is_southern,
                'ellps': 'WGS84'
            })
            
            transformer = Transformer.from_crs("EPSG:4326", res_crs, always_xy=True)

            for lon, lat, *z in coords:
                easting, northing = transformer.transform(lon, lat)
                elev = z[0] if z else 0
                data.append({
                    'Name': p.name,
                    'Description': p.description,
                    'Type': p.geometry.geom_type,
                    'Longitude': lon,
                    'Latitude': lat,
                    'Easting': easting,
                    'Northing': northing,
                    'Zone': utm_zone,
                    'Hemisphere': 'S' if is_southern else 'N',
                    'Elevation': elev
                })
                
        return pd.DataFrame(data)

    def save_to_excel(self, df, filepath):
        df.to_excel(filepath, index=False)

    def save_to_dxf(self, df, filepath):
        doc = ezdxf.new('R2010')
        msp = doc.modelspace()
        
        grouped = df.groupby('Name')
        
        for name, group in grouped:
            if len(group) == 1:
                # Point
                row = group.iloc[0]
                msp.add_point((row['Easting'], row['Northing'], row['Elevation']), dxfattribs={'layer': 'POINTS'})
                msp.add_text(name, dxfattribs={'height': 2.0}).set_pos((row['Easting'], row['Northing'], row['Elevation']))
            else:
                # Line/Polyline
                points = list(zip(group['Easting'], group['Northing'], group['Elevation']))
                msp.add_polyline3d(points, dxfattribs={'layer': 'LINES'})
                msp.add_text(name, dxfattribs={'height': 2.0}).set_pos(points[0])
                
        doc.saveas(filepath)
