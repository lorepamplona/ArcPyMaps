print("Script started")

import arcpy
import os

arcpy.env.workspace = r"C:\Users\CHD\Documents\CHD\2023\Codes"
input_folder = r"C:\Users\CHD\Documents\CHD\2023\Codes\Input XYZ"
output_folder = r"C:\Users\CHD\Documents\CHD\2023\Codes\Output XYZ"
mask_folder = r"C:\Users\CHD\Documents\CHD\2023\Codes\Masks"
def clip_with_mask_if_exists(output_raster, mask_prefix):
    mask_shp = None
    #print("Mask prefix:", mask_prefix)
    for f in os.listdir(mask_folder):
        #print("Found file:", f)
        if f.lower().startswith(mask_prefix.lower()) and f.endswith('.shp'):
            mask_shp = os.path.join(mask_folder, f)
            break

    if mask_shp:
        print("Found mask:", mask_shp)
        clipped_raster = os.path.splitext(output_raster)[0] + '_clipped.tif'
        #desc = arcpy.Describe(mask_shp)        
        #rectangle = "{} {} {} {}".format(desc.extent.XMin, desc.extent.YMin, desc.extent.XMax, desc.extent.YMax)
        #arcpy.management.Clip(output_raster, rectangle, clipped_raster, mask_shp, "-3.402823e+38", "ClippingGeometry", "NO_MAINTAIN_EXTENT")
        out_raster = arcpy.sa.ExtractByMask(output_raster, mask_shp)        
        out_raster.save(clipped_raster)
        return clipped_raster
    else:
        print("No matching mask found. Skipping clipping.")
        return output_raster
def clean_filename(filename):
    return "".join(c for c in filename if c.isalnum() or c == '_')

# And then use it like this:


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

for xyz_file in xyz_files:
    input_xyz = os.path.join(input_folder, xyz_file)
    output_raster_name = os.path.splitext(xyz_file)[0] + '.tif'
    output_raster = os.path.join(output_folder, "".join(e for e in os.path.splitext(xyz_file)[0] if e.isalnum()) + '.tif')

    print("Processing:", input_xyz)
    print("Output raster:", output_raster)

    try:
        # Convert XYZ to shapefile of points
        input_points = os.path.join(output_folder, os.path.splitext(xyz_file)[0] + '.shp')
        if arcpy.Exists(input_points):
            arcpy.Delete_management(input_points)
        arcpy.ASCII3DToFeatureClass_3d(input_xyz, "XYZ", input_points, "POINT")

        tin_output = os.path.join(output_folder, os.path.splitext(xyz_file)[0] + '.tin')
        if arcpy.Exists(tin_output):
            arcpy.Delete_management(tin_output)

        arcpy.CreateTin_3d(tin_output, arcpy.SpatialReference(31981), [[input_points, 'Shape.Z']])


        # Convert TIN to raster
        raster_temp = os.path.join(output_folder, os.path.splitext(xyz_file)[0] + '_temp.tif')
        if arcpy.Exists(raster_temp):
            arcpy.Delete_management(raster_temp)
        arcpy.ddd.TinRaster(tin_output, raster_temp, "FLOAT", "LINEAR", "CELLSIZE", 1, 1)

        # Applying the Z factor
        raster_temp_zfactor = os.path.join(output_folder, os.path.splitext(xyz_file)[0] + '_temp_zfactor.tif')
        if arcpy.Exists(raster_temp_zfactor):
            arcpy.Delete_management(raster_temp_zfactor)
            spatial_ref = arcpy.SpatialReference(31981)  # replace with the correct EPSG code or projection file
            arcpy.ProjectRaster_management(raster_temp, raster_temp_zfactor, spatial_ref, "BILINEAR", 1, "1 0", "", 1)

        # Check if a mask exists and clip the raster if it does
        
        # Extract the necessary prefix (before the first space)
        mask_prefix = os.path.splitext(xyz_file)[0].split(' ')[0]
        output_raster = clip_with_mask_if_exists(raster_temp, mask_prefix)


        # Convert raster to points
        #arcpy.RasterToPoint_conversion(output_raster, "in_memory/temp_points_raster", "VALUE")

        # Convert points to raster
        #if arcpy.Exists(output_raster):
          #  arcpy.Delete_management(output_raster)
        #arcpy.PointToRaster_conversion("in_memory/temp_points_raster", "GRID_CODE", output_raster, "MEAN", "", 1)

                
        output_contours = os.path.join(output_folder, clean_filename(os.path.splitext(xyz_file)[0]) + '_contours.shp')
        print("Output contours:", output_contours)
        if arcpy.Exists(output_contours):
            arcpy.Delete_management(output_contours)
        contour_interval = 5
        
        #arcpy.ddd.Contour(output_raster, output_contours, contour_interval)
        arcpy.ddd.Contour(output_raster, output_contours, contour_interval)

        print("Output contours:", output_contours)
    except Exception as e:
        print("Error while processing file:", e)
    finally:
        clean_temp_data()

print("Script finished")
