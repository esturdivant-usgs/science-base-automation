# -*- coding: utf-8 -*-
"""
sb_automation.py

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
import sys
sb_auto_dir = os.path.dirname(os.path.realpath(__file__))
#sb_auto_dir = os.path.dirname(os.path.realpath('sb_automation.py'))
sys.path.append(sb_auto_dir) # Add the script location to the system path just to make sure this works.
from autoSB import *
from config_autoSB import *

"""
#%% Initialize SB session
sb = log_in(useremail)
"""
#%% Find landing page
if not "landing_id" in locals():
	try:
		landing_id = os.path.split(landing_link)[1] # get ID for parent page from link
	except:
		print('Either the ID (landing_id) or the URL (landing_link) of the ScienceBase landing page must be specified.')
# get JSON item for parent page
landing_item = sb.get_item(landing_id)
#print("CITATION: {}".format(landing_item['citation'])) # print to QC citation
# make dictionary of ID and URL values to update in XML
new_values = {'landing_id':landing_item['id'], 'doi':dr_doi}

"""
Work with landing page and XML
"""
# Check for metadata and image files in landing directory
#FIXME: this block is not necessary; remove from simplified version
for f in os.listdir(parentdir):
	if f.lower().endswith('xml'):
		parent_xml = os.path.join(parentdir,f) # metadata file in landing directory = parent_xml
	if f.lower().endswith(('png','jpg','gif')): # if there is a PNG, JPG, or GIF file
		imagefile = os.path.join(parentdir,f)
	elif "previewImage" in locals(): # only if there is not an image file in the parent directory, use the image specified during configuration
		if os.path.isfile(previewImage):
			imagefile = previewImage
		else:
			print("{} does not exist.".format(previewImage))
	else:
		print("Preview image not specified.")

if update_landing_page:
	#%% Populate landing page from metadata
	if "parent_xml" in locals():
		# Update XML file to include new parent ID and DOI
		parent_xml = update_xml(parent_xml, new_values)
		try: # upload XML to landing page
			landing_item = sb.upload_file_to_item(landing_item, parent_xml)
		except Exception as e:
			print(e)
	if "parent_xml" in locals():
		if 'body' not in landing_item.keys():
			try: # update SB landing page with specific fields from XML
				landing_item = get_fields_from_xml(sb, landing_item, parent_xml, landing_fields_from_xml)
				landing_item=sb.updateSbItem(landing_item)
			except Exception as e:
				print(e)
	if "imagefile" in locals():
		try: # Add preview image to landing page
			landing_item = sb.upload_file_to_item(landing_item, imagefile)
		except Exception as e:
			print("Exception while trying to upload file {}: {}".format(imagefile, e))

# Remove all child pages
if replace_subpages: # If this is used, you may have to wait a long time before the removal takes full effect.
	delete_all_children(sb, landing_id)
	landing_item = remove_all_files(sb, landing_id)
# Set imagefile
if 'previewImage' in data_inherits:
	for f in os.listdir(parentdir):
		if f.lower().endswith(('png','jpg','gif')):
			imagefile = os.path.join(parentdir,f)
elif "previewImage" in locals():
	imagefile = previewImage
else:
	imagefile = False

"""
Create SB page structure: nested child pages following directory hierarchy
Inputs: parent directory, landing page ID
This one should overwrite the entire data release (excluding the landing page).
"""
if not sb.is_logged_in():
	print('Logging back in...')
	try:
		sb = pysb.SbSession(env=None).login(useremail,password)
	except NameError:
		sb = pysb.SbSession(env=None).loginc(useremail)

if update_subpages:
	# Initialize dictionaries that will store relationships: directories/file:ID, ID:JSON item, parentID:childIDs
	dict_DIRtoID = {os.path.basename(parentdir): landing_id} # Initialize top dir/file:ID entry to dict
	dict_IDtoJSON = {landing_id: landing_item} # Initialize with landing page
	dict_PARtoCHILDS = {} # Initialize empty parentID:childIDs dictionary
	# Create sub-parent container pages. If pages already exist, they will not be recreated.
	for (root, dirs, files) in os.walk(parentdir):
		for dirname in dirs:
			parent_id = dict_DIRtoID[os.path.basename(root)] # get ID for parent
			#print('Finding/creating page for "{}" in "{}" (ID: {})'.format(dirname, os.path.basename(root), parent_id))
			subpage = find_or_create_child(sb, parent_id, dirname, skip_search=False, verbose=True) # get JSON for subpage based on parent ID and dirname
			subpage = inherit_SBfields(sb, subpage, subparent_inherits)
			if 'previewImage' in subparent_inherits and "imagefile" in locals():
				subpage = sb.upload_file_to_item(subpage, imagefile)
			# store values in dictionaries
			dict_DIRtoID[dirname] = subpage['id']
			dict_IDtoJSON[subpage['id']] = subpage
			dict_PARtoCHILDS.setdefault(parent_id, set()).add(subpage['id'])
else: # Import pre-created dictionaries if all SB pages exist
	with open(os.path.join(parentdir,'dir_to_id.json'), 'r') as f:
		dict_DIRtoID = json.load(f)
	with open(os.path.join(parentdir,'id_to_json.json'), 'r') as f:
		dict_IDtoJSON = json.load(f)
	with open(os.path.join(parentdir,'parentID_to_childrenIDs.txt'), 'rb') as f:
		dict_PARtoCHILDS = pickle.load(f)

"""
Create and populate data pages
Inputs: parent directory, landing page ID
For each XML file in each directory, create a data page, revise the XML, and upload the data to the new page
"""
if not sb.is_logged_in():
	print('Logging back in...')
	try:
		sb = pysb.SbSession(env=None).login(useremail,password)
	except NameError:
		sb = pysb.SbSession(env=None).loginc(useremail)

if not "dict_DIRtoID" in locals():
	with open(os.path.join(parentdir,'dir_to_id.json'), 'r') as f:
		dict_DIRtoID = json.load(f)

# For each XML file in each directory, create a data page, revise the XML, and upload the data to the new page
for (root, dirs, files) in os.walk(parentdir):
	for d in dirs:
		xmllist = glob.glob(os.path.join(root,d,'*.xml'))
		for xml_file in xmllist:
			# Get values
			dr_doi = dr_doi if 'dr_doi' in locals() else get_DOI_from_item(flexibly_get_item(sb, dict_DIRtoID[d]))
			# Create (or find) new data page based on title in XML
			parentid = dict_DIRtoID[d]
			data_title = get_title_from_data(xml_file) # get title from XML
			data_item = find_or_create_child(sb, parentid, data_title, skip_search=True, verbose=True) # Create (or find) data page based on title
			# Make updates
			if update_XML: # Update XML file to include new child ID and DOI
				find_and_replace_text(xml_file) # Replace 'http:' with 'https:'
				update_xml(xml_file, {'landing_id':landing_item['id'], 'doi':dr_doi, 'child_id':data_item['id']})
			if update_data: # Upload data files (FIXME: currently only shapefile) #if metadata.findall(formname_tagpath)[0].text == 'Shapefile':
				data_item = upload_shp(sb, data_item, xml_file, replace=True, verbose=True)
			elif update_XML: # If XML was updated, but data was not uploaded, replace only XML.
				sb.replace_file(xml_file, data_item) # This function does not work well.
			# Pass parent fields on to child
			data_item = inherit_SBfields(sb, data_item, data_inherits)
			if 'previewImage' in data_inherits:
				try:
					data_item = sb.upload_file_to_item(data_item, imagefile)
				except Exception as e:
					print(e)
			# store values in dictionaries
			dict_DIRtoID[xml_file] = data_item['id']
			dict_IDtoJSON[data_item['id']] = data_item
			dict_PARtoCHILDS.setdefault(parent_item['id'], set()).add(data_item['id'])

#%% Pass down fields from parents to children
# print("\nPassing down fields from parents to children...")
# universal_inherit(sb, top_id, data_inherits)

#%% BOUNDING BOX
print("\nGetting extent of child data for parent pages...")
set_parent_extent(sb, landing_id)

# Preview Image
if add_preview_image_to_all:
	dict_IDtoJSON = upload_all_previewImages(sb, parentdir, dict_DIRtoID, dict_IDtoJSON)

# Save dictionaries
with open(os.path.join(parentdir,'dir_to_id.json'), 'w') as f:
	json.dump(dict_DIRtoID, f)
with open(os.path.join(parentdir,'id_to_json.json'), 'w') as f:
	json.dump(dict_IDtoJSON, f)
with open(os.path.join(parentdir,'parentID_to_childrenIDs.txt'), 'ab+') as f:
	pickle.dump(dict_PARtoCHILDS, f)
