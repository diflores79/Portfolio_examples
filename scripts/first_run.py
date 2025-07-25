import arcpy 

#repos folder variables
gh_main_folder = 'C:/github/Portfolio_examples'

#copies files from C:/github/Portfolio_examples to a newly created C:/github_house_search_local
arcpy.management.Copy(gh_main_folder, 'C:/github_house_search_local')