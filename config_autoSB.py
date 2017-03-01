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
#-----------------------
#   REQUIRED
#-----------------------
# SB username (should be entire USGS email):
useremail = 'esturdivant@usgs.gov'
# SB password. If commented out, you will be prompted for your password each time you run the script.
#password =

# URL of data release landing page (e.g. 'https://www.sciencebase.gov/catalog/item/__item_ID__'):
landing_link = "https://www.sciencebase.gov/catalog/item/58055f50e4b0824b2d1c1ee7" # real page - GOM
#landing_link = "https://www.sciencebase.gov/catalog/item/58868c92e4b0cad700058da1" # testing page

# Path to local top-level directory of data release (equivalent to landing page):
# OSX: If this is a server mounted and visible in your Volumes: r'/Volumes/[directory on server]'
parentdir = r'/Users/esturdivant/Desktop/SEATL_final' # OSX
#parentdir = "c:/Users/esturdivant/SE_ATLANTIC_0124" # WINDOWS

# DOI of data release (e.g. '10.5066/F78P5XNK'):
dr_doi = "10.5066/F74X55X7"

# Year of publication, if it needs to updated. Used as the date in citation publication date and the calendar date in time period of content.
pubdate = '2017'

# The edition element in the metadata can be modified here.
#edition = '1.0'

# Image file (with path) to be used as preview image. If commented out, the preview image will be ignored.
#previewImage = r'/Users/esturdivant/Desktop/SE_ATLANTIC/NASCP_SEAtlantic.png'

#-------------------------------------------------------------------------------
#   OPTIONAL - Page inheritance
#-------------------------------------------------------------------------------
# SB fields that will be copied (inherited) from landing page to sub-pages (subparents), which are different from data pages.
# Defaults: citation, contacts, body (='abstract' in XML; 'summary' in SB), purpose, webLinks
subparent_inherits = ['citation','contacts','body','purpose'] #'webLinks'

# SB fields that data pages inherit from their parent page. All other fields will be automatically populated from the XML.
# Defaults: citation, body.
data_inherits = ['citation','contacts', 'body'] # include ,'webLinks'?

# SB fields that will be populated from the XML file in the top directory, assuming an error-free XML is present.
# Note that body = abstract. The Summary item on SB will automatically be created from body.
# Default: [].
landing_fields_from_xml = []

#-------------------------------------------------------------------------------
# Time-saving options
#-------------------------------------------------------------------------------
# Default True:
update_subpages = True # False to save time if  SB pages already exist
update_XML      = True # False to save time if XML already has the most up-to-date values.
update_data     = True # False to save time if up-to-date data files have already been uploaded.
verbose         = True

# Default False:
add_preview_image_to_all = False # True to put the first image file encountered in a directory on its corresponding page
update_landing_page      = False # True if values on the landing page should be updated from XML file in the parent directory
replace_subpages         = False # True to delete all child pages before running. Not necessary. Use cautiously; deleted items seem to linger in the SB memory so it is best to run the function delete_all_children(sb, landing_id) a few minutes before running the script.

# ------------------------------------------------------------------------------
# Additions and replacements for metadata XML
# ------------------------------------------------------------------------------
# Add {container: new XML element} item to metadata_additions dictionary for each element to appended to the container element.
# Appending will not remove any elements.

# Example of a new cross reference:
new_crossref = """
    <crossref><citeinfo>
        <origin>Emily Himmelstoss</origin>
        <origin>Meredith Kratzmann</origin>
        <origin>Emily Himmelstoss</origin>
        <pubdate>2017</pubdate>
        <title>National Assessment of Shoreline Change: Summary Statistics for Updated Vector Shorelines and Associated Shoreline Change Data for the Gulf of Mexico and Southeast Atlantic Coasts</title>
        <serinfo><sername>Open-File Report</sername><issue>2017-1015</issue></serinfo>
        <pubinfo>
        <pubplace>Reston, VA</pubplace>
        <publish>U.S. Geological Survey</publish>
        </pubinfo>
        <onlink>https://doi.org/10.3133/ofr20171015</onlink>
    </citeinfo></crossref>
"""
metadata_additions = {'./idinfo':new_crossref}

# # If an element needs to be removed,
# remove_fills = {'./idinfo/crossref' # XPath to the location of the bad element
#                 :'AUTHOR' # text string that identifies the bad element
#                 }

# Example of a new distribution information:
new_distrib = """
    <distrib>
		<cntinfo>
            <cntperp>
                <cntper>Emily Himmelstoss</cntper>
				<cntorg>U.S. Geological Survey</cntorg>
			</cntperp>
			<cntaddr>
				<addrtype>mailing and physical address</addrtype>
				<address>384 Woods Hole Road</address>
				<city>Woods Hole</city>
				<state>MA</state>
				<postal>02543-1598</postal>
				<country>USA</country>
			</cntaddr>
			<cntvoice>508-548-8700 x2262</cntvoice>
			<cntfax>508-457-2310</cntfax>
            <cntemail>ehimmelstoss@usgs.gov</cntemail>
		</cntinfo>
	</distrib>
    """
metadata_replacements = {'./distinfo':new_distrib}

"""
Initialize
"""
#%% Initialize SB session
if "password" in locals():
    sb = log_in(useremail, password)
else:
    sb = log_in(useremail)
