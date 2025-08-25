
import pandas as pd
import arcpy 
from arcgis import GIS
from arcgis.features import GeoAccessor, GeoDaskSeriesAccessor, FeatureLayer
from datetime import date
import shutil
import os
from arcgis.features import FeatureLayerCollection
import json


#repos folder variables
gh_main_folder = 'C:/github/Portfolio_examples'
gh_geospatial_folder = gh_main_folder + '/geospatial_files'
gh_script_folder = gh_main_folder + '/scripts'

#local folder variables
main_folder = 'C:/github_house_search_local/geospatial_files'
csv_folder = main_folder + '/csv'
json_folder = main_folder + '/json'
layers_folder = main_folder + '/layers'
shapefile_folder = main_folder + '/shapefile'
gdb = main_folder + '/house_search.gdb'
scratch_dataset = gdb + '/to_be_deleted'
db_sde = main_folder + '/db.sde'
postgres_schema = db_sde + '/homes.postgres'
all_homes = postgres_schema + '/homes_for_sale'
new_homes_json = json_folder + '/new_homes_geojson.geojson'

#setting arcpy environments
arcpy.env.overwriteOutput = True
arcpy.env.workspace = gdb

#user will have to provide these inputs
new_homes_csv = arcpy.GetParameter(0)
agol_username = arcpy.GetParameter(1)
agol_password = arcpy.GetParameter(2)
db_user = arcpy.GetParameter(3)
db_pw = arcpy.GetParameter(4)


#if C:/github_house_search_local does not exist, then the files from the geospatial_files folder will be copied over to create C:/github_house_search_local
arcpy.AddMessage('Confirming the local folders exist. If not, then creating them.')
if not arcpy.Exists(main_folder):
    arcpy.management.Copy(gh_main_folder, main_folder)
    arcpy.AddMessage('Created local folders')

#Takes the csv input to create temp layer of new homes and then to feature class
arcpy.AddMessage('creating feature layer and then feature class from homes in csv file')
xy_temp = arcpy.management.MakeXYEventLayer(new_homes_csv, 'LONGITUDE', 'LATITUDE', 'xy_layer_{}'.format(date.today()))
new_homes_fc = arcpy.conversion.FeatureClassToFeatureClass(xy_temp, scratch_dataset, 'new_homes')
new_homes_fc_count = arcpy.GetCount_management(new_homes_fc)
arcpy.AddMessage('{} features were imported from the csv file'.format(new_homes_fc_count))

#clip new homes feature class to nj geometry
arcpy.AddMessage('clipping new homes within nj')
nj = arcpy.management.MakeFeatureLayer(gdb + '/territories/NJ_state', 'NJ')
new_homes_nj = arcpy.analysis.Clip(new_homes_fc, nj, scratch_dataset + '/new_homes_nj')
arcpy.management.Delete(new_homes_fc) # this isnt needed anymore at this point
new_homes_nj_ct = arcpy.GetCount_management(new_homes_nj)
arcpy.AddMessage('{} homes remain in NJ'.format(new_homes_nj_ct))

"""
#export agol floodplain layer to feature class, and reduce number of records in the feature class
sql = "FLD_AR_ID LIKE '34%' And esri_symbology = '1% Annual Chance Flood Hazard'"
arcpy.conversion.ExportFeatures('https://services.arcgis.com/P3ePLMYs2RVChkJx/arcgis/rest/services/USA_Flood_Hazard_Reduced_Set_gdb/FeatureServer/0', gdb + '/Flooding/njfloodplain', where_clause= sql)
"""

#convert floodplain feature class to layer for downstream use
arcpy.AddMessage('creating feature layer from nj floodplain feature class')
nj_100yr_path = gdb + '/Flooding/njfloodplain'
nj_100yr= arcpy.management.MakeFeatureLayer(nj_100yr_path, 'nj_100yr')

"""
#connect to NJ Passenger Rail Stations
item_trains = gis.content.get('4e8764433a5a4eb9a323635b428c6f22')
lyr_trains = search_trains.layers[0]

#converts the trains layer to spatial dataframe and then to feature class
sdf_trains = GeoAccessor.from_layer(lyr_trains)
trains_fc = sdf_trains.spatial.to_featureclass(gdb + '/transit/nj_trains')
"""

#creates new feature class from the spatial join between homes and stations 
arcpy.AddMessage('Doing a spatial join between new homes and trains that are within 1.5 km')
trains_fc = gdb + '/transit/nj_trains'
arcpy.analysis.SpatialJoin(new_homes_nj, trains_fc, gdb + '/homes/new_homes_sj_trains', match_option='WITHIN_A_DISTANCE', search_radius= '1.5 kilometers')
arcpy.management.Delete(new_homes_nj) # this isnt needed anymore at this point

#adds(near_station) field, which indicates if the home is near a train station
arcpy.AddMessage('adding new near_station field and indicating if the homes are near a train station')
homes_sj_trains = gdb + '/homes/new_homes_sj_trains'
arcpy.management.AddField(homes_sj_trains, 'near_station', 'Text', field_alias= 'Near Train Station', field_length=1)
arcpy.management.CalculateField(homes_sj_trains, 'near_station',expression= "iif(IsEmpty($feature.muni), 'n', 'y')", expression_type='ARCADE')

#selects homes in the joined homes that are within the 100 year floodplain. 
#Selected homees will have a new field (in_floodplain) with the text '1% Annual Chance Flood Hazard' 
arcpy.AddMessage('selecting new homes that are in a floodplain and adding a field that indicates they are in a 100 yr floodplain')
homes_sj_trains_lyr = arcpy.MakeFeatureLayer_management(homes_sj_trains, "homes_sj_trains_lyr") #needs to be a layer for selection
arcpy.management.SelectLayerByLocation(homes_sj_trains_lyr, overlap_type= 'INTERSECT', select_features= nj_100yr)
arcpy.management.CalculateField(homes_sj_trains_lyr, 'in_floodplain', expression= "return '1% Annual Chance Flood Hazard'", expression_type= "ARCADE", field_type='TEXT')

#selects homes in the joined homes that are NOT within the 100 year floodplain. 
# Selected homees will the text 'not in 100 year floodplain' in the in_floodplain field
arcpy.AddMessage('Selecting new homes not working 100 yr floodplain and adding a field that indicates they are not in 100 yr floodplain')
arcpy.management.SelectLayerByLocation(homes_sj_trains_lyr, overlap_type= 'INTERSECT', select_features= nj_100yr, invert_spatial_relationship= 'INVERT')
arcpy.management.CalculateField(homes_sj_trains_lyr, 'in_floodplain', expression= "return 'not in 100 year floodplain'", expression_type= "ARCADE", field_type='TEXT')
arcpy.SelectLayerByAttribute_management(homes_sj_trains_lyr, 'CLEAR_SELECTION')

#creates database connection
arcpy.AddMessage('Connecting to enterprise database')
arcpy.management.CreateDatabaseConnection(main_folder,'db','POSTGRESQL', 'localhost,5433', 'DATABASE_AUTH',db_user, db_pw, 'DO_NOT_SAVE_USERNAME', 'homes')

#appends data from layer to the homes_for_sale feature class in the database
homes_sj_trains_ct = arcpy.GetCount_management(homes_sj_trains_lyr)
arcpy.AddMessage('Appending {} new home features to homes_for_sale feature class'.format(homes_sj_trains_ct))
arcpy.management.Append(homes_sj_trains_lyr, all_homes, schema_type= 'NO_TEST')

#selects records in all_homes fc that satify my criteria
arcpy.AddMessage('Selecting homes_for_sale features that are not in the 100 yr floodplain, is near a station, has 2 beds, and less than 450,000')
sql = "in_floodplain = 'not in 100 year floodplain' And near_station = 'y' And BEDS >= 2 And PRICE < 450000"
select_homes = arcpy.management.SelectLayerByAttribute(all_homes, 'NEW_SELECTION', sql)
select_homes_ct = arcpy.GetCount_management(select_homes)
arcpy.AddMessage('{} homes were selected and will be exported to AGOL'.format(select_homes_ct))

#converts select_homes layer to geojson
arcpy.AddMessage('Converting selected homes to geojson file')
arcpy.conversion.FeaturesToJSON(select_homes, new_homes_json , geoJSON="GEOJSON")

#connects to AGOL
arcpy.AddMessage('connecting to portal')
gis = GIS(url="https://wwww.arcgis.com", username=agol_username, password=agol_password)

#connects to the new homes layer
arcpy.AddMessage('connecting to new homes hosted feature layer')
new_homes_collection= gis.content.get('ae635057e4e0498fba022ed6cb50d8b3')
new_homes_layer = new_homes_collection.layers[0].container

#overwrite the new homes hosted feature layer with the contents of the geojson file
arcpy.AddMessage('overwriting new homes hosted feature layer with {} features from geojson file'.format(select_homes_ct))
new_homes_layer.manager.overwrite(new_homes_json)

#connects to the homes for sale hosted feature layer
arcpy.AddMessage('connecting to homes for sale hosted feature layer')
homes_for_sale_collection = gis.content.get('7acd4bbc02a843b785760776bbebb8e3')
homes_for_sale_layer = homes_for_sale_collection.layers[0]

#truncates the homes for sale hosted fature layer
arcpy.AddMessage('truncating homes for sale hosted feature layer')
homes_for_sale_layer.manager.truncate()
homes_for_sale_layer_ct = homes_for_sale_layer.query(return_count_only = True)
arcpy.AddMessage('The homes for sale hosted feature layer has {} features'.format(homes_for_sale_layer_ct))

#appends the data from the new homes hosted feature layer to the homes for sale hosted feature layer in AGOL
arcpy.AddMessage('appending {} features from new homes hosted feature layer to homes for sale hosted feature layer'.format(select_homes_ct))
homes_for_sale_layer.append(item_id ='ae635057e4e0498fba022ed6cb50d8b3', upload_format = 'featureService')
homes_for_sale_layer_ct = homes_for_sale_layer.query(return_count_only = True)
arcpy.AddMessage('The homes for sale hosted feature layer now has {} features'.format(homes_for_sale_layer_ct))

arcpy.AddMessage('deleting an old feature class')
arcpy.management.Delete(homes_sj_trains) # this isnt needed anymore at this point


