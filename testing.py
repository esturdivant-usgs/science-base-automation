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


sb = log_in(useremail)
parentitem.keys() = flexibly_get_item(sb, dict_DIRtoID['NCwest'])
parentitem['webLinks']=[{'uri':'doi.gov/oinoknoinoinoinoinoinoin'}]
dr_doi = get_DOI_from_item(flexibly_get_item(sb, dict_DIRtoID[d]))


def replace_element_in_xml(in_metadata, new_elem, containertag='./distinfo'):
	# Overwrites the first element in containertag corresponding to the tag of new_elem
	# in_metadata accepts either xml file or root element of parsed metadata.
	# new_elem accepts either lxml._Element or XML string
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
    # If new element is still a string convert it to an XML element
    if type(new_elem) is str:
        new_elem = etree.fromstring(new_elem)
    elif not type(new_elem) is etree._Element:
        raise TypeError("'new_elem' takes either strings or elements.")
	# Replace element with new_elem
    elem = metadata_root.findall(containertag)[0]
    old_elem = elem.findall(new_elem.tag)[0]
    elem.replace(old_elem, new_elem)
	# Either overwrite XML file with new XML or return the updated metadata_root
    if type(xml_file) is str:
        tree.write(xml_file)
        return xml_file
    else:
        return metadata_root

new_distrib = """
    <distrib>
		<cntinfo>
			<cntorgp>
				<cntorg>ScienceBase USGS</cntorg>
			</cntorgp>
			<cntaddr>
				<addrtype>mailing and physical address</addrtype>
				<address>ADDRESS</address>
				<city>CITY</city>
				<state>STATE</state>
				<postal>ZIP CODE</postal>
				<country>USA</country>
			</cntaddr>
			<cntvoice>PHONE</cntvoice>
			<cntfax>FAX</cntfax>
		</cntinfo>
	</distrib>
    """

xml_file = r"/Users/esturdivant/Documents/Projects/ScienceBase/SE_ATLANTIC/Florida/FLne_shorelines.shp2.xml"
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
