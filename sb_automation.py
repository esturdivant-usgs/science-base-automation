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
import datetime
import sys
from pathlib import Path
try:
	sb_auto_dir = os.path.dirname(os.path.realpath(__file__))
except:
	sb_auto_dir = os.path.dirname(os.path.realpath('sb_automation.py'))
sys.path.append(sb_auto_dir) # Add the script location to the system path just to make sure this works.
from autoSB import *
from config_autoSB import *


#%% Initialize SB session
"""
sb = log_in(useremail)
"""
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

#%% Work with landing page and XML
"""
Work with landing page and XML
"""
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
	if os.path.isfile(previewImage):
		imagefile = previewImage
	else:
		print("{} does not exist.".format(previewImage))
else:
	imagefile = False

if update_landing_page: #this block is not necessary; remove from simplified version
	# Check for metadata and image files in landing directory
	landing_item = update_landing_page(parentdir, parent_xml, imagefile, new_values)

#%% Create SB page structure
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
#%%
if not update_subpages and not os.path.isfile(os.path.join(parentdir,'id_to_json.json')):
	print("id_to_json.json file is not in parent directory, so we will perform update_subpages routine.")
	update_subpages = True
if update_subpages:
	# Initialize dictionaries that will store relationships: directories/file:ID, ID:JSON item, parentID:childIDs
	# org_map = {'DIRtoID': {os.path.basename(parentdir): landing_id}, # Initialize top dir/file:ID entry to dict
	# 			'IDtoJSON': {landing_id: landing_item}, # Initialize with landing page
	# 			'PARtoCHILDS': {}}
	dict_DIRtoID = {os.path.basename(parentdir): landing_id} # Initialize top dir/file:ID entry to dict
	dict_IDtoJSON = {landing_id: landing_item} # Initialize with landing page
	dict_PARtoCHILDS = {} # Initialize empty parentID:childIDs dictionary
	# Create sub-parent container pages. If pages already exist, they will not be recreated.
	for (root, dirs, files) in os.walk(parentdir):
		for dirname in dirs:
			# parent_id = org_map['DIRtoID'][os.path.basename(root)] # get ID for parent
			parent_id = dict_DIRtoID[os.path.basename(root)] # get ID for parent
			#print('Finding/creating page for "{}" in "{}" (ID: {})'.format(dirname, os.path.basename(root), parent_id))
			subpage = find_or_create_child(sb, parent_id, dirname, verbose=verbose) # get JSON for subpage based on parent ID and dirname
			if 'previewImage' in subparent_inherits and "imagefile" in locals():
				subpage = sb.upload_file_to_item(subpage, imagefile)
			# store values in dictionaries
			# org_map['DIRtoID'][dirname] = subpage['id']
			# org_map['IDtoJSON'][subpage['id']] = subpage
			# org_map['PARtoCHILDS'].setdefault(parent_id, set()).add(subpage['id'])
			dict_DIRtoID[dirname] = subpage['id']
			dict_IDtoJSON[subpage['id']] = subpage
			dict_PARtoCHILDS.setdefault(parent_id, set()).add(subpage['id'])
	# Save dictionaries
	# with open(os.path.join(parentdir,'org_map.json'), 'w') as f:
	# 	json.dump(org_map, f)
	with open(os.path.join(parentdir,'dir_to_id.json'), 'w') as f:
		json.dump(dict_DIRtoID, f)
	with open(os.path.join(parentdir,'id_to_json.json'), 'w') as f:
		json.dump(dict_IDtoJSON, f)
	with open(os.path.join(parentdir,'parentID_to_childrenIDs.txt'), 'ab+') as f:
		pickle.dump(dict_PARtoCHILDS, f)
else: # Import pre-created dictionaries if all SB pages exist
	# with open(os.path.join(parentdir,'org_map.json'), 'r') as f:
	# 	org_map = json.load(f)
	with open(os.path.join(parentdir,'dir_to_id.json'), 'r') as f:
		dict_DIRtoID = json.load(f)
	with open(os.path.join(parentdir,'id_to_json.json'), 'r') as f:
		dict_IDtoJSON = json.load(f)
	with open(os.path.join(parentdir,'parentID_to_childrenIDs.txt'), 'rb') as f:
		dict_PARtoCHILDS = pickle.load(f)

#%% Create and populate data pages
"""
Create and populate data pages
Inputs: parent directory, landing page ID, dictionary of new values (new_values)
For each XML file in each directory, create a data page, revise the XML, and upload the data to the new page
"""
if verbose:
	print('---\nChecking log in information...')
#sb = log_in(useremail) #FIXME
if not sb.is_logged_in():
	print('Logging back in...')
	try:
		sb = pysb.SbSession(env=None).login(useremail,password)
	except NameError:
		sb = pysb.SbSession(env=None).loginc(useremail)

if verbose:
	print('Checking for directory: ID dictionary...')
# if not "org_map" in locals():
# 	with open(os.path.join(parentdir,'org_map.json'), 'r') as f:
# 		org_map = json.load(f)
if not "dict_DIRtoID" in locals():
	with open(os.path.join(parentdir,'dir_to_id.json'), 'r') as f:
		dict_DIRtoID = json.load(f)

# List XML files
xmllist = glob.glob(os.path.join(parentdir, '**/*.xml'), recursive=True)

#%%
# For each XML file in each directory, create a data page, revise the XML, and upload the data to the new page
if verbose:
	print('\n---\nWalking through XML files to create/find a data page, update the XML file, and upload the data...')
cnt = 0

for xml_file in xmllist:
	cnt += 1
	if not sb.is_logged_in():
		print('Logging back in...')
		try:
			sb = pysb.SbSession(env=None).login(useremail, password)
		except NameError:
			sb = pysb.SbSession(env=None).loginc(useremail)
	# 1. GET VALUES from XML
	dirname = os.path.basename(os.path.split(xml_file)[0])
	parentid = dict_DIRtoID[dirname]
	new_values['doi'] = dr_doi if 'dr_doi' in locals() else get_DOI_from_item(flexibly_get_item(sb, parentid))
	# Get title of data by parsing XML
	data_title = get_title_from_data(xml_file)
	# Create (or find) data page based on title
	data_item = find_or_create_child(sb, parentid, data_title, verbose=verbose)
	# If pubdate in new_values, set it as the date for the SB page
	try:
		data_item["dates"][0]["dateString"]= new_values['pubdate'] #FIXME add this to a function in a more generalized way?
	except:
		pass
	# 2. MAKE UPDATES
	# Update XML
	if update_XML:
		# add SB UID to be updated in XML
		new_values['child_id'] = data_item['id']
		# Look for browse graphic
		searchstr = xml_file.split('.')[0].split('_meta')[0] + '*browse*'
		try:
			browse_file = glob.glob(searchstr)[0]
			new_values['browse_file'] = browse_file.split('/')[-1]
		except Exception as e:
			print("{}\nWe weren't able to upload a browse image for page {}.".format(e, dirname))
		# Make the changes to the XML based on the new_values dictionary
		update_xml(xml_file, new_values, verbose=verbose) # new_values['pubdate']
	# Upload data to ScienceBase
	if update_data:
		# Upload all files in dir that match basename of XML file. Record list of files that were not uploaded because they were above the threshold set by max_MBsize
		data_item, bigfiles1 = upload_files_matching_xml(sb, data_item, xml_file, max_MBsize=max_MBsize, replace=True, verbose=verbose)
		if bigfiles1:
			if not 'bigfiles' in locals():
				bigfiles = []
			bigfiles += bigfiles1
	# Upload XML to ScienceBase
	elif update_XML:
		# If XML was updated, but data was not uploaded, replace only XML.
		try:
			sb.replace_file(xml_file, data_item) # Does not update SB page to match metadata
		except e:
			print('Retry with update_data = True. pysb.replace_file() is not working for this use. Returned: \n'+e)
	if 'previewImage' in data_inherits and "imagefile" in locals():
		data_item = sb.upload_file_to_item(data_item, imagefile)
	if verbose:
		now_str = datetime.datetime.now().strftime("%H:%M:%S on %Y-%m-%d")
		print('Completed {} out of {} xml files at {}.\n'.format(cnt, len(xmllist), now_str))
	# store values in dictionaries
	# org_map['DIRtoID'][xml_file] = data_item['id']
	# org_map['IDtoJSON'][data_item['id']] = data_item
	# org_map['PARtoCHILDS'].setdefault(parentid, set()).add(data_item['id'])
	dict_DIRtoID[xml_file] = data_item['id']
	dict_IDtoJSON[data_item['id']] = data_item
	dict_PARtoCHILDS.setdefault(parentid, set()).add(data_item['id'])

#%% Pass down fields from parents to children
print("\n---\nPassing down fields from parents to children...")
inherit_topdown(sb, landing_id, subparent_inherits, data_inherits, verbose=verbose)

#%% BOUNDING BOX
if update_extent:
	print("\nGetting extent of child data for parent pages...")
	set_parent_extent(sb, landing_id, verbose=verbose)

# Preview Image
if add_preview_image_to_all:
	# org_map['IDtoJSON'] = upload_all_previewImages(sb, parentdir, org_map['DIRtoID'], org_map['IDtoJSON'])
	dict_IDtoJSON = upload_all_previewImages(sb, parentdir, dict_DIRtoID, dict_IDtoJSON)

# Save dictionaries
# with open(os.path.join(parentdir,'org_map.json'), 'w') as f:
# 	json.dump(org_map, f)
with open(os.path.join(parentdir,'dir_to_id.json'), 'w') as f:
	json.dump(dict_DIRtoID, f)
with open(os.path.join(parentdir,'id_to_json.json'), 'w') as f:
	json.dump(dict_IDtoJSON, f)
with open(os.path.join(parentdir,'parentID_to_childrenIDs.txt'), 'ab+') as f:
	pickle.dump(dict_PARtoCHILDS, f)

#%% QA/QC
if quality_check_pages:
	qcfields_dict = {'contacts':4, 'webLinks':0, 'facets':1}
	print('Checking that each page has: \n{}'.format(qcfields_dict))
	pagelist = check_fields2_topdown(sb, landing_id, qcfields_dict, verbose=False)


now_str = datetime.datetime.now().strftime("%H:%M:%S on %Y-%m-%d")
print('\n{}\nAll done! View the result at {}'.format(now_str, landing_link))
if 'bigfiles' in locals():
	if len(bigfiles) > 0:
		print("These files were too large to upload so you'll need to use the large file uploader: {}".format(bigfiles))
