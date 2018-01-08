# -*- coding: utf-8 -*-
"""
testing.py

By: Emily Sturdivant, esturdivant@usgs.gov
Last modified: 1/10/17

OVERVIEW: Script creates child pages that mimic the directory structure and
populates the pages using a combination of fields from the landing page and the metadata.
Directories within home must be named as desired for each child page.
Currently, the script creates a new child page for each metadata file.

REQUIRES: pysb, lxml, config_autoSB.py, autoSB.py
To install pysb with pip: pip install -e git+https://my.usgs.gov/stash/scm/sbe/pysb.git#egg=pysb

ALTERNATIVE: only create child page from metadata if data files also exist...
...or if there are multiple metadata files in the directory.
"""
#%% Import packages
import pysb # Install on OSX with "pip install -e git+https://my.usgs.gov/stash/scm/sbe/pysb.git#egg=pysb"
import os
import glob
from lxml import etree
import json
import pickle
import datetime
import sys
try:
    sb_auto_dir = os.path.dirname(os.path.realpath(__file__))
except:
    sb_auto_dir = os.path.dirname(os.path.realpath('sb_automation.py'))
    sb_auto_dir = r'/Users/esturdivant/GitHub/science-base-automation'
sys.path.append(sb_auto_dir) # Add the script location to the system path just to make sure this works.
from autoSB import *
from config_autoSB import *
from Tkinter import *



#%%
landing_id
subparent_inherits
data_inherits
inherit_topdown(sb, landing_id, subparent_inherits, data_inherits, verbose=verbose)


#%% Upload all XML files without updating them.
parentdir = r'/Volumes/ThunderVant/Projects/UAS_BlackBeach/Publishing/Data_publishing/data_release_revisedSept' # OSX Desktop
with open(os.path.join(parentdir,'dir_to_id.json'), 'r') as f:
	dict_DIRtoID = json.load(f)

replace_files_by_ext(sb, parentdir, dict_DIRtoID, match_str='*.xml') # only replaces the file if the file is already on the data page.

#%% Temp: upload images.zip
xml_file = '/Volumes/ThunderVant/Projects/UAS_BlackBeach/Publishing/Data_publishing/data_release_revisedSept/Field Data (images and reference points)/bb20160318_UAS_images_meta.xml'
d = 'Field Data (images and reference points)'

if not sb.is_logged_in():
	print('Logging back in...')
	try:
		sb = pysb.SbSession(env=None).login(useremail,password)
	except NameError:
		sb = pysb.SbSession(env=None).loginc(useremail)

with open(os.path.join(parentdir,'dir_to_id.json'), 'r') as f:
	dict_DIRtoID = json.load(f)

parentid = dict_DIRtoID[d]
# Create (or find) new data page based on title in XML
data_title = get_title_from_data(xml_file) # get title from XML
data_item = find_or_create_child(sb, parentid, data_title, verbose=verbose) # Create (or find) data page based on title
# Upload to ScienceBase
data_item, bigfiles1 = upload_files_matching_xml(sb, data_item, xml_file, max_MBsize=2000, replace=True, verbose=verbose)



#%% DEM

xml_file = '/Volumes/ThunderVant/Projects/UAS_BlackBeach/Publishing/Data_publishing/data_release_4upload_3/SfM products (point cloud, orthomosaic, and DEM)/bb20160318_sfm_dem_meta.xml'
d = 'SfM products (point cloud, orthomosaic, and DEM)'
if not sb.is_logged_in():
	print('Logging back in...')
	try:
		sb = pysb.SbSession(env=None).login(useremail,password)
	except NameError:
		sb = pysb.SbSession(env=None).loginc(useremail)
parentid = dict_DIRtoID[d]
new_values['doi'] = dr_doi if 'dr_doi' in locals() else get_DOI_from_item(flexibly_get_item(sb, parentid))
# Create (or find) new data page based on title in XML
data_title = get_title_from_data(xml_file) # get title from XML
data_item = find_or_create_child(sb, parentid, data_title, verbose=verbose) # Create (or find) data page based on title
try: #FIXME: add this to a function in a more generalized way?
    data_item["dates"][0]["dateString"]= new_values['pubdate']
    #data_item["dates"][1]["dateString"]= {"type": "Info", "dateString": "2016", "label": "Time Period"} # What should the time period value reflect?
except:
    pass
# Upload to ScienceBase
data_item, bigfiles1 = upload_files_matching_xml(sb, data_item, xml_file, max_MBsize=2000, replace=True, verbose=verbose)

# sb, xml_file, directory, dict_DIRtoID, new_values,

#%%QC
if quality_check_pages:
	qcfields_dict = {'contacts':4, 'webLinks':0, 'facets':1}
	print('Checking that each page has: \n{}'.format(qcfields_dict))
	pagelist = check_fields2_topdown(sb, landing_id, qcfields_dict, verbose=False)

landing_item = sb.get_item(landing_id)
child_id = '58b89028e4b01ccd5500c263'
child_item = sb.get_item(child_id)

# Revise the XML, except for the values created by SB
# Recursively list all XML files in parentdir
xmllist = []
for root, dirs, files in os.walk(parentdir):
	for d in dirs:
		xmllist += glob.glob(os.path.join(root,d,'*.xml'))

#%% Count XML files and modify metadata
xmllist = []
for root, dirs, files in os.walk(parentdir):
	for d in dirs:
		xmllist += glob.glob(os.path.join(root,d,'*.xml'))
xml_cnt = len(xmllist)
# for xml_file in xmllist:
# 	tree = etree.parse(xml_file)
# 	metadata_root = tree.getroot()
# 	if "remove_fills" in locals():
# 		[remove_xml_element(metadata_root, path, ftext) for path, ftext in remove_fills.items()])
# 	if "metadata_additions" in locals():
# 		[add_element_to_xml(metadata_root, new_elem, containertag) for containertag, new_elem in metadata_additions.items()]
# 	if "metadata_replacements" in locals():
# 		[replace_element_in_xml(metadata_root, new_elem, containertag) for containertag, new_elem in metadata_replacements.items()]
# 	tree.write(xml_file)
# 	find_and_replace_text(xml_file, 'http:', 'https:') 		    # Replace 'http:' with 'https:'
# 	find_and_replace_text(xml_file, 'dx.doi.org', 'doi.org') 	# Replace 'dx.doi.org' with 'doi.org'

xml_file = '/Volumes/ThunderVant/Projects/UAS_BlackBeach/Publishing/Data_publishing/data_release_revisedSept_sb/SfM products (point cloud, orthomosaic, and DEM)/bb20160318_sfm_orthomosaic_meta.xml'
os.path.basename(os.path.dirname(xml_file))
cnt = 0
# for xml_file in xmllist:
cnt += 1
if not sb.is_logged_in():
    print('Logging back in...')
    try:
        sb = pysb.SbSession(env=None).login(useremail,password)
    except NameError:
        sb = pysb.SbSession(env=None).loginc(useremail)
d = os.path.basename(os.path.dirname(xml_file))
parentid = dict_DIRtoID[d]
new_values['doi'] = dr_doi if 'dr_doi' in locals() else get_DOI_from_item(flexibly_get_item(sb, parentid))
# Create (or find) new data page based on title in XML
data_title = get_title_from_data(xml_file) # get title from XML
data_item = find_or_create_child(sb, parentid, data_title, verbose=verbose) # Create (or find) data page based on title
try:
    data_item["dates"][0]["dateString"]= new_values['pubdate'] #FIXME add this to a function in a more generalized way?
    #data_item["dates"][1]["dateString"]= {"type": "Info", "dateString": "2016", "label": "Time Period"} # What should the time period value reflect?
except:
    pass
# 2. MAKE UPDATES
# Update XML
if update_XML:
    # Check for Browse graphic
    dataname = xml_file.split('.')[0]
    dataname = dataname.split('_meta')[0]
    browse_file = glob.glob(dataname + '*browse*')[0]
    if len(browse_file) > 0:
        new_values['browse_file'] = browse_file
    # add SB UID to be updated in XML
    new_values['child_id'] = data_item['id']
    update_xml(xml_file, new_values, verbose=verbose) # new_values['pubdate']
# Upload to ScienceBase
if update_data:
    # Upload all files in dir that match basename of XML file
    # data_item = upload_data(sb, data_item, xml_file, replace=True, verbose=verbose)
    data_item, bigfiles1 = upload_files_matching_xml(sb, data_item, xml_file, max_MBsize=max_MBsize, replace=True, verbose=verbose)
    if bigfiles1:
        if not 'bigfiles' in locals():
            bigfiles = []
        else:
            bigfiles += bigfiles1
elif update_XML:
    # If XML was updated, but data was not uploaded, replace only XML.
    try:
        sb.replace_file(xml_file, data_item) # Does not update SB page to match metadata
    except e:
        print('Retry with update_data = True. pysb.replace_file() is not working for this use. Returned: \n'+e)
    # sb.upload_files_and_upsert_item(data_item, [xml_file])
if verbose:
    now_str = datetime.datetime.now().strftime("%H:%M:%S on %Y-%m-%d")
    print('Completed {} out of {} xml files at {}.\n'.format(cnt, xml_cnt, now_str))


"""
Tkinter learning
"""
# Button widget with counter
counter = 0
def counter_label(label):
  def count():
    global counter
    counter += 1
    label.config(text=str(counter))
    label.after(1000, count)
  count()

root = Tk() # Tk root widget initializes Tkinter. Appears as window with title bar after calling root.mainloop()
root.title("Counting Seconds")
label = Label(root, fg="green")
label.pack()
counter_label(label)
button = Button(root, text='Stop', width=25, command=root.destroy)
button.pack()

# Entry widget
master = Tk()
Label(master, text="First Name").grid(row=0)
Label(master, text="Last Name").grid(row=1)

e1 = Entry(master)
e2 = Entry(master)

e1.grid(row=0, column=1)
e2.grid(row=1, column=1)

mainloop( )
