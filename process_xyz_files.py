print("Script started")

import arcpy
import os

arcpy.env.workspace = r"C:\Users\CHD\Documents\ArcPyProject"
input_folder = r"C:\Users\CHD\Documents\ArcPyProject\Input XYZ"
output_folder = r"C:\Users\CHD\Documents\ArcPyProject\Output XYZ"

print("Input folder: {}".format(input_folder))
print("Output folder: {}".format(output_folder))

try:
    xyz_files = [f for f in os.listdir(input_folder) if f.endswith('.xyz')]
    print("Found XYZ files:", xyz_files)
except Exception as e:
    print("Error while listing XYZ files:", e)

def clean_temp_data():
    if arcpy.Exists("in_memory/temp_points"):
        arcpy.Delete_management("in_memory/temp_points")

def clip_with_mask_if_exists(output_raster, mask_prefix):
    mask_shp = None
    for f in os.listdir(input_folder):
        if f.startswith(mask_prefix) and f.endswith('.shp'):
            mask_shp = os.path.join(input_folder, f)
            break

    if mask_shp:
        print("Found mask:", mask_shp)
        clipped_raster = os.path.splitext(output_raster)[0] + '_clipped.tif'
        arcpy.Clip_management(output_raster, "#", clipped_raster, mask_shp, "#", "ClippingGeometry")
        return clipped_raster
    else:
        print("No matching mask found. Skipping clipping.")
        return output_raster

for xyz_file in xyz_files:
    input_xyz = os.path.join(input_folder, xyz_file)    
    output_raster_name = os.path.splitext(xyz_file)[0] + '.tif'
    output_raster = os.path.join(output_folder, os.path.splitext(xyz_file)[0].replace(',', '_').replace(' ', '_') + '.tif')

    print("Processing:", input_xyz)
    print("Output raster:", output_raster)

    try:
        spatial_ref = arcpy.SpatialReference(31981)
        arcpy.CreateFeatureclass_management("in_memory", "temp_points", "POINT", "", "DISABLED", "ENABLED", spatial_ref)
        arcpy.AddField_management("in_memory/temp_points", "POINT_Z", "DOUBLE")

        with arcpy.da.InsertCursor("in_memory/temp_points", ["SHAPE@X", "SHAPE@Y", "SHAPE@Z", "POINT_Z"]) as cursor:
            with open(input_xyz, "r") as f:
                for line in f:
                    x, y, z = map(float, line.split(","))
                    cursor.insertRow((x, y, z, z))

        arcpy.PointToRaster_conversion("in_memory/temp_points", "POINT_Z", output_raster, "MEAN")

        # Clip raster with a mask if it exists
        output_raster = clip_with_mask_if_exists(output_raster, os.path.splitext(xyz_file)[0])

        output_contours = os.path.join(output_folder, os.path.splitext(xyz_file)[0] + '_contours.shp')
        contour_interval = 5
        arcpy.Contour_3d(output_raster, output_contours, contour_interval)

        print("Output contours:", output_contours)
    except Exception as e:
        print("Error while processing file:", e)
    finally:
        clean_temp_data()
