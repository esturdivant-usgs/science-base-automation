# -*- coding: utf-8 -*-
"""
Please see README.md (https://github.com/esturdivant-usgs/science-base-automation) for detailed instructions.

sb_automation.py

By: Emily Sturdivant, esturdivant@usgs.gov

OVERVIEW: Script creates child pages that mimic the directory structure and
populates the pages using a combination of fields from the landing page and the metadata.
Directories within home must be named as desired for each child page.
Currently, the script creates a new child page for each metadata file.

REQUIRES: pysb, lxml, config_autoSB.py, autoSB.py
To install pysb with pip: pip install -e git+https://my.usgs.gov/stash/scm/sbe/pysb.git#egg=pysb
"""

#%% Import packages
import sciencebasepy as pysb
import os
import glob
from lxml import etree
import json
import pickle
from datetime import datetime
import sys
import shutil
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
if delete_all_subpages:
    if not update_subpages:
        print('WARNING: You chose not to update subpages, but also to delete all child pages. Both are not possible so we will remove and create them.')
    print("Deleting all child pages of landing page...")
    print(delete_all_children(sb, landing_id))
    # Try new get_ancestor_ids() and delete_items() to remove all children
    # ancestor_ids = sb.get_ancestor_ids(landing_id)
    # sb.delete_items(ancestor_ids)
    # Remove any files from the landing page
    landing_item = remove_all_files(sb, landing_id, verbose=verbose)
    update_subpages = True

# Set imagefile
if 'previewImage' in subparent_inherits:
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

#%% Change folder name to match XML title
"""
Change folder name to match XML title
"""
print('\n---\nRenaming folders to match XML title...')
rename_dirs_from_xmls(parentdir)

#%% Create SB page structure
"""
Create SB page structure: nested child pages following directory hierarchy
Inputs: parent directory, landing page ID
This one should overwrite the entire data release (excluding the landing page).
"""
# Log into SB if it's timed out
sb = log_in(useremail, password)
mapfile_dir2id = os.path.join(stash_dir, 'dir_to_id.json')
os.makedirs(os.path.dirname(mapfile_dir2id), exist_ok=True)

# If there's no id_to_json.json file available, we need to create the subpage structure.
if not update_subpages and not os.path.isfile(mapfile_dir2id):
    print("dir_to_id.json file is not in parent directory, so we will perform update_subpages routine.")
    update_subpages = True

if update_subpages:
    print('\n---\nCreating sub-pages...')
    dict_DIRtoID = setup_subparents(sb, parentdir, landing_id, imagefile)
    # Save dictionaries
    with open(mapfile_dir2id, 'w') as f:
        json.dump(dict_DIRtoID, f)
else: # Import pre-created dictionaries if all SB pages exist
    with open(mapfile_dir2id, 'r') as f:
        dict_DIRtoID = json.load(f)

#%% Create and populate data pages
"""
Create and populate data pages
Inputs: parent directory, landing page ID, dictionary of new values (new_values)
For each XML file in each directory, create a data page, revise the XML, and upload the data to the new page
"""
print('\n---\nWorking with XML files...')
# Log into SB if it's timed out
sb = log_in(useremail, password)
valid_ids = sb.get_ancestor_ids(landing_id)

#%% Work with XMLs
# Optionally remove or restore original XML files.
if remove_original_xml:
    print('Removing all .xml_orig files in {} tree.'.format(os.path.basename(parentdir)))
    remove_files(parentdir, pattern='**/*.xml_orig')
elif restore_original_xml:
    if not update_XML:
        print('WARNING: You selected to restore original XMLs, but not to update XMLs. This may cause problems.')
    restore_original_xmls(parentdir)
    print('Restored .xml_orig files in {} tree.'.format(os.path.basename(parentdir)))

# add DOI to be updated in XML
if 'dr_doi' in locals():
    new_values['doi'] = dr_doi
else:
    new_values['doi'] = get_DOI_from_item(flexibly_get_item(sb, landing_id))

# Optionally update all XML files from SB values
if update_XML:
    update_all_xmls(parentdir, new_values, sb, dict_DIRtoID, verbose=True)

#%% Upload data
if update_data:
    # For each XML file in each directory, upload the data to the new page
    if verbose:
        print('\n---\nWalking through XML files to upload the data...')
    cnt = 0
    xmllist = glob.glob(os.path.join(parentdir, '**/*.xml'), recursive=True)
    xmllist = xmllist[start_xml_idx:]
    for xml_file in xmllist:
        cnt += 1
        print("File {}: {}".format(cnt + start_xml_idx, xml_file))
        # Get SB page ID from the XML
        datapageid = get_pageid_from_xmlpath(xml_file, sb=sb, dict_DIRtoID=dict_DIRtoID, valid_ids=valid_ids, parentdir=parentdir, verbose=False)
        # Log into SB if it's timed out
        sb = log_in(useremail, password)
        data_item = sb.get_item(datapageid)
        # Upload data to ScienceBase
        # Update publication date in item
        try:
            # If pubdate in new_values, set it as the date for the SB page
            data_item["dates"][0]["dateString"]= new_values['pubdate'] #FIXME add this to a function in a more generalized way?
        except:
            pass
        # Upload all files in directory to the SB page
        data_item, bigfiles1 = upload_files(sb, data_item, xml_file, max_MBsize=max_MBsize, replace=True, verbose=verbose)
        # Record files that were not uploaded because they were above the max_MBsize threshold
        if bigfiles1:
            if not 'bigfiles' in locals():
                bigfiles = []
            bigfiles += bigfiles1
        # Log into SB if it's timed out
        sb = log_in(useremail, password)
        if 'previewImage' in data_inherits and "imagefile" in locals():
            data_item = sb.upload_file_to_item(data_item, imagefile)
        if verbose:
            now_str = datetime.now().strftime("%H:%M:%S on %Y-%m-%d")
            print('Completed {} out of {} total xml files at {}.\n'.format(start_xml_idx+cnt, start_xml_idx+len(xmllist), now_str))
        # store values in dictionaries
        dict_DIRtoID[xml_file] = data_item['id']

print("\n---\nRunning universal updates (browse graphics and udpated XMls)...")

# Preview Image
if add_preview_image_to_all:
    upload_all_previewImages(sb, parentdir, dict_DIRtoID)

#%% Update SB preview image from the uploaded files.
if update_XML:
    sb = log_in(useremail, password)
    update_all_browse_graphics(sb, parentdir, landing_id, valid_ids)

#%% Check for and upload XMLs that have been modified since last upload.
sb = log_in(useremail, password)
upload_all_updated_xmls(sb, parentdir, valid_ids)

#%% Pass down fields from parents to children
print("\n---\nPassing down fields from parents to children...")
inherit_topdown(sb, landing_id, subparent_inherits, data_inherits, verbose=verbose)

#%% BOUNDING BOX
if update_extent:
    print("\nGetting extent of child data for parent pages...")
    set_parent_extent(sb, landing_id, verbose=verbose)

# Save dictionaries
with open(mapfile_dir2id, 'w') as f:
    json.dump(dict_DIRtoID, f)

#%% QA/QC
if 'qcfields_dict' in locals():
    qcfields_dict = {'contacts':7, 'webLinks':0, 'facets':1}
    print('Checking that each page has: \n{}'.format(qcfields_dict))
    pagelist = check_fields2_topdown(sb, landing_id, qcfields_dict, verbose=False)

now_str = datetime.now().strftime("%H:%M:%S on %m/%d/%Y")
print('\n{}\nAll done! View the result at {}'.format(now_str, landing_link))
if 'bigfiles' in locals():
    if len(bigfiles) > 0:
        print("These files were too large to upload so you'll need to use the large file uploader:")
        print(*bigfiles, sep = "\n")

#%% Backup the XMLs resulting from SB upload
today = datetime.now().strftime("%Y%m%d")
xmlstash = os.path.join(stash_dir, 'output_xmls_{}'.format(today))
os.makedirs((xmlstash), exist_ok=True)
print('Saving output XMLs to {}'.format(xmlstash))
for fp in glob.glob(os.path.join(parentdir, '[!x]*/**/*.[xX][mM][lL]')):
    shutil.copy(fp, xmlstash)
shutil.make_archive(xmlstash, 'zip', xmlstash)
