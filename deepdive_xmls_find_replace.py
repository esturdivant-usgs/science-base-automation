"""
Populate metadata files in the DeepDive data release.
"""
#%% Import packages
import os
import pandas as pd
import shutil
import io
import glob
import datetime
import re
import sys
from lxml import etree

#%%
"""
The master copy of the template spreadsheet is the Google Doc. Before running,
download it and change the csvfile variable below to the correct pathname.
"""
def trunc(string, length=40):
	string = (string[:length-3] + '...') if len(string) > length else string
	return(string)

def replace_in_file(fname, fstr, rstr, fill='xxx'):
    with io.open(fname, 'r', encoding='utf-8') as f:
        s = f.read()
    s, ct = re.subn(fstr, rstr, s)
    print("Replaced values matching '{}': {}.".format(trunc(fstr), ct))
    ct_fills = len(re.findall('(?i){}'.format(fill), s)) # Count remaining xxx values
    if ct_fills > 0:
        print("Found {} '{}' fills remaining.".format(ct_fills, fill))
    with io.open(fname, 'w', encoding='utf-8') as f:
        f.write(s)
    return(fname)

def find_replace_dfvalues(fname, df, sycode, temp_field='templated_value', verbose=True):
    # Takes dataframe
    ct = 0
    # 1. Read input file
    with io.open(fname, 'r', encoding='utf-8') as f:
        s = f.read()
    # 2. Replace strings for each row in the template DF
    for fstr, row in df.iterrows():
        rstr = str(row.loc[sycode])
        if not isinstance(fstr, str): # type(fstr) == 'str':
            continue
        if not rstr == 'nan':
            # s = s.replace(fstr, rstr)
            s, ct2 = re.subn(fstr, rstr, s)
            ct += ct2
    # 2.b. Replace metadata date
    nowstr = datetime.datetime.now().strftime("%Y%m%d")
    s, ct2 = re.subn("<metd>.*</metd>", "<metd>{}</metd>".format(nowstr), s)
    ct += ct2
    # 2.c. Count remaining xxx values
    ct_fills = len(re.findall('(?i)xxx', s))
    # 3. Write output file
    with io.open(fname, 'w', encoding='utf-8') as f:
        f.write(s)
    if verbose:
        if ct_fills < 1:
            print("{} value(s) replaced. No 'xxx' fill values remaining.".format(ct))
        else:
            print("{} value(s) replaced.".format(ct))
            print("{} 'xxx' value(s) remaining.".format(ct_fills))
    return(ct_fills)

def replace_in_filelist(searchpath, findstr, replacestr):
    """
    Example use:
    searchpath = os.path.join(basedir, '*/*/*_pts_eainfo.xml')
    findstr = "<attr>xxxNourishmentxxx</attr>"
    replacestr = nourish_ea
    replace_in_filelist(searchpath, findstr, replacestr)
    """
    xmllist = glob.glob(searchpath)
    for fp in xmllist:
        ct = 0
        # 1. Read input file
        with io.open(fp, 'r', encoding='utf-8') as f:
            s = f.read()
        # 2. Replace strings
        s, ct2 = re.subn(findstr, replacestr, s)
        ct += ct2
        # 2.c. Count remaining xxx values
        ct_fills = len(re.findall('(?i)xxx', s))
        # 3. Write output file
        with io.open(fp, 'w', encoding='utf-8') as f:
            f.write(s)
        # Wrap up
        print("{} value(s) replaced.".format(ct))
        print("{} 'xxx' value(s) remaining in {}.".format(ct_fills, os.path.basename(fp)))

def copytree(src, dst, symlinks=False, ignore=None):
    for item in os.listdir(src):
        s = os.path.join(src, item)
        d = os.path.join(dst, item)
        if os.path.isdir(s):
            shutil.copytree(s, d, symlinks, ignore)
        else:
            shutil.copy2(s, d)

def backup_xmls(basedir, sycode, backup_dir, perform_backup=True, verbose=True):
    # Backup XML files before the os.rename overwrites them
    xmllist = glob.glob(os.path.join(basedir, sycode, '*.xml'), recursive=False)
    for infile in xmllist:
        relpath = os.path.relpath(infile, basedir)
        orig_backup = os.path.join(backup_dir, relpath)
        if not os.path.exists(orig_backup) and perform_backup:
            os.makedirs(os.path.split(orig_backup)[0], exist_ok=True)
            shutil.copy(infile, orig_backup)
        else:
            if verbose:
                print("We already have a backup of that file. ")
    return(True)

def rename_xmls(basedir, sycode, valuesdf, verbose=True):
    if not os.path.exists(os.path.join(basedir, sycode)):
        if verbose:
            print("The '{}' directory isn't present in the basedir.".format(sycode))
        return([])
    xmllist = glob.glob(os.path.join(basedir, sycode, '*.xml'), recursive=False)
    # Rename template xml files to the sycode
    sycode_elev = valuesdf.at['xxx-elev siteyear code-xxx', sycode]
    sycode_hab = valuesdf.at['xxx-hab siteyear code-xxx', sycode]
    for fp in xmllist:
        ct = 0
        fp_out, ct = re.subn("xxxx", sycode, fp)
        if ct == 1:
            os.rename(fp, fp_out)
            continue
        fp_out, ct = re.subn("X{4}", sycode_hab, fp)
        if ct == 1:
            os.rename(fp, fp_out)
            continue
        fp_out, ct = re.subn("X{3}", sycode_elev, fp)
        if ct == 1:
            os.rename(fp, fp_out)
            continue
    # List all xml files in [sycode] folder in basedir.
    xmllist = glob.glob(os.path.join(basedir, sycode, '*.xml'), recursive=False)
    if verbose:
        print("There are {} XML files in {}. ".format(len(xmllist), os.path.join(basedir, sycode)))
    return(xmllist)

def rename_sycode_dirs(basedir, valuesdf, code2name=True):
    # Rename from the full name to the code or vice versa
    # Map the sycodes to the full names
    namelist = []
    for sycode in valuesdf.columns:
        newname = '{}, {}, {}'.format(valuesdf.at['xxx-site-xxx', sycode],
                                      valuesdf.at['xxx-state abbr-xxx', sycode],
                                      valuesdf.at['xxx-supclass year-xxx', sycode])
        namelist += [newname]
    dirnames = pd.DataFrame(index=valuesdf.columns, data=namelist, columns=['syname'])
    # Conditionally perform rename
    if code2name:
        # Rename from the code to the full name
        for i, row in dirnames.iterrows():
            try:
                os.rename(os.path.join(basedir, i), os.path.join(basedir, row.syname))
            except:
                pass
    else:
        # Rename from the full name to the code
        for i, row in dirnames.iterrows():
            try:
                os.rename(os.path.join(basedir, row.syname), os.path.join(basedir, i))
            except:
                pass

# Copied from autoSB.py
def remove_xml_element(in_metadata, path='./', fill_text=['AUTHOR']):
    # Remove XML elements in path that contain fill text
    """ Example:
    tree = etree.parse(xml_file)
    metadata_root = tree.getroot()
    metadata_root = remove_xml_element(metadata_root)
    tree.write(xml_file)
    """
    # get metadata root
    metadata_root, tree, xml_file = get_root_flexibly(in_metadata)
    # get fill_text as list of strings
    if type(fill_text) is str:
        fill_text = [fill_text]
    elif not type(fill_text) is list:
        print('fill_text must be string or list')
        raise(Exception)
    # Search the matching tags for fill_text and remove all elements in which it is found.
    container, tag = os.path.split(path)
    parent_elem = metadata_root.find(container)
    for elem in parent_elem.iter(tag):
        for text in elem.itertext():
            for ftext in fill_text:
                if ftext in text:
                    parent_elem.remove(elem)
    # Either overwrite XML file with new XML or return the updated metadata_root
    if type(xml_file) is str:
        tree.write(xml_file)
        return xml_file
    else:
        return metadata_root

def get_root_flexibly(in_metadata):
	if type(in_metadata) is etree._Element:
		metadata_root = in_metadata
		tree = False
		xml_file =False
	elif type(in_metadata) is str:
		xml_file = in_metadata
		try:
			tree = etree.parse(xml_file) # parse metadata using etree
		except etree.XMLSyntaxError as e:
			print("XML Syntax Error while trying to parse XML file: {}".format(e))
			return False
		except Exception as e:
			print("Exception while trying to parse XML file: {}".format(e))
			return False
		metadata_root=tree.getroot()
	else:
		print("{} is not an accepted variable type for 'in_metadata'".format(in_metadata))
	return metadata_root, tree, xml_file

def replace_element_in_xml(in_metadata, new_elem, containertag='./distinfo'):
	# Overwrites the first element in containertag corresponding to the tag of new_elem
	# in_metadata accepts either xml file or root element of parsed metadata.
	# new_elem accepts either lxml._Element or XML string
	# Whether in_metadata is a filename or an element, get metadata_root
	metadata_root, tree, xml_file = get_root_flexibly(in_metadata)
	if type(new_elem) is str:
		new_elem = etree.fromstring(new_elem)
	elif not type(new_elem) is etree._Element:
		raise TypeError("'new_elem' takes either strings or elements.")
	# Replace element with new_elem
	elem = metadata_root.findall(containertag)[0]
	old_elem = elem.findall(new_elem.tag)[0]
	elem.replace(old_elem, new_elem)
	# Either overwrite XML file with new XML or return the updated metadata_root
	if type(xml_file) is str:
		tree.write(xml_file)
		return xml_file
	else:
		return metadata_root

def change_cei10_shoreline_xml(xml_file, valuesdf):
    # 1. <purpose> Change to: “This file consists of GeoTIFF raster data produced in reference to the shoreline polygon dataset (cei10_shoreline.shp) published within the larger work. The shoreline was not further checked for topological consistency. No further logical accuracy tests were conducted on the present dataset.”
    new_elem = """<purpose>The shoreline polygons (cei10_shoreline.shp) are a generalized delineation of the mean high water (MHW) position on the seaward face of the island and mean tidal level (MTL, average of MHW and mean low water) position on the inland face. They delineate the shoreline for the purposes of this study.  These polygons were used to measure distance to ocean and distance to foraging (see larger work). In addition, the inlet delineation polylines (cei10_inletLines.shp) use single straight line segments to roughly locate each side of tidal inlets for the barrier island study area. These lines were used to designate the transition between ocean-facing and land-facing sides of the barrier island. They were created manually to cross the MHW contour line on each side of a tidal inlet within the study area.</purpose>"""
    metadata_replacements = {'./idinfo/descript':new_elem}
    [replace_element_in_xml(xml_file, new_elem, containertag) for containertag, new_elem in metadata_replacements.items()]

    # 2. Remove cross-ref
    remove_fills = {'./idinfo/crossref':['xxx-morph pt filename-xxx']}
    [remove_xml_element(xml_file, path, ftext) for path, ftext in remove_fills.items()]

    # 3. Change horizpar
    new_elem = """<horizpar>cei10_shoreline.shp: Positional accuracy is dependent on the accuracy of the input dataset (DEM) and on the generalization routines used to create these polygons. For any given section, these outlines are assumed to be accurate within 25 m.\n\ncei10_inletLines.shp: These data are an approximation. Their assumed positional accuracy is 5 m.</horizpar>"""
    metadata_replacements = {'./dataqual/posacc/horizpa':new_elem}
    [replace_element_in_xml(xml_file, new_elem, containertag) for containertag, new_elem in metadata_replacements.items()]

    # 4. Change procdesc
    ipy = valuesdf.cei10.loc['xxx-ipy filename-xxx']
    sycode = 'cei10'
    mhw = valuesdf.cei10.loc['xxx-mhw offset-xxx']
    mtl = valuesdf.cei10.loc['xxx-mtl elev-xxx']
    poly_ct = valuesdf.cei10.loc['xxx-polys in shoreline-xxx']
    new_elem = """<procdesc>Full methods are provided in the associated Methods OFR (Zeigler and others 2019). The iPython notebook used for processing ({}.html) is distributed with this dataset.\n\n{}_shoreline.shp:\n\nA polygon outlining the shoreline of the island was created for the study area. On the ocean-facing side of the island, this was considered the MHW contour (Weber and others 2005, Zeigler and others 2019). To include partially submerged wetland on the estuarine-side, the land-facing shoreline was delineated at mean tidal level (MTL), which was calculated from the local MHW and mean low water (MLW) levels at the given study area.\n\nThe local MLW elevation was estimated from NOAA&#8217;s VDatum (2014 release) as the average MLW elevation at a sample of nearshore points in the study area. Experimentation conducted as part of this study found that the MTL delineation more consistently identified the boundary between marsh (intertidal vegetation) and submerged areas than either MHW or MLW. For consistency with the MHW offset applied throughout the project, MHW was used as part of the calculation of MTL.\n\nTo create this shoreline, we performed the following steps. Most of the steps were performed programmatically using the function functions_warcpy.DEMtoFullShorelinePoly in bi-transect-extractor (Sturdivant, 2018):\n\n1. Manually digitize lines from the DEM that indicate where land meets a tidal inlet, which is considered the division point between the oceanside and the bayside or estuarine side of the island. This line was visually approximated.\n\n2. Create a generalized polygon from the DEM in which every cell within the polygon is above MHW (MHW polygon). This was performed programmatically using the function functions_warcpy.RasterToLandPerimeter in bi-transect-extractor v1.0 (Sturdivant, 2018) with a MHW elevation of {} m NAVD88, calculated for the area by Weber and others (2005). The process includes generalizing the polygons (Aggregate Polygons tool in the Cartography toolbox) using an aggregation distance of 10 m, a minimum area of 300 m, and a minimum hole size of 300 m.\n\n3. Repeat Step 3 for MTL, using an MTL elevation of {} m NAVD88.\n\n4. Merge the polygons so that the MHW contour outlines the island on the oceanside and the MTL contour outlines the island on the bayside, divided at the delineated tidal inlets. To do so, create a symmetrical difference polygon between MHW and MTL polygons (SymDiff) and split the resulting polygon at the inlet lines (Feature to Polygon). Create a polygon that outlines only the bayside area that is above MTL and below MHW (MTL-only polygon) by manually deleting the segments of the symmetrical difference polygon that pertain to the ocean-side of the island. Merge the MTL-only polygon with the MHW polygon (Union, Dissolve). This was performed using the function functions_warcpy.CombineShorelinePolygons in bi-transect-extractor (Sturdivant, 2018).\n\n5. QA/QC the output and manually revise any sections with clearly incorrect artifacts.\n\nThe dataset contains {} polygons.</procdesc>""".format(ipy, sycode, mhw, mtl, poly_ct)
    metadata_replacements = {'./dataqual/lineage/procstep':new_elem}
    [replace_element_in_xml(xml_file, new_elem, containertag) for containertag, new_elem in metadata_replacements.items()]

    # Remove section of resdesc
    fstr = " as well as the iPython notebook \(xxx-ipy filename-xxx\.html\) used for processing\."
    rstr = "."
    xml_file = os.path.join(basedir, 'cei10', 'cei10_shoreline_inletLines_meta.xml')
    replace_in_file(xml_file, fstr, rstr)

    return(xml_file)

def change_cei10_disocean_xmls(xml_file):
    # 1. Remove cross-ref
    remove_fills = {'./idinfo/crossref':['xxx-morph pt filename-xxx']}
    [remove_xml_element(xml_file, path, ftext) for path, ftext in remove_fills.items()]

    # 2. <logic> Change to: “This file consists of GeoTIFF raster data produced in reference to the shoreline polygon dataset (cei10_shoreline.shp) published within the larger work. The shoreline was not further checked for topological consistency. No further logical accuracy tests were conducted on the present dataset.”
    new_logic = """<logic>This file consists of GeoTIFF raster data produced in reference to the shoreline polygon dataset (cei10_shoreline.shp) published within the larger work. The shoreline was not further checked for topological consistency. No further logical accuracy tests were conducted on the present dataset.</logic>"""
    new_horizpar = """<horizpar>We assume an accuracy within 5 m horizontally. No formal accuracy assessments of the horizontal positional information in the dataset have been conducted. However, the accuracy is dependent on that of the source data.\n\nHorizontal accuracy is inherited from the seaward portion of the shoreline polygons (cei10_shoreline.shp in the larger work). Seaward segments of the shoreline polygons are accurate to about 5 m.\n\nThis raster file was created in reference system North American Datum (NAD) 1983 Universal Transverse Mercator (UTM) zone 18N at a resolution of 5 m.</horizpar>"""
    metadata_replacements = {'./dataqual':new_logic, './dataqual/posacc/horizpa':new_horizpar}
    [replace_element_in_xml(xml_file, new_elem, containertag) for containertag, new_elem in metadata_replacements.items()]
    for containertag, new_elem in metadata_replacements.items():
        print('Replaced {}'.format(containertag))

    # 4. Replace text in procdesc
    fstr = "points \(cei10_SLpts\.shp in larger work\) were"
    rstr = "(cei10_shoreline.shp in larger work) was" #"(cei10_shoreline.shp in larger work) was"
    replace_in_file(xml_file, fstr, rstr)
    return(xml_file)

def change_fiis14_shoreline_xml(xml_file):
    new_elem = """<complete>fiis14_shoreline.shp: The polygons represent a generalized outline of the land above water. Polygons within 30 m of each other were aggregated and land masses and polygon holes less than 300 m2 were eliminated (Aggregate Polygons tool in Cartography toolbox, ArcGIS 10.5). Polygon outlines were compared to ancillary datasets, such as elevation and orthoimagery. The delineation is generalized and should not be used for any purpose that requires precision or accuracy, such as navigation or engineering.\n\nThese polygons extend to the east outside the bounds of the study area. The other datasets in this release do not extend as far, but the area was included to facilitate the calculation of the Dist2Inlet variable, which is measured in the 5-m points file (fiis14_pts.csv in the larger work).\n\nfiis14_inletLines.shp: All points where the barrier island alongshore shoreline is broken are located in these data. If one side of a delineated inlet was not within the study area, that side was not delineated.</complete>"""
    metadata_replacements = {'./dataqual':new_elem}
    [replace_element_in_xml(xml_file, new_elem, containertag) for containertag, new_elem in metadata_replacements.items()]
    return(xml_file)

def change_rock14_SupClas_xml(xml_file):
    # Purpose
    fstr = """Raster files Rock14_SubType\.tif, Rock14_VegDen\.tif, Rock14_VegType\.tif were reclassified from the supervised classification raster with some manual modifications\. Rock14_SubType\.tif"""
    rstr = """Raster files Rock14_SubType.tif, Rock14_VegDen.tif, Rock14_VegType.tif were reclassified from the supervised classification raster with some manual modifications. Specific to Rockaway 2014, the substrate type, vegetation type, and vegetation density layers were refined using a shapefile of landcover types digitized in-situ by H. Abouelezz of the National Park Service (Zeigler and others 2017). Rock14_SubType.tif"""
    replace_in_file(xml_file, fstr, rstr)
    # SubType
    fstr = """Not all values may be represented for this site\.\n\nWe made one manual change to the reclassification of the supervised classification to create the substrate type layer"""
    rstr = """Not all values may be represented for this site.\n\nWe further refined the substrate type layer with a shapefile of landcover types made by H. Abouelezz in 2013 with a hand-held Global Navigation Satellite System receiver (hereafter, the “GNSS dataset”; Zeigler and others 2017). This dataset covered a small portion of our total study area. We reclassified polygons in the GNSS dataset to match categories considered for Substrate Type (i.e., Sand, Shell/Gravel/Cobble, Mud/Peat, Water, or Development) and converted the reclassified GNSS dataset to a raster. We overlayed this rasterized GNSS dataset onto the classification layer such that raster cells took on the value of the GNSS dataset. All remaining cells (i.e., those not covered by the GNSS dataset) retained their value from the reclassified supervised classification.\n\nWe made one manual change to the reclassification of the supervised classification to create the substrate type layer"""
    replace_in_file(xml_file, fstr, rstr)
    # VegDen
    fstr = """Not all values may be represented in this dataset\.\n\nWe made one manual change to the reclassification of the supervised classification to create the vegetation density layer"""
    rstr = """Not all values may be represented for this site.\n\nWe further refined the vegetation density layer with a shapefile of landcover types made by H. Abouelezz in 2013 with a hand-held Global Navigation Satellite System receiver (hereafter, the “GNSS dataset”; Zeigler and others 2017). This dataset covered a small portion of our total study area. We reclassified polygons in the GNSS dataset to match categories considered for vegetation density (i.e., None, Sparse, Moderate, etc.) and converted the reclassified GNSS dataset to a raster. We overlayed this rasterized GNSS dataset onto the classification layer such that raster cells took on the value of the GNSS dataset. All remaining cells (i.e., those not covered by the GNSS dataset) retained their value from the reclassified supervised classification.\n\nWe made one manual change to the reclassification of the supervised classification to create the vegetation density layer"""
    replace_in_file(xml_file, fstr, rstr)
    # VegType
    fstr = """Not all values may be represented for this site\.\n\nWe made one manual change to the reclassification of the supervised classification to create the vegetation type layer"""
    rstr = """Not all values may be represented for this site.\n\nWe further refined the vegetation type layer with a shapefile of landcover types made by H. Abouelezz in 2013 with a hand-held Global Navigation Satellite System receiver (hereafter, the “GNSS dataset”; Zeigler and others 2017). This dataset covered a small portion of our total study area. We reclassified polygons in the GNSS dataset to match categories considered for vegetation type (i.e., None, Herbaceous, Shrub, etc.) and converted the reclassified GNSS dataset to a raster. We overlayed this rasterized GNSS dataset onto the classification layer such that raster cells took on the value of the GNSS dataset. All remaining cells (i.e., those not covered by the GNSS dataset) retained their value from the reclassified supervised classification.\n\nWe made one manual change to the reclassification of the supervised classification to create the vegetation type layer"""
    replace_in_file(xml_file, fstr, rstr)
    # return
    return(xml_file)

#%%
"""
## Execute
"""
# Initialize variables
basedir = r"/Volumes/stor/Projects/DeepDive/5_datarelease_packages/vol1_v3"
backup_dir = os.path.join(basedir, "backup_xmls")
template_dir = r"/Volumes/stor/Projects/DeepDive/5_datarelease_packages/template_development/v2.5/templates"
csvfname = "template_values.csv"
csvfpath = os.path.join(basedir, csvfname)

#%% Save copy of csv file (templating spreadsheet) in backup dir
nowbackup = os.path.join(backup_dir, datetime.datetime.now().strftime("%Y%m%d"))
os.makedirs((nowbackup), exist_ok=True)
shutil.copy2(csvfpath, nowbackup)

# Get values from CSV
valuesdf = pd.read_csv(csvfpath, header=0, index_col='templated_value', dtype='str')#, names=['templated_value', sycode])

#%% Rename from the full name to the code
rename_sycode_dirs(basedir, valuesdf, False)

#%% Run the process -
# For every site-year, copy and rename the template files, then replace the fill values from the spreadsheet
perform_backup = False
remaining_fills = pd.DataFrame(columns=['file', 'fill_count'])
for sycode in valuesdf.columns:
    # Back up existing XML files and copy template
    backup_xmls(basedir, sycode, backup_dir, perform_backup, verbose=False)
    # Copy template files into sycode directory
    copytree(template_dir, os.path.join(basedir, sycode))
    # Rename template XMLs to match the site-year.
    xmllist = rename_xmls(basedir, sycode, valuesdf)
    #% Run find and replace to apply to all xml files in list
    for infile in xmllist:
        relpath = os.path.relpath(infile, basedir)
        ct_fills = find_replace_dfvalues(infile, valuesdf, sycode, verbose=False)
        if ct_fills > 0:
            remaining_fills = remaining_fills.append({'file':relpath, 'fill_count':ct_fills}, ignore_index=True)

print(len(remaining_fills))
print(remaining_fills)

#%% Make "manual" changes to files
# Cedar 2010
xml_file = os.path.join(basedir, 'cei10', 'CeI10_DisOcean.tif.xml')
change_cei10_disocean_xmls(xml_file)
xml_file = os.path.join(basedir, 'cei10', 'cei10_shoreline_inletLines_meta.xml')
change_cei10_shoreline_xml(xml_file, valuesdf)
xml_file = os.path.join(basedir, 'cei10', 'CeI11_SupClas_GeoSet_SubType_VegDen_VegType_meta.xml')
# 1. Remove cross-ref
remove_fills = {'./idinfo/crossref':['xxx-morph pt filename-xxx']}
[remove_xml_element(xml_file, path, ftext) for path, ftext in remove_fills.items()]

# Cedar 2014
fstr = "if present \(xxx-no dev in larger work\)\."
rstr = "if present."
xml_file = os.path.join(basedir, 'cei14', 'CeI14_SupClas_GeoSet_SubType_VegDen_VegType_meta.xml')
replace_in_file(xml_file, fstr, rstr)
xml_file = os.path.join(basedir, 'cei12', 'CeI12_SupClas_GeoSet_SubType_VegDen_VegType_meta.xml')
replace_in_file(xml_file, fstr, rstr)
xml_file = os.path.join(basedir, 'cei10', 'CeI11_SupClas_GeoSet_SubType_VegDen_VegType_meta.xml')
replace_in_file(xml_file, fstr, rstr)

# FireIsland
xml_file = os.path.join(basedir, 'fiis14', 'fiis14_shoreline_inletLines_meta.xml')
change_fiis14_shoreline_xml(xml_file)

# Rockaway 2014
xml_file = os.path.join(basedir, 'rock14', 'rock14_DC_DT_SLpts_meta.xml')
new_elem = """<vertaccr>The per-feature vertical accuracy estimate is not provided for this dataset. Vertical accuracy is dependent on density of and scatter in the lidar data points, and the lidar point uncertainty.</vertaccr>"""
metadata_replacements = {'./dataqual/posacc/vertacc':new_elem}
[replace_element_in_xml(xml_file, new_elem, containertag) for containertag, new_elem in metadata_replacements.items()]
# Rockaway 2014 SupClas
xml_file = os.path.join(basedir, 'rock14', 'Rock14_SupClas_GeoSet_SubType_VegDen_VegType_meta.xml')
change_rock14_SupClas_xml(xml_file)


#%% Remove all xmls from data folders
for sycode in valuesdf.columns:
    par = os.path.join(basedir, sycode)
    old_xmls = glob.glob(os.path.join(par, '[!xxx_trash]*/*.xml'))
    for xml in old_xmls:
        os.remove(xml)
    # For some reason, the first glob doesn't include the xmls in the shoreline* dir
    old_xmls = glob.glob(os.path.join(par, 'shoreline*/*.xml'))
    for xml in old_xmls:
        os.remove(xml)

#%% Move the new xmls to data folders. Delete unclaimed XMLs.
for sycode in valuesdf.columns:
    par = os.path.join(basedir, sycode)
    dirs = glob.glob(os.path.join(par, '*/'))
    for d in dirs:
        # get search str from directory name
        d = os.path.split(d)[0]
        searchstr = os.path.basename(d).split()[0]
        xmls = glob.glob(os.path.join(par, '*{}*.xml'.format(searchstr))) #[0]
        if not xmls:
            continue
        elif len(xmls) > 1:
            print("WARNING: Multiple XML files matched '{}'".format(searchstr))
        xml_in = xmls[0]
        xml_out = os.path.join(d, os.path.basename(xml_in))
        shutil.move(xml_in, xml_out)
    # Delete any remaining XML files in the sycode directory.
    leftovers = glob.glob(os.path.join(par, '*.xml'))
    if len(leftovers) > 0:
        for xml in leftovers:
            os.remove(xml)
        print("Removed remaining {} XMLs from {} because they weren't matched.".format(len(leftovers), sycode))

#%% Check remaining XMLs for xxx fill values
remaining_fills = pd.DataFrame(columns=['file', 'fill_count'])
for sycode in valuesdf.columns:
    # List xmls
    xmllist = glob.glob(os.path.join(basedir, sycode, '*', '**.xml'), recursive=True)
    #% Run find and replace to apply to all xml files in list
    for infile in xmllist:
        relpath = os.path.relpath(infile, basedir)
        # Read file
        with io.open(infile, 'r', encoding='utf-8') as f:
            s = f.read()
        # Count fills
        ct_fills = len(re.findall('(?i)xxx', s))
        if ct_fills > 0:
            remaining_fills = remaining_fills.append({'file':relpath, 'fill_count':ct_fills}, ignore_index=True)

print(remaining_fills)

#%% Change the directory names (back-and-forth between code and full name)
# Map the sycodes to the full names
rename_sycode_dirs(basedir, valuesdf)

#%% Duplicate the dataset for ScienceBase upload
try:
    shutil.rmtree(basedir+'_4sb', ignore_errors=True)
except:
    pass
shutil.copytree(basedir, basedir+'_4sb', ignore=shutil.ignore_patterns('xxx_trash', 'backup_xmls'))














#%%
