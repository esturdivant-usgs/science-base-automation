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
# sb_auto_dir = os.path.dirname(os.path.realpath(__file__))
sb_auto_dir = '/Users/esturdivant/GitHub/science-base-automation'
# sb_auto_dir = os.path.dirname(os.path.realpath('testing.py'))
sys.path.append(sb_auto_dir) # Add the script location to the system path just to make sure
from autoSB import *
from config_autoSB import *

parentdir = r'/Users/esturdivant/Desktop/GOM_final' # OSX

# Inherit non-existent webLinks
# landing_item = sb.get_item(landing_id)
#
# child_id = '582ca4a8e4b04d580bd378f1'
# child_item = sb.get_item(child_id)

# Python 3:
# ixmllist = glob.iglob(os.path.join(parentdir,'**','*.xml'), recursive=True)

# Revise the XML, except for the values created by SB
# Recursively list all XML files in parentdir
xmllist = []
for root, dirs, files in os.walk(parentdir):
	for d in dirs:
		xmllist += glob.glob(os.path.join(root,d,'*.xml'))



xml_file = xmllist[6]

update_xml(xml_file, locals(), verbose=True)

find_and_replace_from_dict(xml_file, find_n_replace)


for rstr, flist in find_n_replace.iteritems():
	for fstr in flist:
		find_and_replace_text(xml_file, fstr, rstr)




fr_list = list()
for rstr, flist in find_n_replace.iteritems():
	if type(flist) is str:
		flist = [flist]
	for fstr in flist:
		fr_list.append((fstr, rstr))

f1 = open(xml_file, 'r')
f2 = open(xml_file+'.tmp', 'w')
for line in f1:
	for fstr, rstr in fr_list:
		line = line.replace(fstr, rstr)
	f2.write(line)
f1.close()
f2.close()


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

remove_fills = {'./idinfo/crossref':['AUTHOR', 'Meredith Kratzmann']}

for xml_file in xmllist[3:7]:
	tree = etree.parse(xml_file)
	metadata_root = tree.getroot()
	if "remove_fills" in locals():
		[remove_xml_element(metadata_root, path, ftext) for path, ftext in remove_fills.items()]
	tree.write(xml_file)

if not "landing_id" in locals():
	try:
		landing_id = os.path.split(landing_link)[1] # get ID for parent page from link
	except:
		print('Either the ID (landing_id) or the URL (landing_link) of the ScienceBase landing page must be specified in config_autoSB.py.')
delete_all_children(sb, landing_id)
