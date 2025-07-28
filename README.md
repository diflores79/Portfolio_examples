# Readme

## About
This is a personal side project. The goal of this geoprocessing tool is to geospatially analyze new homes from [Redfin](https://www.redfin.com/county/1910/NJ/Union-County) to identify newly posted NJ homes that are not within the 100 year floodplain, and has a train station within 1.5 kilometers. There will be 2 exports of the data:

1. All new homes will be appended to a local feature class: `C:/github_house_search_local/geospatial_files/gdb/homes/homes_for_sale`
2. Select homes will be automatically appended to a House Search hosted feature layer in ArcGIS Online (AGOL). New homes that meet this criteria will be appended to the AGOL hosted feature layer:

    - Must not be within the 100 year floodplain
    - Must be within 1.5 km of a train station
    - Must have more than 2 bedrooms
    - The price must be less than $450,000 
    
    The House Search hosted feature layer is displayed in the [House Seach Web Map](https://www.arcgis.com/apps/mapviewer/index.html?webmap=a9f2fa2b4262417f96440b300cdda491).

    ![House Search Web Map](/Documentation/Images/web_map.png)


The script for the geoprocessing tool is [house_search_agol.py](/scripts/house_search_agol.py). Review [Workflow Section](#workflow) to see a high level workflow of the geoprocessing tool


## Data Sources
### New Homes

The new homes data is exported from [Redfin](https://www.redfin.com). To export data from Redfin:
1. Search for homes in Redfin
2. Set the layout of the search results as `Table`
2. Scroll down to the bottom of the table and click `Download All`

The dowloaded csv will be used as an input in the geoprocessing tool.

### 100 Year Floodplain

The 100 year floodplain data was exported from the [USA Flood Hazard Reduced Set gdb](https://services.arcgis.com/P3ePLMYs2RVChkJx/arcgis/rest/services/USA_Flood_Hazard_Reduced_Set_gdb/FeatureServer) feature layer. The query used to select and export floodplain features was:

- FLD_AR_ID LIKE '34%
- And esri_symbology = '1% Annual Chance Flood Hazard'

The results were stored locally as a feature class in `C:\github_house_search_local\house_search.gdb\Flooding\njfloodplain`. This feature class is used to 100 year floodplains in New Jersey.

### NJ Train Stations

The NJ train station data was exported from the [NJ Passenger Rail Stations](https://hub.arcgis.com/datasets/njdca::nj-passenger-rail-stations/about) feature layer. It was converted to a local feature class to easier processing.

## Workflow

Below is a high level diagram of the geoprocessing tool:

![High Level Diagram](/Documentation/High_level_diagram.png)

A summary of the geoprocessing tool:

1. It will convert the dowloaded new homes csv to a new homes layer.
2. It will spatially join the new homes layer with the NJ Trains feature class and a new `near_station` field will be added to the new homes layer:
    - New homes that have NJ Trains attributes appended to them will have "y" in the `new_station` field
    - New homes that do not have NJ Trains attributes appended to them will have "n" in the `new_station` field
3. It will do a spatial intersect between the new homes layer and the 100 year floodplain feature class and create a new `in_floodplain` field:
    - New homes that were selected during the spatial intersect will have "1% Annual Chance Flood Hazard" in the `in_floodplain` field.
    - New homes that were not selected during the spatial intersect will have "not in 100 year floodplain" in the `in_floodplain` field.
4. All new home features will be appended to a local feature class. This feature class will archive all of the processed homes.
5. But new homes that meet this criteria will be exported to a local homes feature class:
   - `in_floodplain` = "not in 100 year floodplain"
   - `near_station` = "y"
   - `Beds` >= 2
   - `Price` < 450000
6. The data in the local homes feature class will be used to overwrite a private new homes hosted feature layer in AGOL.
7. The data from the private new homes hosted feature layer will be appended to the [house search hosted feature layer](https://www.arcgis.com/home/item.html?id=7acd4bbc02a843b785760776bbebb8e3). 

The results of the geoprocessing tool can be displayed in the [House Seach Web Map](https://www.arcgis.com/apps/mapviewer/index.html?webmap=a9f2fa2b4262417f96440b300cdda491).


## Prerequisites

Before running the geoprocessing tool, the user should:

1. Clone [Portfolio_examples](https://github.com/diflores79/Portfolio_examples/tree/main) to `C:\github`
2. Run /scripts/first_run.py locally to copy files to `C:\github_house_search_local`
3. Open `C:\github_house_search_local\geospatial_files\web_map_view.aprx` with ArcGIS Pro.
4. In ArcGIS Pro, click on the `View` tab, and then click on `Catalog Pane`.
5. In the opened Catalog Pane, open `Folders`, right-click `web_map_view.atbx`, click `New`, and then click on `Script`
6. On the left side of the New Script window, click on `Execution`, click on the Browse button, find `C:\github_house_search_local\scripts\house_search_agol.py`, and then click ok.
7. On the left side of the New Script window, click Parameters. You will create 3 parameters:

    | Label | Data Type | 
    |-------| ------|
    | Type "csv path" | Select "File" Parameter Data Type|
    | Type "AGOL Username" | Keep the Parameter Data Type as "String" |
    | Type "AGOL Password" | Keep the Parameter Data Type as "String" |
8. Save the project to keep the changes





