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
sys.path.append(sb_auto_dir) # Add the script location to the system path just to make sure this works.
from autoSB import *
from config_autoSB import *



new_crossref = "<citeinfo><origin>Peter Ruggiero</origin><origin>Meredith Kratzmann</origin><origin>Emily Himmelstoss</origin><origin>E. Robert Thieler</origin><origin>David Reid</origin><pubdate>2013</pubdate><title>National Assessment of Shoreline Change: Historical Shoreline Change along the Pacific Northwest Coast</title><serinfo><sername>Open-File Report</sername><issue>2012-1007</issue></serinfo><pubinfo><pubplace>Reston, VA</pubplace><publish>U.S. Geological Survey</publish></pubinfo><onlink>https://pubs.usgs.gov/of/2012/1007/</onlink></citeinfo>""


tree = etree.parse(xml_file) # parse metadata using etree
metadata_root=tree.getroot()
# fstr = './idinfo/crossref'
# container, tag = os.path.split(fstr)
container = './idinfo'
tag = 'crossref'
elem = metadata_root.findall(container)[0]
elem.append(etree.Element(tag)) # append new tag to container element
elems = metadata_root.findall(fstr)
elems[len(elems)].text = new_crossref # set new value to final (new) tag
tree.write(xml_file)
