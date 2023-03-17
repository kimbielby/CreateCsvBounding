import numpy as np
import json
import rasterio as rio
import pandas
""" Global Variables """
img_left_bounds = 0  # Left boundary of image in geo coordinates
img_right_bounds = 0  # Right boundary of image in geo coordinates
img_top_bounds = 0  # Top boundary of image in geo coordinates
img_bottom_bounds = 0  # Bottom boundary of image in geo coordinates
px_per_m = 0  # Number of pixels per metre of geo-coordinates
for_csv = []  # The list of list for bounding boxes in image


""" Handles all methods """
def here_we_go(geojson_file, img_filename, new_csv_name):
    poss_uuid, tree_annot = get_valid_uuid(geojson_file, img_filename)
    print("Length of poss_uuid list is: ", len(poss_uuid)) # Error checking
    full_coords_list = get_uuid_coords(poss_uuid, tree_annot)  # Get full geo-coordinates for possible uuid's
    print("Length of full_coords_list is: ", len(full_coords_list))  # Error checking
    lists_for_csv(img_filename, full_coords_list)
    print("Length of for_csv is: ", len(for_csv))  # Error checking
    calc_img_px_coords()
    print("Length of for_csv is: ", len(for_csv))  # Error checking
    create_csv(new_csv_name)


# TODO: SHOULD I BE COPYING FILES FIRST BEFORE DOING STUFF WITH THEM
#   - LIKE GABRIELA WAS SAYING IN AI MODULE?


""" 
Gets a list of uuid's from the geojson file whose bounding boxes geo-coords are within those of the image 
"""
def get_valid_uuid(geo_json_file, img_file):
    # Open the GeoJSON file and load it with JSON
    geo_j_file = open(geo_json_file)
    tree_annotations = json.load(geo_j_file)

    total_poss = 0  # Number of possible bounding boxes in image
    poss_uuid_list = []  # Empty list to put in uuid numbers of possible bounding boxes in image

    # Calculate image coords
    calc_px_per(img_file)  # "shouldbeworking2.tif"

    # Check the first x-y coordinate of each uuid to see if it is within bounds
    for i in tree_annotations["features"]:  # Check each bounding box
        uuid_num = i["properties"]["uuid"]  # Stores the uuid of the current bounding box object we are in
        # Holds all the arrays of each vertex in the current bounding box
        coords_array = np.array(i["geometry"]["coordinates"])
        if len(coords_array) > 0:  # Make sure the coordinates arrays are not empty
            current_bbox = coords_array[0][0][0]  # First vertex of the current bounding box

            # Make sure that the x and y coordinates of the first vertex are within image bounds
            if img_right_bounds >= current_bbox[0] >= img_left_bounds and img_top_bounds >= current_bbox[1] >= \
                    img_bottom_bounds:
                poss_uuid_list.append(uuid_num)  # Appends uuid to list if first coordinates are within bounds
                total_poss += 1  # Plus 1 the number of possible bounding boxes in image

    return poss_uuid_list, tree_annotations


"""
Calculates boundaries of image (both pixels and geo-coordinates) and pixels per metre
"""
# TODO
def calc_px_per(img_file):
    # global img_left_bounds
    # global img_right_bounds
    # global img_top_bounds
    # global img_bottom_bounds
    global px_per_m

    # Update the global vars with the Geolocation boundaries of image
    calc_geo_coords_boundaries(img_file)

    the_image = rio.open(img_file)

    # Width and Height of image in pixels
    img_width_px = the_image.width
    img_height_px = the_image.height  # todo: Why is 'img_height_px' not used?

    # Geolocation boundaries of image
    # img_left_bounds = the_image.bounds.left
    # img_right_bounds = the_image.bounds.right
    # img_top_bounds = the_image.bounds.top
    # img_bottom_bounds = the_image.bounds.bottom

    # Width and Height of image in geo-coord metres
    x_coords_span = img_right_bounds - img_left_bounds
    y_coords_span = img_top_bounds - img_bottom_bounds  # todo: Why is 'y_coords_span' not used?

    # Image pixels per geo-coord metre
    px_per_m = img_width_px / x_coords_span


def calc_geo_coords_boundaries(img_file):
    global img_left_bounds
    global img_right_bounds
    global img_top_bounds
    global img_bottom_bounds

    # Open and read the image file
    the_image = rio.open(img_file)

    # Calculate the geolocation boundaries of the image (& update global vars)
    img_left_bounds = the_image.bounds.left
    img_right_bounds = the_image.bounds.right
    img_top_bounds = the_image.bounds.top
    img_bottom_bounds = the_image.bounds.bottom


"""
Gets geo-coordinates for each uuid on poss_uuid_list and stores them in 2D List
"""
def get_uuid_coords(uuid_list, annot_file):
    # Go through geojson and get coordinates for each uuid on poss_uuid_list
    full_coords_list = []
    for i in uuid_list:
        for j in annot_file["features"]:
            if i == j["properties"]["uuid"]:
                full_coords_list.append(j["geometry"]["coordinates"])
    return full_coords_list

"""
From full_coords_list puts certain coordinates into a separate 2D list as:
    image_path (name of the image)
    xmin
    ymin
    xmax
    ymax
    label (e.g. 'tree')
"""
def lists_for_csv(img_name, coord_list):
    # Take certain coords from full_coords_list and put them into a separate list with the following pattern:
    # image_path (name of image); xmin; ymin; xmax; ymax; label (e.g. 'tree')
    global for_csv  # The list of lists for bounding boxes in image
    label = "tree"

    for i in coord_list:
        # Get mins and maxs of bounding box
        geo_xmin = i[0][0][0][0]
        geo_ymin = i[0][0][0][1]
        geo_xmax = i[0][0][2][0]
        geo_ymax = i[0][0][1][1]

        # Put everything in order for line in csv into a list
        temp_list = [img_name, geo_xmin, geo_ymin, geo_xmax, geo_ymax, label]
        # Add that bounding box list to the list of all bounding boxes in image
        for_csv.append(temp_list)


""" 
Calculates the image's pixel min-max for bounding box and replaces their geo-coordinate equivalent in for_csv List 
"""
def calc_img_px_coords():
    global for_csv
    # Calculate image pixel min-max for bounding box and replace their geo-coordinate equivalent in for_csv List
    for i in range(len(for_csv)):
        # The xmin in pixels: geo-coords of left edge of bounding box minus geo-coords of left edge of image
        # Multiplied by pixels per metre to turn geo-coord difference into pixel difference

        # REMEMBER: image pixel coordinates start top-left, NOT bottom-right
        px_xmin = (for_csv[i][1] - img_left_bounds) * px_per_m
        px_ymin = (img_top_bounds - for_csv[i][4]) * px_per_m
        px_xmax = (img_right_bounds - for_csv[i][3]) * px_per_m
        px_ymax = (img_top_bounds - for_csv[i][2]) * px_per_m

        # Now replace items in positions 1 through 4 in the List
        for_csv[i][1:5] = [px_xmin, px_ymin, px_xmax, px_ymax]


"""
Adds column headers and data from for_csv to a pandas dataframe then saves it as a csv file
"""
# TODO
def create_csv(csv_name):
    # TODO: How to delete the first column, the one with the index from 0? Do this after file is created?
    # Column headers to be in csv file
    columns = ["image_path", "xmin", "ymin", "xmax", "ymax", "label"]
    # Everything to be included in csv
    not_index_list = [i for i in for_csv]
    # Create pandas dataframe
    pd = pandas.DataFrame(not_index_list, columns=columns)
    # Create csv with column headers and index
    pd.to_csv(csv_name, index=False)  # "bounding.csv"


"""
Calls function to update the global geocoordinates vars of image
Returns geocoordinates for top-left corner of image 
"""
def get_top_left_geo_coords(img_file):
    calc_geo_coords_boundaries(img_file)
    return img_left_bounds, img_top_bounds
