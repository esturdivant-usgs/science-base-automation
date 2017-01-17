# -*- coding: utf-8 -*-
"""
config_autoSB.py

By: Emily Sturdivant, esturdivant@usgs.gov
Last modified: 1/10/17

OVERVIEW: Configuration file for sb_automation.py
REQUIRES: autoSB.py, pysb, lxml
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

"""
Input variables
"""
# ***REQUIRED***
# SB username (should be entire USGS email):
useremail = 'esturdivant@usgs.gov'
# SB password. If commented out, you will be prompted for your password each time you run the script.
#password = 
# URL of data release landing page (e.g. 'https://www.sciencebase.gov/catalog/item/__item_ID__'):
landing_link = "https://www.sciencebase.gov/catalog/item/58055f50e4b0824b2d1c1ee7" # real page
landing_link = "https://www.sciencebase.gov/catalog/item/580a2b32e4b0f497e7906380" # testing page
# Path to local top directory of data release (equivalent to landing page):
# If this is a server, it should be mounted and visible in your Volumes. Then it is referenced by '/Volumes/__volume_name__'
# The volume name should be the name of the directory on the server, rather than the server itself. Check this by looking at the volumes mounted on your computer. In 
parentdir = r'/Users/esturdivant/Desktop/SE_ATLANTIC' # OSX
parentdir = "c:/Users/esturdivant/Desktop/SE_ATLANTIC" # WINDOWS
# DOI of data release (e.g. '10.5066/F78P5XNK'):
dr_doi = "10.5066/F74X55X7"
# Image file (with path) to be used as preview image. If commented out, the preview image will be ignored.
#previewImage = r'/Users/esturdivant/Desktop/SE_ATLANTIC/NASCP_SEAtlantic.png'
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
update_subpages = True # default: True. False to save time if SB pages already exist
update_XML = True # default: True. False to save time if XML already has the most up-to-date values.
update_data = True # default: True. False to save time if up-to-date data files have already been uploaded.
add_preview_image_to_all = False # default: False. True to put the same preview image (file specified above) on every page in the data release.

replace_subpages = False # default: False. True to delete all child pages before running. Not necessary. Use cautiously; deleted items seem to linger in the SB memory so it is best to run the function delete_all_children(sb, landing_id) a few minutes before running the script.


# update_landing_page = False # default: True. True if values on the landing page should be updated from XML file in the parent directory
# replace_subpages = False # default: False. True to delete all child pages before running. Not necessary. Use cautiously; deleted items seem to linger in the SB memory so it is best to run the function delete_all_children(sb, landing_id) a few minutes before running the script.
# update_subpages = False # default: True. False to save time if SB pages already exist
# update_XML = False # default: True. False to save time if XML already has the most up-to-date values.
# update_data = False # default: True. False to save time if up-to-date data files have already been uploaded.
# add_preview_image_to_all = True # default: False. True to put the same preview image (file specified above) on every page in the data release.
#

"""
Initialize
"""
#%% Initialize SB session
sb = log_in(useremail)
