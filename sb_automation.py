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
sys.path.append(os.path.dirname(os.path.realpath(__file__))) # Add the script location to the system path just to make sure this works.
from autoSB import *

from config_autoSB import *

"""
Input variables

# ***REQUIRED***
# SB username (should be entire USGS email):
useremail = 'esturdivant@usgs.gov'
# SB password. If commented out, you will be prompted for your password each time you run the script.
#password = 
# URL of data release landing page (e.g. 'https://www.sciencebase.gov/catalog/item/__item_ID__'):
landing_link = "https://www.sciencebase.gov/catalog/item/58055f50e4b0824b2d1c1ee7"
# Path to local top directory of data release (equivalent to landing page):
# If this is a server, it should be mounted and visible in your Volumes. Then it is referenced by '/Volumes/__volume_name__'
# The volume name should be the name of the directory on the server, rather than the server itself. Check this by looking at the volumes mounted on your computer. In 
parentdir = r'/Users/esturdivant/Desktop/SE_ATLANTIC'
# DOI of data release (e.g. '10.5066/F78P5XNK'):
dr_doi = "10.5066/F74X55X7"
# Image file (with path) to be used as preview image. If commented out, the preview image will be ignored.
previewImage = r'/Users/esturdivant/Desktop/SE_ATLANTIC/NASCP_SEAtlantic.png'
# The edition element in the metadata can be modified here.
#edition = '1.0'

# ***OPTIONAL***
# SB fields that will be populated from the XML file in the top directory, assuming an error-free XML is present. Default: citation, body, purpose. Note: body = abstract. Summary will automatically be created from body.
landing_fields_from_xml = ['citation','body','purpose']
# SB fields that will be copied (inherited) from the landing page to aggregate pages. Defaults: citation, body (which SB automatically harvests for the summary), purpose.
subparent_inherits = ['citation','body','purpose']
# SB fields data pages inherit from their immediate parent page. All other fields will be automatically populated from the XML. Defaults: citation, body.
data_inherits = ['citation', 'body']

update_landing_page = True # default: True. True if values on the landing page should be updated from XML file in the parent directory
replace_subpages = False # default: False. True to delete all child pages before running. Not necessary. Use cautiously; deleted items seem to linger in the SB memory so it is best to run the function delete_all_children(sb, landing_id) a few minutes before running the script.
update_subpages = True # default: True. False to save time if SB pages already exist
update_XML = True # default: True. False to save time if XML already has the most up-to-date values.
update_data = True # default: True. False to save time if up-to-date data files have already been uploaded.
add_preview_image_to_all = False # default: False. True to put the same preview image (file specified above) on every page in the data release.

"""
#Initialize
"""
#%% Initialize SB session
sb = log_in(useremail)
"""
#%% Find landing page
if landing_link:
	landing_id = os.path.split(landing_link)[1] # get ID for parent page from link
elif landing_id:
	landing_link = 'https://www.sciencebase.gov/catalog/item/{}'.format(landing_id)
# get JSON item for parent page
landing_item = sb.get_item(landing_id) 
print("CITATION: {}".format(landing_item['citation']))
new_values = {'new_id':landing_item['id'], 'doi':dr_doi, 'landing_link':landing_link}

"""
Work with landing page
"""
# Check for metadata and image files in landing directory
for f in os.listdir(parentdir):
	if f.lower().endswith('xml'):
		parent_xml = os.path.join(parentdir,f) # metadata file in landing directory = parent_xml
	if f.lower().endswith(('png','jpg','gif')):
		imagefile = os.path.join(parentdir,f)
	elif "previewImage" in locals():
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
		except Exception, e:
			print(e)
	if "parent_xml" in locals():
		if 'body' not in landing_item.keys():
			try: # update SB landing page with specific fields from XML
				landing_item = get_fields_from_xml(sb, landing_item, parent_xml, landing_fields_from_xml)
				landing_item=sb.updateSbItem(landing_item)
			except Exception, e:
				print(e)
	if "imagefile" in locals():
		try: # Add preview image to landing page
			landing_item = sb.upload_file_to_item(landing_item, imagefile)
		except Exception, e:
			print("Exception while trying to upload file {}: {}".format(imagefile, e))

"""
Create SB page structure: nested child pages following directory hierarchy
Inputs: parent directory, landing page ID
This one should overwrite the entire data release (excluding the landing page).
"""
# Remove all child pages
if replace_subpages: # If this is used, you may have to wait a long time before the removal takes full effect.
	delete_all_children(sb, landing_id)
	landing_item = remove_all_files(sb, landing_id)
if 'previewImage' in data_inherits:
	for f in os.listdir(parentdir):
		if f.lower().endswith(('png','jpg','gif')):
			imagefile = os.path.join(parentdir,f)
elif "previewImage" in locals():
	imagefile = previewImage
else:
	imagefile = False

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

if not sb.is_logged_in():
	print('Logging back in...')
	try:
		sb = pysb.SbSession(env=None).login(useremail,password)
	except NameError:
		sb = pysb.SbSession(env=None).loginc(useremail)

# Create and populate data pages
# For each XML file in each directory, create a data page, revise the XML, and upload the data to the new page
for (root, dirs, files) in os.walk(parentdir):
	for d in dirs:
		xmllist = glob.glob(os.path.join(root,d,'*.xml'))
		for xml_file in xmllist:
			# Get values
			parentid, parent_link, parent_item = flexibly_get_item(sb, dict_DIRtoID[d])
			if not dr_doi: # Get DOI link from parent_item
				dr_doi = get_DOI_from_item(parent_item)
			# Create (or find) new data page based on title in XML
			data_title = get_title_from_data(xml_file) # get title from XML
			print("TITLE: {}".format(data_title))
			data_item = find_or_create_child(sb, parentid, data_title, True) # Create (or find) data page
			if update_XML: # Update XML file to include new child ID and DOI
				new_values['directdownload_link'] = 'https://www.sciencebase.gov/catalog/file/get/{}'.format(data_item['id'])
				new_values['new_id'] = data_item['id']
				update_xml(xml_file, new_values)
			if update_data: # Upload data files (FIXME: currently only shapefile) #if metadata.findall(formname_tagpath)[0].text == 'Shapefile':
				data_item = upload_shp(sb, data_item, xml_file, replace=True, verbose=True)
			elif update_XML: # If XML was updated, but data was not uploaded, replace only XML.
				sb.replace_file(xml_file, data_item) # This function does not work well.
			# Pass parent fields on to child
			data_item = inherit_SBfields(sb, data_item, data_inherits)
			if 'previewImage' in data_inherits:
				try:
					data_item = sb.upload_file_to_item(data_item, imagefile)
				except Exception, e:
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
