import io, json
from tempfile import mkdtemp
from glob import glob
from os.path import join, basename
from shutil import rmtree
from osgeo import gdal
from zipfile import ZipFile

from app import settings
from app.utils import resource_utility


def run(file_data, field_database):
    file_bytes = io.BytesIO(file_data)
    zip_file = ZipFile(file_bytes, 'r')
    geojson = __convert_to_geojson(zip_file)
    for feature in geojson['features']:
        feature_properties = feature['properties']
        resource_type = 'Unknown'
        if 'Befunde' in feature_properties['source_file']:
            feature_identifier = settings.ShapefileImporter.FIND_SECTION_ID_TEMPLATE.format(**feature_properties)
            resource_type = 'FeatureSegment'
        else:
            feature_identifier = feature_properties['id']

        resource = {}
        resource['identifier'] = feature_identifier
        
        for source, target in settings.ShapefileImporter.PROPERTY_MAP.items():
            copied_value = feature_properties.get(source, None)
            
            if not copied_value is None:
                resource[target] = copied_value
        resource['geometry'] = feature['geometry']
        print(field_database.populate_resource(resource_utility.inflate(resource), resource_type).content)

def __convert_to_geojson(zipped_shapes):
    try:
        extract_here = mkdtemp()
        zipped_shapes.extractall(extract_here)
        shape_files = glob(join(extract_here, '**', '*.shp'))
        features = []
        json_path = join(extract_here, 'result.geojson')
        options = gdal.VectorTranslateOptions(format='GeoJSON')

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