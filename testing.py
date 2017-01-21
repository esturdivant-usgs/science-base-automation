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


def add_element_to_xml(in_metadata, new_elem, fstr='./idinfo/crossref'):
    # Whether in_metadata is a filename or an element, get metadata_root
    if type(in_metadata) is etree._Element:
        metadata_root = in_metadata
        xml_file =False
    elif type(in_metadata) is str:
        xml_file = in_metadata
        tree = etree.parse(xml_file) # parse metadata using etree
        metadata_root=tree.getroot()
    else:
        print("{} is not an accepted variable type for 'in_metadata'".format(in_metadata))
    # If new element is a string convert it to an XML element
    container, tag = os.path.split(fstr)
    elem = metadata_root.findall(container)[0]
    elem.append(etree.Element(tag)) # append new tag to container element
    elems = metadata_root.findall(fstr)
    i = len(elems)
    if type(new_elem) is str:
        new_elem = etree.fromstring(new_elem)
    elif not type(new_elem) is etree._Element:
        raise TypeError("'new_elem' takes either strings or elements.")
    elems[i-1] = new_elem # set new value to final (new) tag
    if xml_file:
        tree.write(xml_file)
        return xml_file
    else:
        return metadata_root

xml_file = '/Users/emilysturdivant/Documents/USGS/Test Data Release/North Carolina/NCwest/NCwest_transects_rates_LT_2.shp.xml'
new_crossref = r"<citeinfo><origin>Peter Ruggiero</origin><origin>Meredith Kratzmann </origin> <origin>Emily Himmelstoss</origin><origin>E. Robert Thieler</origin><origin>David Reid</origin><pubdate>2013</pubdate><title>National Assessment of Shoreline Change: Historical Shoreline Change along the Pacific Northwest Coast</title><serinfo><sername>Open-File Report</sername><issue>2012-1007</issue></serinfo><pubinfo><pubplace>Reston, VA</pubplace><publish>U.S. Geological Survey</publish></pubinfo><onlink>https://pubs.usgs.gov/of/2012/1007/</onlink></citeinfo>"
xml_file = add_element_to_xml(xml_file, new_crossref)

elem = etree.fromstring(new_crossref)
tree = etree.parse(xml_file) # parse metadata using etree
metadata_root=tree.getroot()
metadata_root = add_element_to_xml(metadata_root, new_crossref)
tree.write(xml_file+'tmp.xml')
