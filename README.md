# Readme

## About
This is a personal side project. The goal of this geoprocessing tool is to geospatially analyze new homes from [Redfin](https://www.redfin.com/county/1910/NJ/Union-County) to identify newly posted NJ homes that are not within the 100 year floodplain, and has a train station within 1.5 kilometers. There will be 2 exports of the data:

1. All new homes will be appended to a local feature class: `C:/github_house_search_local/geospatial_files/gdb/homes/homes_for_sale`
2. Select homes will be automatically appended to a hosted feature class in ArcGIS Online (AGOL). New homes that meet this criteria will be appended to the AGOL hosted feature layer:

    - Must not be within the 100 year floodplain
    - Must be within 1.5 km of a train station
    - Must have more than 2 bedrooms
    - The price must be less than $450,000 

Review script/house_search_agol.py to see what the script does and how it processes and loads the new homes data.

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

## Prerequisites

Before running the geoprocessing tool, the user should:

1. Clone [Portfolio_examples](https://github.com/diflores79/Portfolio_examples/tree/main) to `C:\github`
2. Run /scripts/first_run.py locally to copy files to `C:\github_house_search_local`
3. Open `C:\github_house_search_local\geospatial_files\web_map_view.aprx` with ArcGIS Pro.
4. In ArcGIS Pro, click on the `View` tab, and then click on `Catalog Pane`.
5. In the opened Catalog Pane, open `Folders`, right-click `web_map_view.atbx`, click `New`, and then click on `Script`
6. On the left side of the New Script window, click on `Execution`, click on the Browse button, find `C:\github_house_search_local\scripts\house_search_agol.py`, and then click ok.
7. On the left side of the New Script window, click Parameters. You will create 3 parameters


