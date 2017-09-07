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

#%% Temp: upload images.zip
xml_file = '/Volumes/ThunderVant/Projects/UAS_BlackBeach/Publishing/Data_publishing/data_release_4upload_3/Field Data (images and reference points)/bb20160318_UAS_images_meta.xml'
d = 'Field Data (images and reference points)'

if not sb.is_logged_in():
	print('Logging back in...')
	try:
		sb = pysb.SbSession(env=None).login(useremail,password)
	except NameError:
		sb = pysb.SbSession(env=None).loginc(useremail)

# get JSON item for parent page
landing_item = sb.get_item(landing_id)
#print("CITATION: {}".format(landing_item['citation'])) # print to QC citation
# make dictionary of ID and URL values to update in XML
new_values = {'landing_id':landing_item['id'], 'doi':dr_doi}
if 'pubdate' in locals():
	new_values['pubdate'] = pubdate
if 'find_and_replace' in locals():
	new_values['find_and_replace'] = find_and_replace
if 'metadata_additions' in locals():
	new_values['metadata_additions'] = metadata_additions
if "metadata_replacements" in locals():
	new_values['metadata_replacements'] = metadata_replacements
if "remove_fills" in locals():
	new_values['remove_fills'] = remove_fills

with open(os.path.join(parentdir,'dir_to_id.json'), 'r') as f:
	dict_DIRtoID = json.load(f)
with open(os.path.join(parentdir,'id_to_json.json'), 'r') as f:
	dict_IDtoJSON = json.load(f)
with open(os.path.join(parentdir,'parentID_to_childrenIDs.txt'), 'rb') as f:
	dict_PARtoCHILDS = pickle.load(f)


parentid = dict_DIRtoID[d]
new_values['doi'] = dr_doi if 'dr_doi' in locals() else get_DOI_from_item(flexibly_get_item(sb, parentid))
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
