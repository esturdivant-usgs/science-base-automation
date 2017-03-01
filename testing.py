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
sb_auto_dir = os.path.dirname(os.path.realpath(__file__))
# sb_auto_dir = '/Users/esturdivant/GitHub/science-base-automation'
# sb_auto_dir = os.path.dirname(os.path.realpath('testing.py'))
sys.path.append(sb_auto_dir) # Add the script location to the system path just to make sure
from autoSB import *
from config_autoSB import *

parentdir = r'/Users/esturdivant/Desktop/GOM_final_xtraCrossrefs' # OSX

# Python 3:
# ixmllist = glob.iglob(os.path.join(root,'**','*.xml'), recursive=True)

# Revise the XML, except for the values created by SB
# Recursively list all XML files in parentdir
xmllist = []
for root, dirs, files in os.walk(parentdir):
	for d in dirs:
		xmllist += glob.glob(os.path.join(root,d,'*.xml'))
# Change each XML file
for xml_file in xmllist:
	find_and_replace_text(xml_file, 'http:', 'https:') 		    # Replace 'http:' with 'https:'
	find_and_replace_text(xml_file, 'dx.doi.org', 'doi.org') 	# Replace 'dx.doi.org' with 'doi.org'
	tree = etree.parse(xml_file)
	metadata_root = tree.getroot()
	if "remove_fills" in locals():
		[remove_xml_element(metadata_root, path, fill_text) for path, fill_text in remove_fills.items()]
	if "metadata_additions" in locals():
		[add_element_to_xml(metadata_root, new_elem, containertag) for containertag, new_elem in metadata_additions.items()]
	if "metadata_replacements" in locals():
		[replace_element_in_xml(metadata_root, new_elem, containertag) for containertag, new_elem in metadata_replacements.items()]
	tree.write(xml_file)
