
import pandas as pd
import arcpy 
from arcgis import GIS
from arcgis.features import GeoAccessor, GeoDaskSeriesAccessor, FeatureLayer
from datetime import date
import shutil
import os
from arcgis.features import FeatureLayerCollection


#repos folder variables
gh_main_folder = 'C:/github/Portfolio_examples'
gh_geospatial_folder = gh_main_folder + '/geospatial_files'

#local folder variables
main_folder = 'C:/github_house_search_local'
csv_folder = main_folder + '/csv'
layers_folder = main_folder + '/layers'
shapefile_folder = main_folder + '/shapefile'
gdb = main_folder + '/house_search.gdb'
scratch_dataset = gdb + '/to_be_deleted'

#setting arcpy environments
arcpy.env.overwriteOutput = True
arcpy.env.workspace = gdb

#user will have to provide these inputs
new_homes_csv = arcpy.GetParameter(0)



#if C:/github_house_search_local does not exist, then the files from the geospatial_files folder will be copied over to create C:/github_house_search_local
if not arcpy.Exists(main_folder):
    arcpy.management.Copy(gh_geospatial_folder, main_folder)

#Takes the csv input to create temp layer of new homes and then to feature class
xy_temp = arcpy.management.MakeXYEventLayer(new_homes_csv, 'LONGITUDE', 'LATITUDE', 'xy_layer_{}'.format(date.today()))
new_homes_fc = arcpy.conversion.FeatureClassToFeatureClass(xy_temp, scratch_dataset, 'new_homes')

#clip new homes feature class to nj geometry
nj = arcpy.management.MakeFeatureLayer(gdb + '/territories/NJ_state', 'NJ')
new_homes_nj = arcpy.analysis.Clip(new_homes_fc, nj, scratch_dataset + '/new_homes_nj')
arcpy.management.Delete(new_homes_fc) # this isnt needed anymore at this point

"""
#export agol floodplain layer to feature class, and reduce number of records in the feature class
sql = "FLD_AR_ID LIKE '34%' And esri_symbology = '1% Annual Chance Flood Hazard'"
arcpy.conversion.ExportFeatures('https://services.arcgis.com/P3ePLMYs2RVChkJx/arcgis/rest/services/USA_Flood_Hazard_Reduced_Set_gdb/FeatureServer/0', gdb + '/Flooding/njfloodplain', where_clause= sql)
"""

#convert floodplain feature class to layer for downstream use
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
trains_fc = gdb + '/transit/nj_trains'
arcpy.analysis.SpatialJoin(new_homes_nj, trains_fc, gdb + '/homes/new_homes_sj_trains', match_option='WITHIN_A_DISTANCE', search_radius= '1.5 kilometers')
arcpy.management.Delete(new_homes_nj) # this isnt needed anymore at this point

#adds(near_station) and calculates a new field (y,n) in the joined homes feature class. This will indicate if the home is near a train station
homes_sj_trains = gdb + '/homes/new_homes_sj_trains'
arcpy.management.AddField(homes_sj_trains, 'near_station', 'Text', field_alias= 'Near Train Station', field_length=1)
arcpy.management.CalculateField(homes_sj_trains, 'near_station',expression= "iif(IsEmpty($feature.muni), 'n', 'y')", expression_type='ARCADE')

#selects homes in the joined homes that are within the 100 year floodplain. 
#Selected homees will have a new field with the text '1% Annual Chance Flood Hazard' 
homes_sj_trains_lyr = arcpy.MakeFeatureLayer_management(homes_sj_trains, "homes_sj_trains_lyr") #needs to be a layer for selection
arcpy.management.SelectLayerByLocation(homes_sj_trains_lyr, overlap_type= 'INTERSECT', select_features= nj_100yr)
arcpy.management.CalculateField(homes_sj_trains_lyr, 'in_floodplain', expression= "return '1% Annual Chance Flood Hazard'", expression_type= "ARCADE", field_type='TEXT')

#selects homes in the joined homes that are NOT within the 100 year floodplain. 
# Selected homees will have a new field with the text 'not in 100 year floodplain'
arcpy.management.SelectLayerByLocation(homes_sj_trains_lyr, overlap_type= 'INTERSECT', select_features= nj_100yr, invert_spatial_relationship= 'INVERT')
arcpy.management.CalculateField(homes_sj_trains_lyr, 'in_floodplain', expression= "return 'not in 100 year floodplain'", expression_type= "ARCADE", field_type='TEXT')
arcpy.SelectLayerByAttribute_management(homes_sj_trains_lyr, 'CLEAR_SELECTION')

#appends today's new homes to local feature class with previous new homes
all_homes = gdb + '/homes/homes_for_sale'
arcpy.management.Append(homes_sj_trains_lyr, all_homes)
arcpy.management.Delete(homes_sj_trains) # this isnt needed anymore at this point


