from tempfile import mkdtemp
from glob import glob
from os.path import join, basename
from shutil import rmtree
import json

from osgeo import gdal

def to_geojson(zipped_shapes):
    try:
        extract_here = mkdtemp()
        zipped_shapes.extractall(extract_here)
        shape_files = glob(join(extract_here, '**', '*.shp'))
        features = []
        json_path = join(extract_here, 'result.geojson')
        options = gdal.VectorTranslateOptions(format="GeoJSON")

        for shape_file in shape_files:
            shape_file_name = basename(shape_file)
            gdal.VectorTranslate(json_path, shape_file, options=options)
        
            with open(json_path, 'r') as jason:
                collection = json.load(jason)
                for feature in collection['features']:
                    feature['properties']['source_file'] = shape_file_name
            features += collection['features']
            
        return {'type': 'FeatureCollection', 'features': features}
    finally:
        rmtree(extract_here)