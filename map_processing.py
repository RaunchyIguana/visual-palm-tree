import pandas as pd
import geopandas as gpd
import os
from os.path import join as jj
import shutil
gpd.io.file.fiona.drvsupport.supported_drivers['KML'] = 'rw'

######################
## Plan Map Styling ##
######################

source_zones = gpd.read_file("SourceFiles/Brewery Zones and Points - Leaflet Planning Version.kml", layer = 'Zones', driver = 'KML')
points = gpd.read_file("SourceFiles/Brewery Zones and Points - Leaflet Planning Version.kml", layer = 'POIs', driver = 'KML')

parks = gpd.read_file('SourceFiles/parks')
library = gpd.read_file("SourceFiles/Libraries.kml", driver = 'KML')

source_zones.rename(columns = {'Name' : 'Zone'}, inplace = True)
source_zones.drop(columns = ['Description'], inplace = True)
points.rename(columns = {'Name' : 'POI'}, inplace = True)
points.drop(columns = ['Description'], inplace = True)

source_pz = points.sjoin(source_zones, how = 'left', predicate = 'within')
source_pz.drop(columns = ['index_right'], inplace = True)

index_list = []

def fp_maker(filepath):
    if not os.path.exists(filepath):
        os.mkdir(filepath)

def js_var(filename, var_name):
    with open(filename, 'r', encoding='utf-8') as file:
        data = file.readlines()

        data[0] = 'var {0} = {1}\n'.format(var_name, '{')

        with open(filename, 'w', encoding='utf-8') as file:
            file.writelines(data)

def file_writer(in_folder, out_folder, files):
    for file in files:
        shutil.copyfile(jj(in_folder, file), jj(out_folder, file))

def file_maker(query = None):
    if query:
        pz = source_pz.query('Zone == @query').copy()
        zones = source_zones.query('Zone == @query').copy()
    else:
        pz = source_pz.copy()
        zones = source_zones.copy()
        query = "Full"

    fp_maker(jj('Maps', query))
    fp_maker(jj('Maps', query, 'Layers'))

    base_path = jj('Maps', query)
    layer_path = jj('Maps', query, 'Layers')

    pz['color'] = pz.Zone.apply(lambda s: s.split(' ')[0].lower())
    pz.to_file(jj(layer_path, 'points.js'), driver = 'GeoJSON')
    zones['color'] = zones.Zone.apply(lambda s: s.split(' ')[0].lower())
    zones.to_file(jj(layer_path, 'zones.js'), driver = 'GeoJSON')
    parks.to_file(jj(layer_path, 'parks.js'), driver = 'GeoJSON')
    library.to_file(jj(layer_path, 'libraries.js'), driver = 'GeoJSON')

    js_var(jj(layer_path, 'points.js'), 'points')
    js_var(jj(layer_path, 'zones.js'), 'zones')
    js_var(jj(layer_path, 'parks.js'), 'parks')
    js_var(jj(layer_path, 'libraries.js'), 'libs')

    #############################
    ## Template Code Injection ##
    #############################

    with open('Templates/map_template.html', 'r', encoding='utf-8') as file:
        data = file.readlines()

    data[8] = '		<script type="text/javascript" src="Layers/points.js"></script>\n'
    data[9] = '		<script type="text/javascript" src="Layers/zones.js"></script>\n'
    data[10] = '		<script type="text/javascript" src="Layers/parks.js"></script>\n'
    data[11] = '		<script type="text/javascript" src="Layers/libraries.js"></script>\n'

    map_path = '{0}/{1}.html'.format(base_path, query)
    with open(map_path, 'w', encoding='utf-8') as file:
        file.writelines(data)

    flist = ['book-stack.svg', 'geolet.js', 'map.css']
    file_writer('Templates', base_path, flist)

    index_list.append((query, map_path))

file_maker()
for zone in source_zones.Zone.unique():
    file_maker(zone)

with open('index.html', 'w') as idx:
    idx_string = '<!DOCTYPE html>\n<head>\n    <meta http-equiv="content-type" content="text/html; charset=UTF-8" />\n</head>\n<body>  <p>Map Links</p>\n'

    for data in index_list:
        name, href = data
        fstring = '    <ul>\n      <li><a href="{0}">{1}</a></li>\n    </ul>\n'.format(href, name)
        idx_string += fstring

    idx_string += '</body'
    idx.writelines(idx_string)
