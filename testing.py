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
import pysb # Install on OSX with "pip install -e git+https://my.usgs.gov/stash/scm/sbe/pysb.git#egg=pysb" # This package is under development so I recommend that you reinstall regularly to get the latest version. Currently: 1.3.6
import os
import glob
from lxml import etree
import json
import pickle
import sys
#sb_auto_dir = os.path.dirname(os.path.realpath(__file__))
sb_auto_dir = os.path.dirname(os.path.realpath('sb_automation.py'))
sys.path.append(sb_auto_dir) # Add the script location to the system path just to make sure
from autoSB import *
from config_autoSB import *

# This does not wipe the page:
# Can a JSON item only include the 'id' for sb.updateSbItem(item) to work?
#new_values['child_id'] = "58877ff3e4b02e34393c0d5d"
#if overwrite_datapages:
data_id = "58877ff3e4b02e34393c0d5d"
data_item = {}
data_item['id'] = data_id
data_item['title'] = "Title 3"
#data_item['title'] = data_title
new_item = sb.update_item(data_item)
new_item["dates"][1]["dateString"]

for (root, dirs, files) in os.walk(parentdir):
	for d in dirs:
		xmllist = glob.glob(os.path.join(root,d,'*.xml'))

xml_file = xmllist[0]

new_item = sb.upload_files_and_upsert_item(data_item, [xml_file]) # this updated the SB item when I uploaded an XML with a different name
new_item["dates"][0]["dateString"]

sb.replace_file(xml_file, data_item)

sb.replace_file(xml_file, new_item) # Replace requires a complete JSON item - can't have only the ID, like for upload_files_and_upsert_item()

new_item = sb.upload_file_to_item(data_item, xml_file)

data_item = upload_shp(sb, data_item, xml_file, replace=True, verbose=verbose)
