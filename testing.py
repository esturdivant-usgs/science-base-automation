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


parentdir = r'/Users/esturdivant/Desktop/GOM_final' # OSX
for root, dirs, files in os.walk(parentdir):
	for d in dirs:
		xmllist += glob.glob(os.path.join(root,d,'*.xml'))

xmllist = glob.glob(os.path.join(parentdir, '*.xml'))

xml_file = xmllist[0]

cr1 = """
	<crossref>
		<citeinfo>
			<origin>Robert A. Morton</origin>
			<origin>Tara L. Miller</origin>
			<origin>Laura J. Moore</origin>
			<pubdate>2004</pubdate>
			<title>National Assessment of Shoreline Change: Part 1 Historical Shoreline Changes and Associated Coastal Land Loss along the U.S. Gulf of Mexico</title>
			<serinfo>
				<sername>Open-File Report</sername>
				<issue>2004-1043</issue>
			</serinfo>
			<pubinfo>
				<pubplace>Reston, VA</pubplace>
				<publish>U.S. Geological Survey</publish>
			</pubinfo>
			<onlink>https://pubs.usgs.gov/of/2004/1043/</onlink>
		</citeinfo>
	</crossref>"""
cr2 = """<crossref>
		<citeinfo>
			<origin>E.R. Thieler</origin>
			<origin>E.A. Himmelstoss</origin>
			<origin>J.L. Zichichi</origin>
			<origin>A. Ergul</origin>
			<pubdate>2009</pubdate>
			<title>Digital Shoreline Analysis System (DSAS) version 4.0 - An ArcGIS extension for calculating shoreline change</title>
			<serinfo>
				<sername>Open-File Report</sername>
				<issue>2008-1278</issue>
			</serinfo>
			<pubinfo>
				<pubplace>Reston, VA</pubplace>
				<publish>U.S. Geological Survey</publish>
			</pubinfo>
			<othercit>Current version of software at time of use was 4.3</othercit>
			<onlink>https://woodshole.er.usgs.gov/project-pages/DSAS/version4/</onlink>
			<onlink>https://woodshole.er.usgs.gov/project-pages/DSAS/</onlink>
		</citeinfo>
	</crossref>"""
cr3 = """<crossref><citeinfo>
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
remove_elemstr = """<crossref><citeinfo>
		<origin>AUTHOR</origin>
		<pubdate>YEAR</pubdate>
		<title>TITLE</title>
		<serinfo><sername>Open-File Report</sername><issue>ISSUE</issue></serinfo>
		<pubinfo>
		<pubplace>Reston, VA</pubplace>
		<publish>U.S. Geological Survey</publish>
		</pubinfo>
		<onlink>URL</onlink>
	</citeinfo></crossref>"""
elem2newvalue = {cr1:{'./idinfo/crossref':0},
                 cr2:{'./idinfo/crossref':1},
                 cr3:{'./idinfo/crossref':2}}

tree = etree.parse(xml_file)
metadata_root=tree.getroot()
# loop
newval, elemfind = elem2newvalue.items()[0]
newelem = etree.fromstring(newval)
# loop
fstr, i = elemfind.items()[0]
# find_elem = metadata_root.findall(fstr)[i]
# parent_elem = find_elem.getparent()
# parent_elem.replace(find_elem, newelem)
# # save
# tree.write(xml_file)



def remove_xml_element(metadata_root, path='./idinfo/crossref', fill_text='AUTHOR'):
	# Remove any elements in path that contain fill text
	# To be used as:
	# tree = etree.parse(xml_file)
	# metadata_root = tree.getroot()
	# metadata_root = remove_xml_element(metadata_root)
	# tree.write(xml_file)
	container, tag = os.path.split(path)
	parent_elem = metadata_root.find(container)
	for elem in parent_elem.iter(tag):
		for text in elem.itertext():
			if fill_text in text:
				parent_elem.remove(elem)
	return metadata_root

xml_file = xmllist[1]
tree = etree.parse(xml_file)
metadata_root = tree.getroot()
metadata_root = remove_xml_element(metadata_root)
tree.write(xml_file)
# remove_elem = etree.fromstring(remove_elemstr)
# container, tag = os.path.split(fstr)
# parent_elem = metadata_root.find(container)
# parent_elem.remove(remove_elem) # remove only works for element that was
# replace_elem = etree.fromstring(replacestr)

parentdir = r'/Users/esturdivant/Desktop/GOM_final' # OSX
# Get list of all xmlfiles in directory tree
xmllist = []
for root, dirs, files in os.walk(parentdir):
	for d in dirs:
		xmllist += glob.glob(os.path.join(root,d,'*.xml'))

for xml_file in xmllist:
	tree = etree.parse(xml_file)
	metadata_root = tree.getroot()
	metadata_root = remove_xml_element(metadata_root)
	tree.write(xml_file)
