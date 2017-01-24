#%% Import packages
import pysb # Install on OSX with "pip install -e git+https://my.usgs.gov/stash/scm/sbe/pysb.git#egg=pysb"
import os
import glob
from lxml import etree
import json
import pickle
import sys
#sb_auto_dir = os.path.dirname(os.path.realpath(__file__))
sb_auto_dir = os.path.dirname(os.path.realpath('sb_automation.py'))
sys.path.append(sb_auto_dir) # Add the script location to the system path just to make sure this works
from autoSB import *
from config_autoSB import *




xml_file = r"/Users/esturdivant/Documents/Projects/ScienceBase/SE_ATLANTIC/Florida/FLne_shorelines.shp2.xml"

new_pubdate = "<pubdate>2017</pubdate>"

replace_element_in_xml(xml_file, new_distrib)


tree = etree.parse(xml_file) # parse metadata using etree
metadata_root=tree.getroot()
containertag = './distinfo'
elem = metadata_root.findall(containertag)[0]

new_elem = etree.fromstring(new_distrib)
old_elem = elem.findall(new_elem.tag)[0]
new_elem.tag == 'distrib'
elem.replace(old_elem, new_elem)


tree.write(xml_file)


strip_elements(elem, new_elem.tag)
