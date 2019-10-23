"""
Populate metadata files in the DeepDive data release.
"""
#%% Import packages
import os
import pandas as pd
import shutil
import io
import glob
from datetime import datetime
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
    print("{}: {} value(s) replaced matching '{}'".format(os.path.basename(fname), ct, trunc(fstr)))
    ct_fills = len(re.findall('(?i){}'.format(fill), s)) # Count remaining xxx values
    if ct_fills > 0:
        print("{}: {} '{}' fills remaining.".format(os.path.basename(fname), ct_fills, fill))
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
            if verbose:
                print("Replace '{}' with '{}'".format(fstr, rstr))
            # s = s.replace(fstr, rstr)
            s, ct2 = re.subn(fstr, rstr, s)
            ct += ct2
    # 2.b. Replace metadata date
    nowstr = datetime.now().strftime("%Y%m%d")
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
    print("Searching for '{}'".format(trunc(findstr, 60)))
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
        print("{}: {} value(s) replaced; {} 'xxx' value(s) remaining".format(os.path.basename(fp), ct, ct_fills))

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
    xmllist = glob.glob(os.path.join(basedir, sycode, '**/*.[xX][mM][lL]'), recursive=True)
    if verbose:
        print('XMLs to backup: {}'.format(len(xmllist)))
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
    if verbose:
        print('Number of XMLs to rename: {}'.format(len(xmllist)))
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
        newname = valuesdf.at['xxx-site folder name-xxx', sycode]
        namelist += [newname]
    dirnames = pd.DataFrame(index=valuesdf.columns, data=namelist, columns=['syname'])
    # Conditionally perform rename
    if code2name:
        # Rename from the code to the full name
        for i, row in dirnames.iterrows():
            try:
                os.rename(os.path.join(basedir, i), os.path.join(basedir, row.syname))
            except Exception as ex:
                print(ex)
                pass
    else:
        # Rename from the full name to the code
        for i, row in dirnames.iterrows():
            try:
                os.rename(os.path.join(basedir, row.syname), os.path.join(basedir, i))
            except:
                pass

def copy_modified_files(src, dest, searchstr='**/*.xml', override_limit=False):
    # To search for specific files... searchstr = '**/*SLpts.dbf'
    ct = 0
    flist = glob.glob(os.path.join(src, searchstr), recursive=True)
    for fpath in flist:
        fname = os.path.basename(fpath)
        print(fname+'...')
        destmatchlist = glob.glob(os.path.join(dest, '**/{}'.format(fname)), recursive=True)
        if not destmatchlist:
            print('No matching files.')
            continue
        elif len(destmatchlist) == 1:
            fpath2 = destmatchlist[0]
            modtime1 = datetime.utcfromtimestamp(os.path.getmtime(fpath))
            modtime2 = datetime.utcfromtimestamp(os.path.getmtime(fpath2))
            # Replace the file if the modified time in the source directory is greater than the that in the destination
            if modtime1 > modtime2:
                shutil.copy(fpath, fpath2)
                print('Copied {} to {}'.format(fpath, fpath2))
                ct += 1
        elif override_limit:
            for fpath2 in destmatchlist:
                shutil.copy(fpath, fpath2)
                ct += 1
        else:
            print('More than one match.')
            continue
    if ct > 0:
        print("Copied {} files.\n".format(ct))
    return

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
    return(metadata_root, tree, xml_file)

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

def add_element_to_xml(in_metadata, new_elem, containertag='./idinfo'):
    # Appends element 'new_elem' to 'containertag' in XML file. in_metadata accepts either xmlfile or root element of parsed metadata. new_elem accepts either lxml._Element or XML string
    # Whether in_metadata is a filename or an element, get metadata_root
    # FIXME: Check whether element already exists
    metadata_root, tree, xml_file = get_root_flexibly(in_metadata)
    # If new element is still a string convert it to an XML element
    if type(new_elem) is str:
        new_elem = etree.fromstring(new_elem)
    elif not type(new_elem) is etree._Element:
        raise TypeError("'new_elem' takes either strings or elements.")
    # Append new_elem to containertag element
    elem = metadata_root.findall(containertag)[0]
    elem.append(new_elem) # append new tag to container element
    # Either overwrite XML file with new XML or return the updated metadata_root
    if type(xml_file) is str:
        tree.write(xml_file)
        return(xml_file)
    else:
        return(metadata_root)

def change_asis14_xmls(basedir):
    # Assateague
    sycode = 'asis14'
    # morph points
    xml_file = os.path.join(basedir, sycode, sycode+'_DC_DT_SLpts_meta.xml')
    fstr = "<attrdomv><edom><edomv>12xxx</edomv><edomvd>Virginiaxxx</edomvd><edomvds>Producer defined</edomvds></edom> </attrdomv>"
    rstr = "<attrdomv><edom><edomv>12</edomv><edomvd>Virginia</edomvd><edomvds>Producer defined</edomvds></edom> </attrdomv><attrdomv><edom><edomv>13</edomv><edomvd>Maryland</edomvd><edomvds>Producer defined</edomvds></edom> </attrdomv>"
    replace_in_file(xml_file, fstr, rstr)
    # All XMLs
    fstr = "<placekey>MD &#x26; VA</placekey>"
    rstr = "<placekey>MD</placekey><placekey>VA</placekey><placekey>Virginia</placekey><placekey>Chincoteague National Wildlife Refuge</placekey>"
    xmllist = glob.glob(os.path.join(basedir, sycode, '**.xml'), recursive=True)
    [replace_in_file(xml_file, fstr, rstr) for xml_file in xmllist]
    return

def change_assa14_xmls(basedir):
    # Assawoman
    # Mention that Assawoman and Wallops are the same island.
    sycode = 'assa14'
    # Add to place keywords
    containertag = './idinfo/keywords/place'
    new_tag = """<placekey>Wallops Island</placekey>"""
    xmllist = glob.glob(os.path.join(basedir, sycode, '**.xml'), recursive=True)
    # Don't rerun this
    [add_element_to_xml(xml_file, new_tag, containertag) for xml_file in xmllist]
    # Add to None theme keywords
    fstr = "<themekey>Assawoman Island</themekey>"
    fstr = "<themekey>Assawoman Island</themekey>(?!<themekey>Wallops)"
    rstr = "<themekey>Assawoman Island</themekey><themekey>Wallops Island</themekey>"
    replace_in_filelist(os.path.join(basedir, sycode, '**.xml'), fstr, rstr)

# North Carolina sites
def change_NC_xmls(basedir):
    # North Carolina sites
    # Replace srcinfo, crossref, and in-line references for NASC transects
    fstr_rstr = {"""<srccite>[\s\S]*New England and Mid-Atlantic Coasts[\s\S]*They were downloaded in 2017\.</srccontr>""":
    """<srccite><citeinfo><origin>Meredith G. Kratzmann</origin><origin>Emily A. Himmelstoss</origin><origin>E. Robert Thieler</origin><pubdate>2017</pubdate><title>National assessment of shoreline change – A GIS compilation of updated vector shorelines and associated shoreline change data for the Southeast Atlantic Coast</title><serinfo><sername>data release</sername><issue>DOI:10.5066/F74X55X7</issue></serinfo><pubinfo><pubplace>Reston, VA</pubplace><publish>U.S. Geological Survey</publish></pubinfo><onlink>https://doi.org/10.5066/F74X55X7</onlink></citeinfo></srccite><typesrc>digital data</typesrc><srctime><timeinfo><sngdate><caldate>2017</caldate></sngdate></timeinfo><srccurr>publication date</srccurr></srctime><srccitea>NASC transects</srccitea><srccontr>Shore-normal transects with long term shoreline change rates from the National Assessment of Shoreline Change (NASC) (NCnorth_transects_rates_LT.shp, NCcentral_transects_rates_LT.shp, NCsouth_transects_rates_LT.shp for both North Carolina sites). The data are distributed as an Esri polyline shapefile referenced to World Geodetic System 1984 (WGS84). They were downloaded in 2018.</srccontr>""",
     # """<crossref>[\s\S]*New England and Mid-Atlantic Coasts[\s\S]*</crossref>""": """<crossref><citeinfo><origin>Meredith G. Kratzmann</origin><origin>Emily A. Himmelstoss</origin><origin>E. Robert Thieler</origin><pubdate>2017</pubdate><title>National assessment of shoreline change – A GIS compilation of updated vector shorelines and associated shoreline change data for the Southeast Atlantic Coast</title><serinfo><sername>data release</sername><issue>DOI:10.5066/F74X55X7</issue></serinfo><pubinfo><pubplace>Reston, VA</pubplace><publish>U.S. Geological Survey</publish></pubinfo><onlink>https://doi.org/10.5066/F74X55X7</onlink></citeinfo></crossref>""",
    "Himmelstoss and others \(2010\)": "Kratzmann and others (2017)"}
    sycode = 'caha14'
    xml_file = os.path.join(basedir, sycode, sycode+'_pts_trans_ubw_meta.xml')
    [replace_in_file(xml_file, fstr, rstr) for fstr, rstr in fstr_rstr.items()]
    sycode = 'calo14'
    xml_file = os.path.join(basedir, sycode, sycode+'_pts_trans_ubw_meta.xml')
    [replace_in_file(xml_file, fstr, rstr) for fstr, rstr in fstr_rstr.items()]

    return

def change_pr14_xmls(basedir):
    # Parker River
    sycode = 'pr14'
    # morph points - no Z error field in DCpts and DTpts
    xml_file = os.path.join(basedir, sycode, sycode+'_DC_DT_SLpts_meta.xml')
    fstr = "It is reported in the field 'xxx-morph z_err-xxx'."
    rstr = ""
    replace_in_file(xml_file, fstr, rstr)

    return

def change_mon14_xmls(basedir):
    # Monomoy
    sycode = 'mon14'
    # morph points - no Z error field in DCpts and DTpts
    xml_file = os.path.join(basedir, sycode, sycode+'_DC_DT_SLpts_meta.xml')
    fstr = "It is reported in the field 'xxx-morph z_err-xxx'."
    rstr = ""
    replace_in_file(xml_file, fstr, rstr)

    # shoreline
    xml_file = os.path.join(basedir, sycode, sycode+'_shoreline_inletLines_meta.xml')
    fstr = "Manually digitize a straight line that bisects MHW where the seaward shoreline meets a tidal inlet"
    rstr = "Manually digitize a straight line that bisects MHW where the Atlantic Ocean shoreline meets the Nantucket Sound or backbarrier inlet"
    replace_in_file(xml_file, fstr, rstr)
    fstr = "seaward face"
    rstr = "Atlantic Ocean side"
    replace_in_file(xml_file, fstr, rstr)
    fstr = "inland face"
    rstr = "Nantucket Sound side"
    replace_in_file(xml_file, fstr, rstr)

    # _pts_trans_ubw_meta
    xml_file = os.path.join(basedir, sycode, sycode+'_pts_trans_ubw_meta.xml')
    fstr = "the inland side"
    rstr = "the western side"
    replace_in_file(xml_file, fstr, rstr)
    fstr = "back-barrier and oceanside shorelines"
    rstr = "easternmost and westernmost shorelines"
    replace_in_file(xml_file, fstr, rstr)
    fstr = "only the most seaward portion"
    rstr = "only the island portion adjacent to the Atlantic Ocean"
    replace_in_file(xml_file, fstr, rstr)
    fstr = "most seaward"
    rstr = "segment adjacent to the Atlantic Ocean."
    replace_in_file(xml_file, fstr, rstr)
    fstr = "less than or equal to 2\.5 m"
    rstr = "less than or equal to 3 m"
    replace_in_file(xml_file, fstr, rstr)

    # DisOcean used both front and back shorelines
    xml_file = os.path.join(basedir, sycode, 'Mon14_DisOcean.tif.xml')
    fstr = "to the ocean, with the ocean boundary being the mean high water \(MHW\) ocean shoreline, according to lidar captured in 2014."
    rstr = "to the outermost shoreline of the island. The island shoreline was derived from lidar captured in 2014 at the mean high water (MHW) adjacent to the Atlantic Ocean and the mean tidal level (MTL) adjacent to Nantucket Sound (see mon14_shoreline.shp in larger work)."
    replace_in_file(xml_file, fstr, rstr)
    fstr = "The portion of this shoreline adjacent to the open ocean, which is the only component of the shoreline relevant to the present dataset, was originally derived from mean high water \(MHW\) shoreline points \(mon14_SLpts\.shp in larger work; 13CNT05_morphology\.csv in Doran and others, 2017\)\. These shoreline points were QA/QC'd in ArcMap and edited in MATLAB\."
    rstr = "The shoreline segment adjacent to the open ocean was originally derived from mean high water (MHW) shoreline points (mon14_SLpts.shp in larger work; 13CNT05_morphology.csv in Doran and others, 2017). These shoreline points were QA/QC'd in ArcMap and edited in MATLAB. The MTL shoreline along Nantucket Sound was extracted from the DEM with less thorough QA/QC."
    replace_in_file(xml_file, fstr, rstr)
    fstr = "Horizontal accuracy is inherited from the edges of the shoreline polygons \(mon14_shoreline\.shp in the larger work\) adjacent to the open ocean, which were derived from the shoreline points \(mon14_SLpts\.shp in larger work\)\. Ocean-facing segments of the shoreline polygons are accurate to about 5 m\."
    rstr = "Horizontal accuracy is inherited from the edges of the shoreline polygons (mon14_shoreline.shp in the larger work), which were partly derived from the shoreline points (mon14_SLpts.shp in larger work). Ocean-facing segments of the shoreline polygons are accurate to about 5 m and sound-facing segments are assumed accurate within 25 m."
    replace_in_file(xml_file, fstr, rstr)
    fstr = """In an Edit session in ArcGIS, we used the ‘Cut Polygons’ tool to manually clip the beach polygon so that only the portion of the polygon on the ocean-facing side of the barrier remained\. The mean high water \(MHW\) shoreline points \(mon14_SLpts\.shp in larger work\) were referenced to identify the extent of the ocean-facing portion of the beach\. For these purposes, this clipped beach area from the MHW shoreline seaward to the edge of the study area was considered the ocean boundary\.\s*Using the ‘Euclidean Distance’ tool, we created a raster layer with a 5x5 m cell size that measured the straight-line distance from each cell within the study area to the closest cell in the clipped beach polygon \(considered the ocean boundary\)\. Cells landward of the MHW shoreline received a positive distance to ocean value and those seaward of the MHW shoreline received a value of 0 m\."""
    rstr = """Unlike at other sites, the full beach area from the island shoreline seaward to the edge of the study area was considered the ocean boundary.\n\nUsing the ‘Euclidean Distance’ tool, we created a raster layer with a 5x5 m cell size that measured the straight-line distance from each cell within the study area to the closest cell in the beach polygon (considered the ocean boundary). Cells landward of the shoreline received a positive distance to ocean value and those seaward of the MHW shoreline received a value of 0 m."""
    replace_in_file(xml_file, fstr, rstr)

    return

def change_ri14_xmls(basedir):
    # Rhode Island
    sycode = 'ri14'
    # Apply to all RI files
    fstr = "Rhode Island, RI" # Make sure this is case-sensitive
    rstr = "Rhode Island National Wildlife Refuge, RI"
    replace_in_filelist(os.path.join(basedir, sycode, '**.xml'), fstr, rstr)
    fstr = "<placekey>Rhode Island</placekey>\s*<placekey>RI"
    rstr = "<placekey>RI"
    replace_in_filelist(os.path.join(basedir, sycode, '**.xml'), fstr, rstr)

    # morph points
    xml_file = os.path.join(basedir, sycode, sycode+'_DC_DT_SLpts_meta.xml')
    fstr = "The NAVD88 elevation of MHW is xxx 0.22, 0.29, 0.36 m  for the region encompassing Rhode Island \(Weber and others, 2005\)."
    rstr = "The Rhode Island coast is separated into three zones with different MHW elevations as follows: 0.29 m NAVD88 from Connecticut to Napatree Point (transects with sort_ID from 1 to 117); 0.22 m NAVD88 from Napatree Point to Point Judith (transects with sort_ID from 118 to 725); and 0.36 m NAVD88 (transects with sort_ID from 726 to 824) from Point Judith to Massacchusetts (Weber and others, 2005). The field 'MHW' in the shoreline points (ri14_SLpts) indicates the MHW offset used to position the given point along the processing transect."
    replace_in_file(xml_file, fstr, rstr)

    # Elevation
    xml_file = os.path.join(basedir, sycode, sycode+'_ElevMHW.tif.xml')
    fstr = "In Raster Calculator in ArcToolbox, we subtracted the mean high water \(MHW\) offset \(xxx 0.22, 0.29, 0.36\) for the Rhode Island study area, as previously determined by Weber and others \(2005\)\."
    rstr = "We created a mean high water (MHW) surface by assigning the following MHW values to cells in the following zones: 0.29 m NAVD88 from Connecticut to Napatree Point; 0.22 m NAVD88 from Napatree Point to Point Judith; and 0.36 m NAVD88 from Point Judith to Massacchusetts (Weber and others, 2005). We then subtracted this 'correction' surface from the DEM (5 m resolution) to get MHW-corrected elevation."
    replace_in_file(xml_file, fstr, rstr)

    # pts_trans
    xml_file = os.path.join(basedir, sycode, sycode+'_pts_trans_ubw_meta.xml')
    fstr = "calculated by Weber and others \(2005\) for the area\."
    rstr = "calculated by Weber and others (2005).\n\nThe Rhode Island coast is separated into three zones with different MHW elevations as follows: 0.29 m NAVD88 from Connecticut to Napatree Point (transects with sort_ID from 1 to 117); 0.22 m NAVD88 from Napatree Point to Point Judith (transects with sort_ID from 118 to 725); and 0.36 m NAVD88 (transects with sort_ID from 726 to 824) from Point Judith to Massacchusetts (Weber and others, 2005)."
    replace_in_file(xml_file, fstr, rstr)
    fstr = """ri14_pts\.csv, part 1"""
    rstr = "MHW datum for Rhode Island study sites: The Rhode Island coast is separated into three zones with different MHW elevations as follows: 0.29 m NAVD88 from Connecticut to Napatree Point (transects with sort_ID from 1 to 117); 0.22 m NAVD88 from Napatree Point to Point Judith (transects with sort_ID from 118 to 725); and 0.36 m NAVD88 (transects with sort_ID from 726 to 824) from Point Judith to Massacchusetts (Weber and others, 2005). The field 'MHW' in the transects (ri_trans.shp) indicates the MHW offset along the given transect.\n\nri14_pts.csv, part 1"
    replace_in_file(xml_file, fstr, rstr)
    fstr = "\(xxx 0\.22, 0\.29, 0\.36 m based on Weber and others, 2005\)"
    rstr = "(see note on MHW datum above)"
    replace_in_file(xml_file, fstr, rstr)
    # uBW in _pts_trans_ubw_meta
    fstr = "respectively\.\s*Distance to inlet:"
    rstr = """respectively.\n\nTransects 56–70 were assigned fill values (-99999) for uBW and uBH because the configuration of the oceanside shoreline caused them to incorrectly be associated with morphology points along a different shoreline.\n\nDistance to inlet:"""
    replace_in_file(xml_file, fstr, rstr)

    # Shoreline
    xml_file = os.path.join(basedir, sycode, sycode+'_shoreline_inletLines_meta.xml')
    fstr = "Sturdivant, 2019\) with a MHW elevation of xxx 0\.22, 0\.29, 0\.36 m NAVD88, calculated for the area by Weber and others \(2005\)\."
    rstr = "Sturdivant, 2019). Although the Rhode Island study area included three MHW elevation values (Weber and others, 2005), the median value (0.29 m) was used as the MWH elevation for the full site when creating the shoreline polygon. This was counteracted in subsequent steps by snapping the polygon to the shoreline points."
    replace_in_file(xml_file, fstr, rstr)
    fstr = "The dataset contains \d* polygons.\s*</procdesc>"
    rstr = "The dataset contains 10 polygons.\n\nSome portions of the Rhode Island site are located on the mainland, which prevents the data from representing a back-barrier shoreline. To address this, the so-called back-barrier shoreline was clipped to a straight line roughly parallel and about 250 m from the shore polygons. If an inland waterbody occurred about 250 m from the shore, then the back-barrier shoreline was clipped to run through the waterbody.</procdesc>"
    replace_in_file(xml_file, fstr, rstr)

    return

def change_cg14_xmls(basedir):
    # Coast Guard
    sycode = 'cg14'
    # Shoreline
    xml_file = os.path.join(basedir, sycode, sycode+'_shoreline_inletLines_meta.xml')
    fstr = "The dataset contains \d* polygons\.\s*</procdesc>"
    rstr = "The dataset contains 4 polygons.\n\nSome portions of the Coast Guard site are located on the mainland, which prevents the data from representing a back-barrier shoreline. To address this, the so-called back-barrier shoreline was clipped to a straight line roughly parallel to and about 250 m from the shore polygons. If an inland waterbody occurred about 250 m from the shore, then the back-barrier shoreline was clipped to run through the waterbody.</procdesc>"
    replace_in_file(xml_file, fstr, rstr)
    return

def change_smi14_xmls(basedir):
    # smi14 - sort_ID values are out of order
    sycode = 'smi14'
    xml_file = os.path.join(basedir, sycode, sycode+'_pts_trans_ubw_meta.xml')
    # Find and replace
    fstr = "using the ArcGIS Spatial Sort tool in spatial increments\."
    rstr = "using the ArcGIS Spatial Sort tool in spatial increments. At Smith Island, these sort_ID values are not all consecutive along the shoreline."
    replace_in_file(xml_file, fstr, rstr)
    fstr = ",' which orders transects sequentially \(from south to north\) along the shoreline\. Transects are spaced alongshore"
    rstr = ".' At Smith Island, these sort_ID values are not ordered sequentially along the shore, unlike at other sites. Transects are spaced alongshore"
    replace_in_file(xml_file, fstr, rstr)
    fstr = "dentifier that orders transects sequentially along the shoreline"
    rstr = "dentifier"
    replace_in_file(xml_file, fstr, rstr)
    return

def change_wre14_xmls(basedir):
    # Wreck
    sycode = 'wre14'
    # Shoreline
    xml_file = os.path.join(basedir, sycode, sycode+'_pts_trans_ubw_meta.xml')
    fstr = "Transects are the base features for wre14_pts\.csv and wre14_ubw\.tif\."
    rstr = "Transects are the base features for wre14_pts.csv and wre14_ubw.tif. Transects have an unusual distribution at Wreck Island. The southern end of the island is bifurcated, with shoreline points present on both the shoreline adjacent to the ocean and the more inland eastward shoreline. To retain as much information as possible, transects were added orthogonal to the inland shoreline section."
    replace_in_file(xml_file, fstr, rstr)

    fstr = "back to the NASC transects\. ID"
    rstr = "back to the NASC transects. Transects have an unusual distribution at Wreck Island. The southern end of the island is bifurcated, with shoreline points present on both the shoreline adjacent to the ocean and the more inland westward shoreline. To retain as much information as possible, transects were added orthogonal to the inland shoreline section. ID"
    replace_in_file(xml_file, fstr, rstr)
    return

#%%
"""
## Execute
The master copy of the template spreadsheet is the Google Doc. Before running,
download it and change the csvfile variable below to the correct pathname.

How to execute:
1. Optionally duplicate the data folder. This code won't touch the data. It will save backup copies of the XMLs and then overwrite them.
2. Download the template table as CSV and save it in the basedir. Update the paths below.
3. Run the code below.

The code:
1. Creates a backup_xmls directory and saves a copy of the csv file there.
2. Parses the CSV to a DF.
3. Renames directories to the sycode in the template table that exactly matches the full name of Site, State, Year
"""
# Initialize variables
basedir = r"/Volumes/stor/Projects/DeepDive/5_datarelease_packages/vol2/release_v4"
backup_dir = os.path.join(basedir, "xxx_backup_xmls")
template_dir = r"/Volumes/stor/Projects/DeepDive/5_datarelease_packages/template_development/vol2_v1/templates"
csvfname = "metadata values - DD vol2 - Sheet1.csv"
csvfpath = os.path.join(basedir, csvfname)
browsedir = r'/Volumes/stor/Projects/DeepDive/5_datarelease_packages/vol2/browse'
sb_dir = basedir+'_forSB'

#%% Save copy of csv file (templating spreadsheet) in backup dir
backup_prerun = os.path.join(backup_dir, '{}_prerun'.format(datetime.now().strftime("%Y%m%d")))
os.makedirs((backup_prerun), exist_ok=True)
shutil.copy2(csvfpath, backup_prerun)

# Get values from CSV
valuesdf = pd.read_csv(csvfpath, header=0, index_col='templated_value', dtype='str')#, names=['templated_value', sycode])

#%% Rename directories to the siteyear codes. Requires exact match.
# from full 'Site, State, Year' name (site, state abbr, year) to the sycode
rename_sycode_dirs(basedir, valuesdf, False)

#%% Run the process -
# For every site-year, copy and rename the template files, then replace the fill values from the spreadsheet
perform_backup = True
remaining_fills = pd.DataFrame(columns=['file', 'fill_count'])
for sycode in valuesdf.columns:
    # Back up existing XML files and copy template
    backup_xmls(basedir, sycode, backup_prerun, perform_backup, verbose=False)
    # Copy template files into sycode directory
    copytree(template_dir, os.path.join(basedir, sycode))
    # Rename template XMLs to match the site-year.
    xmllist = rename_xmls(basedir, sycode, valuesdf, verbose=False)
    print("{}: {} XML files ".format(sycode, len(xmllist)))
    #% Run find and replace to apply to all xml files in list
    for infile in xmllist:
        relpath = os.path.relpath(infile, basedir)
        ct_fills = find_replace_dfvalues(infile, valuesdf, sycode, verbose=False)
        if ct_fills > 0:
            remaining_fills = remaining_fills.append({'file':relpath, 'fill_count':ct_fills}, ignore_index=True)

print("{} files still have fill values:".format(len(remaining_fills)))
print(remaining_fills)

#%% Make "manual" changes to files
change_asis14_xmls(basedir) # Assateague
change_assa14_xmls(basedir) # Assawoman - add Wallops Island to keywords in all XMLs
change_NC_xmls(basedir) # North Carolina sites
change_pr14_xmls(basedir) # Parker River
change_mon14_xmls(basedir) # Monomoy
change_ri14_xmls(basedir) # Rhode Island
change_cg14_xmls(basedir) # Coast Guard
change_wre14_xmls(basedir)
change_smi14_xmls(basedir)

# CHECK THIS
searchpath = os.path.join(basedir, '**/**_pts_trans_ubw_meta.xml')
# pts
# Change Bslope definition to match Doran? Explain negative value.
fstr = "Slope of foreshore at the shoreline point nearest to the transects within 25 m"
rstr = "Beach slope calculated between dune toe and shoreline (NAVD88) at the shoreline point nearest to the transect. A negative value indicates decreasing elevation from dune toe to shoreline"
replace_in_filelist(searchpath, fstr, rstr)

# Explain negative value in uBW and uBH (rare circumstance where the elevation of dune toe or armoring is lower than MHW; rare circumstance where dune toe or armoring was found seaward of the MHW shoreline)
fstr = "where beach width cannot be calculated because input values are missing or the calculation criteria are not met\."
rstr = "where beach width cannot be calculated because input values are missing or the calculation criteria are not met. A negative value indicates that the elevation of the identified top of beach feature is below the MHW elevation."
replace_in_filelist(searchpath, fstr, rstr)

# pts
fstr = "where beach height cannot be calculated because input values are missing or the calculation criteria are not met\."
rstr = "where beach height cannot be calculated because input values are missing or the calculation criteria are not met. A negative value indicates that the identified top of beach feature is seaward of the MHW shoreline."
replace_in_filelist(searchpath, fstr, rstr)

# Transects
fstr = "<attrlabl>Shape_Length</attrlabl>"
rstr = "<attrlabl>Shape_Leng</attrlabl>"
replace_in_filelist(searchpath, fstr, rstr)


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
        print("{}: removed {} XMLs because they weren't matched.".format(sycode, len(leftovers)))

#%% Check remaining XMLs for xxx fill values
remaining_fills = pd.DataFrame(columns=['file', 'fill_count'])
ct = 0
for sycode in valuesdf.columns:
    # List xmls
    xmllist = glob.glob(os.path.join(basedir, sycode, '*', '**.xml'), recursive=True)
    # Check all XML files for fills
    for infile in xmllist:
        ct += 1
        relpath = os.path.relpath(infile, basedir)
        # Read file
        with io.open(infile, 'r', encoding='utf-8') as f:
            s = f.read()
        # Count fills
        ct_fills = len(re.findall('(?i)xxx', s))
        if ct_fills > 0:
            remaining_fills = remaining_fills.append({'file':relpath, 'fill_count':ct_fills}, ignore_index=True)
if len(remaining_fills) > 0:
    print(remaining_fills)
else:
    print("{} files checked; no 'xxx' fills remaining.".format(ct))

#%% Duplicate set of browse graphics into site directories
# Delete all PNGs in the basedir file tree
pnglist = glob.glob(os.path.join(basedir, '**/*.[pP][nN][gG]'), recursive=True)
for fp in pnglist:
    os.remove(fp)
# For each PNG file, copy it into every directory with a matching name in the basedir file tree
browselist = glob.glob(os.path.join(browsedir, '*.[pP][nN][gG]'))
for fpath in browselist:
    # List matching directories
    fname = os.path.basename(fpath)
    searchstr = fname.split('_')[0]
    matchdirs = glob.glob(os.path.join(basedir, '*/{}*'.format(searchstr)))
    print("Copying {} into {} folders matching '{}'".format(fname, len(matchdirs), searchstr))
    for matchdir in matchdirs:
        shutil.copy(fpath, matchdir)

#%% Backup the resulting XMLs
backup_postrun = os.path.join(backup_dir, '{}_postrun'.format(datetime.now().strftime("%Y%m%d")))
os.makedirs((backup_postrun), exist_ok=True)
xmllist = glob.glob(os.path.join(basedir, '[!x]*/**/*.[xX][mM][lL]'))#, recursive=True)
for fp in xmllist:
    shutil.copy(fp, backup_postrun)

#%% Save postrun backup of XMLs to zip file
shutil.make_archive(r'/Volumes/stor/Projects/DeepDive/5_datarelease_packages/vol2/archive/xmls_{}'.format(os.path.basename(backup_postrun)), 'zip', backup_postrun)

#%% Change the directory names (back-and-forth between code and full name)
# Map the sycodes to the full names
rename_sycode_dirs(basedir, valuesdf)

#%% Replace the DBF files for the shorelines after I deleted the Shape_Leng attribute
copy_modified_files(basedir, sb_dir, searchstr='**/*shoreline.dbf')
copy_modified_files(basedir, sb_dir, searchstr='**/*browse.png', override_limit=True)
# copy_modified_files(basedir, sb_dir, searchstr='**/*.xml')

#%% Either replace XML files in SB dir or create new SB dir
ct = 0
if os.path.exists(sb_dir):
    # Overwrite XML files in the SB dir with the updated XMLs
    print("Replacing XML files in directory {}...".format(os.path.basename(sb_dir)))
    xmllist = glob.glob(os.path.join(basedir, '[!x]*/**/*.[xX][mM][lL]'))#, recursive=True)
    for xml in xmllist:
        new_path = glob.glob(os.path.join(sb_dir, '**', os.path.basename(xml)), recursive=True)
        if new_path:
            shutil.copy(xml, new_path[0])
            ct += 1
    for xml_file in glob.glob(os.path.join(sb_dir, '**/*.xml_orig'), recursive=True):
        os.remove(xml_file)
    print('Replaced {} files.'.format(ct))
else:
    print("Directory {} doesn't exist so duplicating release package...".format(os.path.basename(sb_dir)))
    # Duplicate the dataset for ScienceBase upload
    try:
        shutil.rmtree(sb_dir, ignore_errors=True)
    except:
        pass
    shutil.copytree(basedir, sb_dir, ignore=shutil.ignore_patterns('xxx_*', '*Sheet1.csv'))
    print("Created duplicate of release package for upload to ScienceBase.")
    # If the sub-parent page structure is already created, and you don't want to
    # re-create it, you'll need to copy the dict files from the last parent upload
    # folder into the new one.


#%% delete directories in SB dirtree that match the names of directories in the original
# xmllist = glob.glob(os.path.join(basedir, '[!x]*/**/*.[xX][mM][lL]'))#, recursive=True)
# for xml in xmllist:
#     orig_dirname = os.path.basename(os.path.dirname(xml))
#     for d in glob.glob(os.path.join(basedir+'_4sb', '**', orig_dirname), recursive=True):
#         shutil.rmtree(d, ignore_errors=True)

#%% Backup the XMLs resulting from SB upload
# backup_postSB = os.path.join(backup_dir, '{}_postSB'.format(datetime.now().strftime("%Y%m%d")))
# os.makedirs((backup_postSB), exist_ok=True)
# xmllist = glob.glob(os.path.join(sb_dir, '[!x]*/**/*.[xX][mM][lL]'))#, recursive=True)
# for fp in xmllist:
#     shutil.copy(fp, backup_postSB)
# shutil.make_archive(r'/Volumes/stor/Projects/DeepDive/5_datarelease_packages/vol2/archive/xmls_{}'.format(os.path.basename(backup_postSB)), 'zip', backup_postSB)
