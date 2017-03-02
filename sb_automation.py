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
sb_auto_dir = os.path.dirname(os.path.realpath(__file__))
#sb_auto_dir = os.path.dirname(os.path.realpath('sb_automation.py'))
sys.path.append(sb_auto_dir) # Add the script location to the system path just to make sure this works.
from autoSB import *
from config_autoSB import *

"""
#%% Initialize SB session
sb = log_in(useremail)
"""
# #%% Find landing page
# if not "landing_id" in locals():
# 	try:
# 		landing_id = os.path.split(landing_link)[1] # get ID for parent page from link
# 	except:
# 		print('Either the ID (landing_id) or the URL (landing_link) of the ScienceBase landing page must be specified in config_autoSB.py.')
# get JSON item for parent page
landing_item = sb.get_item(landing_id)
#print("CITATION: {}".format(landing_item['citation'])) # print to QC citation
# make dictionary of ID and URL values to update in XML
new_values = {'landing_id':landing_item['id'], 'doi':dr_doi}
if 'pubdate' in locals():
	new_values['pubdate'] = pubdate
if 'metadata_additions' in locals():
	new_values['metadata_additions'] = metadata_additions
if "metadata_replacements" in locals():
	new_values['metadata_replacements'] = metadata_replacements
if "remove_fills" in locals():
	new_values['remove_fills'] = remove_fills

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

if not update_subpages and not os.path.isfile(os.path.join(parentdir,'id_to_json.json')):
	print("id_to_json.json file is not in parent directory, so we will perform update_subpages routine.")
	update_subpages = True
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
			subpage = find_or_create_child(sb, parent_id, dirname, verbose=verbose) # get JSON for subpage based on parent ID and dirname
			subpage = inherit_SBfields(sb, subpage, subparent_inherits)
			if 'previewImage' in subparent_inherits and "imagefile" in locals():
				subpage = sb.upload_file_to_item(subpage, imagefile)
			# store values in dictionaries
			dict_DIRtoID[dirname] = subpage['id']
			dict_IDtoJSON[subpage['id']] = subpage
			dict_PARtoCHILDS.setdefault(parent_id, set()).add(subpage['id'])
	# Save dictionaries
	with open(os.path.join(parentdir,'dir_to_id.json'), 'w') as f:
		json.dump(dict_DIRtoID, f)
	with open(os.path.join(parentdir,'id_to_json.json'), 'w') as f:
		json.dump(dict_IDtoJSON, f)
	with open(os.path.join(parentdir,'parentID_to_childrenIDs.txt'), 'ab+') as f:
		pickle.dump(dict_PARtoCHILDS, f)
else: # Import pre-created dictionaries if all SB pages exist
	with open(os.path.join(parentdir,'dir_to_id.json'), 'r') as f:
		dict_DIRtoID = json.load(f)
	with open(os.path.join(parentdir,'id_to_json.json'), 'r') as f:
		dict_IDtoJSON = json.load(f)
	with open(os.path.join(parentdir,'parentID_to_childrenIDs.txt'), 'rb') as f:
		dict_PARtoCHILDS = pickle.load(f)


"""
Create and populate data pages
Inputs: parent directory, landing page ID, dictionary of new values (new_values)
For each XML file in each directory, create a data page, revise the XML, and upload the data to the new page
"""
if verbose:
	print('checking log in information...')
#sb = log_in(useremail) #FIXME
if not sb.is_logged_in():
	print('Logging back in...')
	try:
		sb = pysb.SbSession(env=None).login(useremail,password)
	except NameError:
		sb = pysb.SbSession(env=None).loginc(useremail)

if verbose:
	print('Checking for directory: ID dictionary...')
if not "dict_DIRtoID" in locals():
	with open(os.path.join(parentdir,'dir_to_id.json'), 'r') as f:
		dict_DIRtoID = json.load(f)

# Count XML files
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

# For each XML file in each directory, create a data page, revise the XML, and upload the data to the new page
if verbose:
	print('\n---\nWalking through XML files to create/find a data page, update the XML file, and upload the data...')
cnt = 0
for root, dirs, files in os.walk(parentdir):
	for d in dirs:
		xmllist = glob.glob(os.path.join(root,d,'*.xml'))
		for xml_file in xmllist:
			cnt += 1
			if not sb.is_logged_in():
				print('Logging back in...')
				try:
					sb = pysb.SbSession(env=None).login(useremail,password)
				except NameError:
					sb = pysb.SbSession(env=None).loginc(useremail)
			# Get values
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
			# Make updates
			# Update XML
			if update_XML: 								# Update XML file to include new child ID and DOI
				new_values['child_id'] = data_item['id'] 		# add SB UID to values that will be updated in XML
				update_xml(xml_file, new_values, verbose=verbose) # new_values['pubdate']
				find_and_replace_text(xml_file, 'http:', 'https:') 			# Replace 'http:' with 'https:'
				find_and_replace_text(xml_file, 'dx.doi.org', 'doi.org') 	# Replace 'dx.doi.org' with 'doi.org'
			# Upload to ScienceBase
			if update_data: # Upload data files (FIXME: currently only shapefile)
				#if metadata.findall(formname_tagpath)[0].text == 'Shapefile':
				data_item = upload_shp(sb, data_item, xml_file, replace=True, verbose=verbose)
			elif update_XML: # If XML was updated, but data was not uploaded, replace only XML.
				try:
					sb.replace_file(xml_file, data_item)
				except e:
					print('Retry with update_data = True. pysb.replace_file() is not working for this use. Returned: \n'+e)
				# sb.upload_files_and_upsert_item(data_item, [xml_file])
			# Pass parent fields on to child
			data_item = inherit_SBfields(sb, data_item, data_inherits, verbose=verbose)
			if verbose:
				now_str = datetime.datetime.now().strftime("%H:%M:%S on %Y-%m-%d")
				print('Completed {} out of {} xml files at {}.\n'.format(cnt, xml_cnt, now_str))
			# store values in dictionaries
			dict_DIRtoID[xml_file] = data_item['id']
			dict_IDtoJSON[data_item['id']] = data_item
			dict_PARtoCHILDS.setdefault(parentid, set()).add(data_item['id'])

#%% Pass down fields from parents to children
# print("\nPassing down fields from parents to children...")
# universal_inherit(sb, top_id, data_inherits)

#%% BOUNDING BOX
print("\nGetting extent of child data for parent pages...")
set_parent_extent(sb, landing_id, verbose=verbose)

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

print('All done! View the result at {}'.format(landing_link))
