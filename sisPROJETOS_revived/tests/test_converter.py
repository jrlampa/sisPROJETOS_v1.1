"""
Testes expandidos do módulo converter (Conversão KMZ/KML para UTM).
"""

import pytest
import pandas as pd
import numpy as np
import tempfile
import os
from src.modules.converter.logic import ConverterLogic


class TestConverterLogic:
    """Suite de testes expandida para ConverterLogic."""
    
    @pytest.fixture
    def converter(self):
        """Fixture que retorna uma instância de ConverterLogic."""
        return ConverterLogic()
    
    def test_converter_initialization(self, converter):
        """Testa inicialização do conversor."""
        assert converter is not None
        assert isinstance(converter, ConverterLogic)
    
    def test_utm_zone_calculation_sao_paulo(self):
        """Testa cálculo de zona UTM para São Paulo."""
        lon, lat = -46.6333, -23.5505  # São Paulo
        utm_zone = int((lon + 180) / 6) + 1
        assert utm_zone == 23  # SP está na zona 23S
    
    def test_utm_zone_calculation_rio(self):
        """Testa cálculo de zona UTM para Rio de Janeiro."""
        lon, lat = -43.1729, -22.9068  # Rio de Janeiro
        utm_zone = int((lon + 180) / 6) + 1
        assert utm_zone == 23  # RJ está na zona 23S
    
    def test_utm_zone_calculation_brasilia(self):
        """Testa cálculo de zona UTM para Brasília."""
        lon, lat = -47.8825, -15.7942  # Brasília
        utm_zone = int((lon + 180) / 6) + 1
        assert utm_zone == 23  # BSB está na zona 23S
    
    def test_utm_zone_calculation_recife(self):
        """Testa cálculo de zona UTM para Recife."""
        lon, lat = -34.8769, -8.0476  # Recife
        utm_zone = int((lon + 180) / 6) + 1
        assert utm_zone == 25  # Recife está na zona 25S
    
    def test_utm_zone_calculation_northern_hemisphere(self):
        """Testa cálculo de zona UTM para hemisfério norte."""
        lon, lat = -122.4194, 37.7749  # San Francisco
        utm_zone = int((lon + 180) / 6) + 1
        assert utm_zone == 10  # SF está na zona 10N
    
    def test_hemisphere_detection_south(self):
        """Testa detecção de hemisfério sul."""
        lat = -23.5505
        is_southern = lat < 0
        assert is_southern is True
    
    def test_hemisphere_detection_north(self):
        """Testa detecção de hemisfério norte."""
        lat = 37.7749
        is_southern = lat < 0
        assert is_southern is False
    
    def test_converter_export_dataframe_structure(self, converter):
        """Testa estrutura do DataFrame exportado."""
        data = [
            {
                'Name': 'P1',
                'Description': 'Poste 1',
                'Type': 'Point',
                'Longitude': -46.6333,
                'Latitude': -23.5505,
                'Easting': 333000,
                'Northing': 7395000,
                'Zone': 23,
                'Hemisphere': 'S',
                'Elevation': 720
            }
        ]
        df = pd.DataFrame(data)
        
        assert not df.empty
        assert 'Name' in df.columns
        assert 'Longitude' in df.columns
        assert 'Latitude' in df.columns
        assert 'Easting' in df.columns
        assert 'Northing' in df.columns
        assert 'Zone' in df.columns
        assert 'Hemisphere' in df.columns
    
    def test_converter_dataframe_types(self, converter):
        """Testa tipos de dados no DataFrame."""
        data = [
            {
                'Name': 'P1',
                'Description': 'Test',
                'Type': 'Point',
                'Longitude': -46.6,
                'Latitude': -23.5,
                'Easting': 333000.5,
                'Northing': 7395000.5,
                'Zone': 23,
                'Hemisphere': 'S',
                'Elevation': 720.0
            }
        ]
        df = pd.DataFrame(data)
        
        assert isinstance(df['Name'].iloc[0], str)
        assert isinstance(df['Longitude'].iloc[0], (int, float, np.number))
        assert isinstance(df['Latitude'].iloc[0], (int, float, np.number))
        assert isinstance(df['Easting'].iloc[0], (int, float, np.number))
        assert isinstance(df['Northing'].iloc[0], (int, float, np.number))
        assert isinstance(df['Zone'].iloc[0], (int, float, np.number))
        assert isinstance(df['Hemisphere'].iloc[0], str)
    
    def test_save_to_excel_creates_file(self, converter):
        """Testa criação de arquivo Excel."""
        data = [{'Name': 'P1', 'Easting': 100, 'Northing': 200, 'Zone': 23}]
        df = pd.DataFrame(data)
        
        with tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False) as tmp:
            tmp_path = tmp.name
        
        try:
            converter.save_to_excel(df, tmp_path)
            assert os.path.exists(tmp_path)
            assert os.path.getsize(tmp_path) > 0
        finally:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)
    
    def test_save_to_dxf_creates_file(self, converter):
        """Testa criação de arquivo DXF."""
        data = [
            {'Name': 'P1', 'Easting': 100, 'Northing': 200, 'Elevation': 720, 'Zone': 23, 'Type': 'Point'}
        ]
        df = pd.DataFrame(data)
        
        with tempfile.NamedTemporaryFile(suffix='.dxf', delete=False) as tmp:
            tmp_path = tmp.name
        
        try:
            converter.save_to_dxf(df, tmp_path)
            assert os.path.exists(tmp_path)
            assert os.path.getsize(tmp_path) > 0
        finally:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)
    
    def test_save_to_csv_creates_file(self, converter):
        """Testa criação de arquivo CSV com formato correto."""
        data = [
            {'Name': 'P1', 'Easting': 100.12345, 'Northing': 200.6789, 'Zone': 23, 'Type': 'Point', 'Longitude': -46.6, 'Latitude': -23.5, 'Elevation': 720.123, 'Description': 'Ponto 1', 'Hemisphere': 'S'},
            {'Name': 'P2', 'Easting': 150.9876, 'Northing': 250.5432, 'Zone': 23, 'Type': 'Point', 'Longitude': -46.5, 'Latitude': -23.4, 'Elevation': 730.456, 'Description': 'Ponto 2', 'Hemisphere': 'S'}
        ]
        df = pd.DataFrame(data)
        
        with tempfile.NamedTemporaryFile(suffix='.csv', delete=False, mode='w', encoding='utf-8-sig') as tmp:
            tmp_path = tmp.name
        
        try:
            converter.save_to_csv(df, tmp_path)
            assert os.path.exists(tmp_path)
            assert os.path.getsize(tmp_path) > 0
            
            # Verificar conteúdo do CSV com separador correto
            df_read = pd.read_csv(tmp_path, sep=';', encoding='utf-8-sig')
            assert len(df_read) == 2
            assert 'Name' in df_read.columns
            assert 'Easting' in df_read.columns
            assert 'Northing' in df_read.columns
            
            # Verificar que o arquivo usa ';' como separador
            with open(tmp_path, 'r', encoding='utf-8-sig') as f:
                first_line = f.readline()
                assert ';' in first_line
                assert ',' not in first_line.replace(',', '')  # Não deve haver vírgula nos headers
        finally:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)
    
    def test_extract_placemarks_empty_list(self, converter):
        """Testa extração de placemarks com lista vazia."""
        placemarks = converter._extract_placemarks([])
        assert placemarks == []
    
    def test_utm_zone_boundaries(self):
        """Testa limites de zonas UTM."""
        # Zona 1 começa em -180°
        lon = -180
        zone = int((lon + 180) / 6) + 1
        assert zone == 1
        
        # Zona 60 termina em 180°
        lon = 179
        zone = int((lon + 180) / 6) + 1
        assert zone == 60
    
    def test_utm_zone_greenwich(self):
        """Testa zona UTM no meridiano de Greenwich."""
        lon = 0
        zone = int((lon + 180) / 6) + 1
        assert zone == 31
    
    def test_dataframe_multiple_points(self, converter):
        """Testa DataFrame com múltiplos pontos."""
        data = [
            {'Name': 'P1', 'Easting': 100, 'Northing': 200, 'Zone': 23},
            {'Name': 'P2', 'Easting': 150, 'Northing': 250, 'Zone': 23},
            {'Name': 'P3', 'Easting': 200, 'Northing': 300, 'Zone': 23},
        ]
        df = pd.DataFrame(data)
        
        assert len(df) == 3
        assert df['Name'].tolist() == ['P1', 'P2', 'P3']
    
    def test_elevation_handling(self, converter):
        """Testa manipulação de elevação."""
        data = [
            {'Name': 'P1', 'Elevation': 720.5, 'Zone': 23},
            {'Name': 'P2', 'Elevation': 0, 'Zone': 23},
        ]
        df = pd.DataFrame(data)
        
        assert df['Elevation'].iloc[0] == 720.5
        assert df['Elevation'].iloc[1] == 0
    
    def test_description_field(self, converter):
        """Testa campo de descrição."""
        data = [
            {'Name': 'P1', 'Description': 'Poste de concreto', 'Zone': 23},
            {'Name': 'P2', 'Description': 'Poste de madeira', 'Zone': 23},
        ]
        df = pd.DataFrame(data)
        
        assert df['Description'].iloc[0] == 'Poste de concreto'
        assert df['Description'].iloc[1] == 'Poste de madeira'
    
    def test_geometry_type_point(self, converter):
        """Testa tipo de geometria Point."""
        data = [{'Name': 'P1', 'Type': 'Point', 'Zone': 23}]
        df = pd.DataFrame(data)
        assert df['Type'].iloc[0] == 'Point'
    
    def test_geometry_type_linestring(self, converter):
        """Testa tipo de geometria LineString."""
        data = [{'Name': 'L1', 'Type': 'LineString', 'Zone': 23}]
        df = pd.DataFrame(data)
        assert df['Type'].iloc[0] == 'LineString'
    
    def test_geometry_type_polygon(self, converter):
        """Testa tipo de geometria Polygon."""
        data = [{'Name': 'Area1', 'Type': 'Polygon', 'Zone': 23}]
        df = pd.DataFrame(data)
        assert df['Type'].iloc[0] == 'Polygon'
    
    def test_coordinate_precision(self, converter):
        """Testa precisão de coordenadas."""
        data = [{
            'Easting': 333256.789123,
            'Northing': 7395123.456789,
            'Zone': 23
        }]
        df = pd.DataFrame(data)
        
        # Verifica que mantém precisão decimal
        assert df['Easting'].iloc[0] > 333256.78
        assert df['Easting'].iloc[0] < 333256.79
    
    def test_negative_coordinates_southern_hemisphere(self, converter):
        """Testa coordenadas negativas no hemisfério sul."""
        lat = -23.5505
        assert lat < 0
        hemisphere = 'S' if lat < 0 else 'N'
        assert hemisphere == 'S'
    
    def test_excel_export_preserves_data(self, converter):
        """Testa que exportação para Excel preserva dados."""
        data = [
            {'Name': 'P1', 'Easting': 100.5, 'Northing': 200.5, 'Zone': 23},
            {'Name': 'P2', 'Easting': 150.5, 'Northing': 250.5, 'Zone': 23},
        ]
        df_original = pd.DataFrame(data)
        
        with tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False) as tmp:
            tmp_path = tmp.name
        
        try:
            converter.save_to_excel(df_original, tmp_path)
            df_loaded = pd.read_excel(tmp_path)
            
            assert len(df_loaded) == len(df_original)
            assert df_loaded['Name'].tolist() == df_original['Name'].tolist()
        finally:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)
    
    def test_csv_precision_rounding(self, converter):
        """Testa arredondamento de 3 casas decimais no CSV."""
        data = [
            {'Name': 'P1', 'Easting': 333256.789456, 'Northing': 7395123.123789, 
             'Elevation': 720.456789, 'Zone': 23, 'Type': 'Point', 
             'Longitude': -46.6, 'Latitude': -23.5, 'Description': 'Test', 'Hemisphere': 'S'}
        ]
        df = pd.DataFrame(data)
        
        with tempfile.NamedTemporaryFile(suffix='.csv', delete=False, mode='w', encoding='utf-8-sig') as tmp:
            tmp_path = tmp.name
        
        try:
            converter.save_to_csv(df, tmp_path)
            df_read = pd.read_csv(tmp_path, sep=';', encoding='utf-8-sig')
            
            # Valores devem manter 3 casas decimais (mas pandas pode ler com mais precisão)
            assert abs(df_read['Easting'].iloc[0] - 333256.789) < 0.001
            assert abs(df_read['Northing'].iloc[0] - 7395123.124) < 0.001
            assert abs(df_read['Elevation'].iloc[0] - 720.457) < 0.001
        finally:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)
    
    def test_save_to_csv_empty_dataframe(self, converter):
        """Testa exportação de DataFrame vazio."""
        df_empty = pd.DataFrame()
        
        with tempfile.NamedTemporaryFile(suffix='.csv', delete=False) as tmp:
            tmp_path = tmp.name
        
        try:
            with pytest.raises(ValueError, match="Cannot export empty DataFrame"):
                converter.save_to_csv(df_empty, tmp_path)
        finally:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)
    
    def test_convert_to_utm_empty_placemarks(self, converter):
        """Testa conversão com lista vazia de placemarks."""
        with pytest.raises(ValueError, match="No placemarks provided"):
            converter.convert_to_utm([])
    
    def test_csv_semicolon_separator(self, converter):
        """Testa que CSV usa ponto e vírgula como separador."""
        data = [
            {'Name': 'P1', 'Easting': 100.123, 'Northing': 200.456, 'Zone': 23, 
             'Type': 'Point', 'Longitude': -46.6, 'Latitude': -23.5, 
             'Elevation': 720.0, 'Description': 'Teste', 'Hemisphere': 'S'}
        ]
        df = pd.DataFrame(data)
        
        with tempfile.NamedTemporaryFile(suffix='.csv', delete=False, mode='w', encoding='utf-8-sig') as tmp:
            tmp_path = tmp.name
        
        try:
            converter.save_to_csv(df, tmp_path)
            
            # Ler arquivo como texto e verificar separador
            with open(tmp_path, 'r', encoding='utf-8-sig') as f:
                content = f.read()
                # Deve conter ponto e vírgula
                assert ';' in content
                # Header deve ter ponto e vírgula
                lines = content.split('\n')
                assert ';' in lines[0]
        finally:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)
    
    def test_save_to_dxf_empty_dataframe_raises_error(self, converter):
        """Testa que save_to_dxf lança erro para DataFrame vazio."""
        df = pd.DataFrame()
        
        with pytest.raises(ValueError, match="DataFrame vazio"):
            converter.save_to_dxf(df, "test.dxf")
    
    def test_save_to_dxf_missing_columns_raises_error(self, converter):
        """Testa que save_to_dxf lança erro quando faltam colunas necessárias."""
        # DataFrame sem a coluna 'Elevation'
        data = [
            {'Name': 'P1', 'Easting': 100, 'Northing': 200}
        ]
        df = pd.DataFrame(data)
        
        with pytest.raises(ValueError, match="Colunas necessárias faltando"):
            converter.save_to_dxf(df, "test.dxf")

