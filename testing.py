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

landing_item = sb.get_item(landing_id)
child_id = '582ca4b7e4b04d580bd3790b'
child_item = sb.get_item(child_id)

inherit_topdown(sb, landing_id, subparent_inherits, data_inherits, verbose=True)

def qc_pages(sb, top_id, qcfields, deficient_pages=[], verbose=False):
	# Given an SB ID, pass on selected fields to all descendants; doesn't look for parents
	for cid in sb.get_child_ids(top_id):
		citem = sb.get_item(cid)
		deficient = qc(sb, citem, qcfields, verbose)
		deficient_pages.append(deficient)
		try:
			deficient_pages = qc_pages(sb, cid, qcfields, deficient_pages, verbose)
		except Exception as e:
			print("EXCEPTION: {}".format(e))
	return deficient_pages


qcfields = ['citation', 'contacts', 'body', 'relatedItems', 'facets']
pagelist = qc_pages(sb, landing_id, qcfields, verbose=True)



# Revise the XML, except for the values created by SB
# Recursively list all XML files in parentdir
xmllist = []
for root, dirs, files in os.walk(parentdir):
	for d in dirs:
		xmllist += glob.glob(os.path.join(root,d,'*.xml'))
