# -*- coding: utf-8 -*-
"""
autoSB.py

By: Emily Sturdivant, esturdivant@usgs.gov
Last modified: 1/10/17

OVERVIEW: Functions used in sb_automation.py
"""
#%% Import packages
import pysb # Install on OSX with "pip install -e git+https://my.usgs.gov/stash/scm/sbe/pysb.git#egg=pysb"
import os
import sys
import glob
from lxml import etree
import json
import pickle
import datetime

__all__ = ['get_title_from_data', 'get_root_flexibly', 'add_element_to_xml', 'fix_attrdomv_error',
		   'remove_xml_element', 'replace_element_in_xml', 'map_newvals2xml',
		   'find_and_replace_text', 'update_xml', 'json_from_xml',
		   'get_fields_from_xml', 'log_in', 'flexibly_get_item',
		   'get_DOI_from_item', 'inherit_SBfields', 'find_or_create_child',
		   'upload_data', 'upload_shp', 'get_parent_bounds', 'get_idlist_bottomup',
		   'set_parent_extent', 'upload_all_previewImages', 'shp_to_new_child',
		   'update_datapage', 'update_subpages_from_landing',
		   'update_pages_from_XML_and_landing', 'remove_all_files',
		   'update_XML_from_SB', 'Update_XMLfromSB', 'update_existing_fields',
		   'delete_all_children', 'remove_all_child_pages',
		   'landing_page_from_parentdir', 'universal_inherit', 'apply_topdown',
		   'apply_bottomup']


#%% Functions
###################################################
#
# Work with XML
#
###################################################
def get_title_from_data(xml_file, metadata_root=False):
	try:
		if not metadata_root:
			tree = etree.parse(xml_file) # parse metadata using etree
			metadata_root=tree.getroot()
		title = metadata_root.findall('./idinfo/citation/citeinfo/title')[0].text # Get title of child from XML
		return title
	except Exception as e:
		print >> sys.stderr, "Exception while trying to parse XML file ({}): {}".format(xml_file, e)
		return False

def get_root_flexibly(in_metadata):
	if type(in_metadata) is etree._Element:
		metadata_root = in_metadata
		tree = False
		xml_file =False
	elif type(in_metadata) is str:
		xml_file = in_metadata
		try:
			tree = etree.parse(xml_file) # parse metadata using etree
		except etree.XMLSyntaxError as e:
			print "XML Syntax Error while trying to parse XML file: {}".format(e)
			return False
		except Exception as e:
			print "Exception while trying to parse XML file: {}".format(e)
			return False
		metadata_root=tree.getroot()
	else:
		print("{} is not an accepted variable type for 'in_metadata'".format(in_metadata))
	return metadata_root, tree, xml_file

def add_element_to_xml(in_metadata, new_elem, containertag='./idinfo'):
	# Appends element 'new_elem' to 'containertag' in XML file. in_metadata accepts either xmlfile or root element of parsed metadata. new_elem accepts either lxml._Element or XML string
	# Whether in_metadata is a filename or an element, get metadata_root
	# FIXME: Check whether element already exists
	metadata_root, tree, xml_file = get_root_flexibly(in_metadata)
	# if type(in_metadata) is etree._Element:
	#     metadata_root = in_metadata
	#     xml_file =False
	# elif type(in_metadata) is str:
	#     xml_file = in_metadata
	#     tree = etree.parse(xml_file) # parse metadata using etree
	#     metadata_root=tree.getroot()
	# else:
	#     print("{} is not an accepted variable type for 'in_metadata'".format(in_metadata))
	# If new element is still a string convert it to an XML element
	if type(new_elem) is str:
	    new_elem = etree.fromstring(new_elem)
	elif not type(new_elem) is etree._Element:
	    raise TypeError("'new_elem' takes either strings or elements.")
	# Append new_elem to containertag element
	elem = metadata_root.findall(containertag)[0]
	elem.append(new_elem) # append new tag to container element
	# Either overwrite XML file with new XML or return the updated metadata_root
	if type(xml_file) is str:
	    tree.write(xml_file)
	    return xml_file
	else:
	    return metadata_root

def fix_attrdomv_error(in_metadata, verbose=False):
	# Fix attrdomv so that each has only one subelement
	metadata_root, tree, xml_file = get_root_flexibly(in_metadata)
	attrdomv = metadata_root.findall('./eainfo/detailed/attr/attrdomv')
	for elem in attrdomv:
		subelems = elem.getchildren()
		if len(subelems) > 1:
			if verbose:
				print('fixing error in Attribute Domain Values...')
			parent = elem.getparent()
			for child in subelems:
				new_elem = parent.makeelement(elem.tag)
				new_elem.insert(0, child)
				parent.append(new_elem)
			parent.remove(elem)
	if type(xml_file) is str:
	    tree.write(xml_file)
	    return xml_file
	else:
	    return metadata_root

def remove_xml_element(metadata_root, path='./', fill_text=['AUTHOR']):
	# Remove any elements in path that contain fill text
	# To be used as:
	# tree = etree.parse(xml_file)
	# metadata_root = tree.getroot()
	# metadata_root = remove_xml_element(metadata_root)
	# tree.write(xml_file)
	if type(fill_text) is str:
		fill_text = [fill_text]
	elif not type(fill_text) is list:
		print('fill_text must be string or list')
		raise(Exception)
	container, tag = os.path.split(path)
	parent_elem = metadata_root.find(container)
	for elem in parent_elem.iter(tag):
		for text in elem.itertext():
			for ftext in fill_text:
				if ftext in text:
					parent_elem.remove(elem)
	return metadata_root

def replace_element_in_xml(in_metadata, new_elem, containertag='./distinfo'):
	# Overwrites the first element in containertag corresponding to the tag of new_elem
	# in_metadata accepts either xml file or root element of parsed metadata.
	# new_elem accepts either lxml._Element or XML string
	# Whether in_metadata is a filename or an element, get metadata_root
	metadata_root, tree, xml_file = get_root_flexibly(in_metadata)
	# if type(in_metadata) is etree._Element:
	# 	metadata_root = in_metadata
	# 	xml_file =False
	# elif type(in_metadata) is str:
	# 	xml_file = in_metadata
	# 	tree = etree.parse(xml_file) # parse metadata using etree
	# 	metadata_root=tree.getroot()
	# else:
	# 	print("{} is not an accepted variable type for 'in_metadata'".format(in_metadata))
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

def replace_element_in_xml_for_wrapper(metadata_root, new_elem, containertag='./distinfo'):
	if type(new_elem) is str:
		new_elem = etree.fromstring(new_elem)
	elif not type(new_elem) is etree._Element:
		raise TypeError("'new_elem' takes either strings or elements.")
	# Replace element with new_elem
	elem = metadata_root.findall(containertag)[0]
	old_elem = elem.findall(new_elem.tag)[0]
	elem.replace(old_elem, new_elem)
	return metadata_root

def xml_write_wrapper(in_metadata, new_elem, containertag='./distinfo'):
	# FIXME: I don't actually know how to make a wrapper. This is completely unchecked.
	# in_metadata accepts either xml file or root element of parsed metadata.
	# Whether in_metadata is a filename or an element, get metadata_root
	metadata_root, tree, xml_file = get_root_flexibly(in_metadata)
	# if type(in_metadata) is etree._Element:
	# 	metadata_root = in_metadata
	# 	xml_file =False
	# elif type(in_metadata) is str:
	# 	xml_file = in_metadata
	# 	tree = etree.parse(xml_file) # parse metadata using etree
	# 	metadata_root=tree.getroot()
	# else:
	# 	print("{} is not an accepted variable type for 'in_metadata'".format(in_metadata))
	# If new element is still a string convert it to an XML element
	replace_element_in_xml_for_wrapper(metadata_root, new_elem, containertag)
	# Either overwrite XML file with new XML or return the updated metadata_root
	if type(xml_file) is str:
		tree.write(xml_file)
		return xml_file
	else:
		return metadata_root

def map_newvals2xml(new_values):
	# Create dictionary of {new value: {XPath to element: position of element in list retrieved by XPath}}
	# """
	# To update XML elements with new text:
	# 	for newval, elemfind in val2xml.items():
	# 		for elempath, i in elemfind.items():
	# 			metadata_root.findall(elempath)[i].text = newval
	# Currently hard-wired; will need to be adapted to match metadata scheme.
	# """
	# Hard-wire path in metadata to each element
	seriesid = './idinfo/citation/citeinfo/serinfo/issue' # Citation / Series / Issue Identification
	citelink = './idinfo/citation/citeinfo/onlink' # Citation / Online Linkage
	lwork_link = './idinfo/citation/citeinfo/lworkcit/citeinfo/onlink' # Larger Work / Online Linkage
	lwork_serID = './idinfo/citation/citeinfo/lworkcit/citeinfo/serinfo/issue' # Larger Work / Series / Issue Identification
	lwork_pubdate = './idinfo/citation/citeinfo/lworkcit/citeinfo/pubdate' # Larger Work / Publish date
	edition = './idinfo/citation/citeinfo/edition' # Citation / Edition
	pubdate = './idinfo/citation/citeinfo/pubdate' # Citation / Publish date
	caldate = './idinfo/timeperd/timeinfo/sngdate/caldate'
	networkr = './distinfo/stdorder/digform/digtopt/onlinopt/computer/networka/networkr' # Network Resource Name
	metadate = './metainfo/metd' # Metadata Date
	# Initialize storage dictionary
	val2xml = {}
	# DOI values
	if 'doi' in new_values.keys():
		# get DOI values (as issue and URL)
		doi_issue = "DOI:{}".format(new_values['doi'])
		doi_url = "https://doi.org/{}".format(new_values['doi'])
		# add new DOI values as {DOI:XXXXX:{'./idinfo/.../issue':0}}
		val2xml[doi_issue] = {seriesid:0, lwork_serID:0}
		val2xml[doi_url] = {citelink: 0, lwork_link: 0, networkr: 2}
	# Landing URL
	if 'landing_id' in new_values.keys():
		landing_link = 'https://www.sciencebase.gov/catalog/item/{}'.format(new_values['landing_id'])
		val2xml[landing_link] = {lwork_link: 1, networkr: 0}
	# Data page URL
	if 'child_id' in new_values.keys():
		# get URLs
		page_url = 'https://www.sciencebase.gov/catalog/item/{}'.format(new_values['child_id']) # data_item['link']['url']
		directdownload_link = 'https://www.sciencebase.gov/catalog/file/get/{}'.format(new_values['child_id'])
		# add values
		val2xml[directdownload_link] = {citelink:2, networkr:1}
		val2xml[page_url] = {citelink: 1, networkr: 1}
	# Edition
	if 'edition' in new_values.keys():
		val2xml[new_values['edition']] = {edition:0}
	if 'pubdate' in new_values.keys():
		val2xml[new_values['pubdate']] = {pubdate:0, lwork_pubdate:0, caldate:0}
	# Date and time of update
	now_str = datetime.datetime.now().strftime("%Y%m%d")
	val2xml[now_str] = {metadate: 0}
	return val2xml

def find_and_replace_text(fname, findstr='http:', replacestr='https:'):
    os.rename(fname, fname+'.tmp')
    with open(fname+'.tmp', 'r') as f1:
        with open(fname, 'w') as f2:
            for line in f1:
                f2.write(line.replace(findstr, replacestr))
    os.remove(fname+'.tmp')
    return fname

def find_and_replace_from_dict(fname, find_dict):
	# Takes dictionary of {replace_value: [find_str, find_str2]}
	os.rename(fname, fname+'.tmp')
	with open(fname+'.tmp', 'r') as f1:
		with open(fname, 'w') as f2:
			for line in f1:
				for rstr, flist in find_dict.iteritems():
					if type(flist) is str:
						flist = [flist]
					for fstr in flist:
						line = line.replace(fstr, rstr)
				f2.write(line)
	os.remove(fname+'.tmp')
	return fname

def update_xml(xml_file, new_values, verbose=False):
	# update XML file to include new child ID and DOI
	# uses dictionary of newval:{findpath:index}, e.g. {DOI:XXXXX:{'./idinfo/.../issue':0}}
	# Parse metadata
	metadata_root, tree, xml_file = get_root_flexibly(xml_file)
	# Work through metadata elements
	elem2newvalue = map_newvals2xml(new_values)
	for newval, elemfind in elem2newvalue.items(): # Update elements with new ID text
		# Add or update the values of each element
		for fstr, i in elemfind.items():
			try:
				metadata_root.findall(fstr)[i].text = newval
			except IndexError: # if the element does not yet exist, create the element
				try:
					container, tag = os.path.split(fstr)
					elem = metadata_root.find(container)
					elem.append(etree.Element(tag))
					metadata_root.findall(fstr)[i].text = newval
				except:
					pass
			except:
				pass
	# Could be moved to main script execution
	if "remove_fills" in new_values:
		[remove_xml_element(metadata_root, path, ftext) for path, ftext in new_values['remove_fills'].items()]
	if "metadata_additions" in new_values:
		[add_element_to_xml(metadata_root, new_elem, containertag) for containertag, new_elem in new_values['metadata_additions'].items()]
	if "metadata_replacements" in new_values:
		[replace_element_in_xml(metadata_root, new_elem, containertag) for containertag, new_elem in new_values['metadata_replacements'].items()]
	metadata_root = fix_attrdomv_error(metadata_root)
	# Overwrite XML file with new XML
	tree.write(xml_file)
	if "find_and_replace" in new_values:
		find_and_replace_from_dict(xml_file, new_values['find_and_replace'])
	if verbose:
		print("UPDATED XML: {}".format(xml_file))
	return xml_file

def json_from_xml():
	#FIXME: Currently hard-wired; will need to adapted to match metadata scheme.
	dict_xml2sb = dict()
	#dict_xml2sb['citation'] =
	dict_xml2sb['purpose'] = {'./idinfo/descript/purpose':0}
	dict_xml2sb['summary'] = {'./idinfo/descript/abstract':0}
	dict_xml2sb['body'] = {'./idinfo/descript/abstract':0}
	return dict_xml2sb

def get_fields_from_xml(sb, item, xml_file, sbfields, metadata_root=False):
	# Based on desired SB fields, get text values from XML
	if not metadata_root:
		tree = etree.parse(xml_file) # parse metadata using etree
		metadata_root=tree.getroot()
	dict_sb_from_xml = json_from_xml() # return dict for locating values in XML
	for field in sbfields:
		elemfind = dict_sb_from_xml[field]
		for fstr,i in elemfind.items():
			try:
				item[field] = metadata_root.findall(fstr)[i].text
			except:
				pass
	item = sb.updateSbItem(item)
	return item

###################################################
#
# SB helper functions
#
###################################################
def log_in(username=False, password=False):
	if 'sb' in globals():
		if not sb.is_logged_in():
			print('Logging back in...')
		else:
			return sb
	if not username:
		username = raw_input("SB username (should be entire USGS email): ")
	if not password:
		sb = pysb.SbSession(env=None).loginc(username)
	else:
		try:
			sb = pysb.SbSession(env=None).login(username, password)
		except Exception as e: # 'Login failed' returned as Exception for bad password in login()
			print('{}. Try reentering...'.format(e))
			sb = pysb.SbSession(env=None).loginc(username) # 'Invalid password, try again' printed for bad password
		except NameError as e:
			print('{}. Try reentering...'.format(e))
			sb = pysb.SbSession(env=None).loginc(username)
	return sb

def flexibly_get_item(sb, mystery_id, output='item'):
	# Given input of either ID or JSON, return ID, link, and JSON item
	if type(mystery_id) is str or type(mystery_id) is unicode:
		item_id = mystery_id
		item = sb.get_item(item_id)
	elif type(mystery_id) is dict:
		item = mystery_id
		item_id = item['id']
	if output.lower() == 'id':
		return item_id
	elif output.lower() == 'url':
		item_link = item['link']['url']
		return item_link
	else:
		return item

def get_DOI_from_item(item):
	# Get DOI link from parent_item
	doi = False
	i = 0
	try:
		weblinks = item['webLinks']
	except:
		print("No 'webLinks' in JSON for {}.".format(item['id']))
		return False
	while not doi:
		doi = doi[-16:] if 'doi' in weblinks[i]['uri'].lower() else False
		i += 1
	return doi

def inherit_SBfields(sb, child_item, inheritedfields=['citation'], verbose=False, inherit_void=True):
	# Upsert inheritedfield from parent to child by retrieving parent_item based on child
	# Modified 3/8/17: if field does not exist in parent, remove in child
	# If field is entered incorrecly, no errors will be thrown, but the page will not be updated.
	if verbose:
		print("Inheriting fields from parent '{}...'".format(child_item['title'][:50]))
	parent_item = flexibly_get_item(sb, child_item['parentId'])
	for field in inheritedfields:
		if not field in parent_item:
			if inherit_void:
				child_item[field] = None
			else:
				print("Field '{}' does not exist in parent and inherit_void is set to False so the current value will be preserved in child '{}...'.".format(field, child_item['title'][:50]))
		else:
			try:
				child_item[field] = parent_item[field]
			except Exception as e:
				print(e)
				pass
	child_item = sb.updateSbItem(child_item)
	return child_item

def find_or_create_child(sb, parentid, child_title, verbose=False):
	# Find or create new child page
	for child_id in sb.get_child_ids(parentid): # Check if child page already exists
		child_item = sb.get_item(child_id)
		if child_item['title'] == child_title:
			if verbose:
				print("FOUND: page '{}...'.".format(child_title[:50]))
			break
	else: # If child doesn't already exist, create
		child_item = {}
		child_item['parentId'] = parentid
		child_item['title'] = child_title
		child_item = sb.create_item(child_item)
		if verbose:
			print("Creating page '{}...' because it was not found in page {}.".format(child_title[:50], parentid))
	return child_item

def upload_data(sb, item, xml_file, replace=True, verbose=False):
	# Upload all files matching the XML filename to SB page.
	# E.g. xml_file = 'path/data_name.ext.xml' will upload all files beginning with 'data_name'
	# optionally remove all present files
	if replace:
		# Remove all files (and facets) from child page
		item = remove_all_files(sb, item, verbose)
	# List all files matching XML
	dataname = xml_file.split('.')[0]
	up_files = glob.glob(dataname + '.*')
	# Upload all files pertaining to data to child page
	if verbose:
		print('UPLOADING: {} ...'.format(os.path.basename(dataname)))
	item = sb.upload_files_and_upsert_item(item, up_files) # upsert should "create or update a SB item"
	return item

def upload_shp(sb, item, xml_file, replace=True, verbose=False):
	# Upload shapefile files to SB page, optionally remove all present files
	data_name = os.path.splitext(os.path.split(xml_file)[1])[0]
	datapath = os.path.split(xml_file)[0]
	if replace:
		# Remove all files (and facets) from child page
		item = remove_all_files(sb, item, verbose)
	# List files pertaining to shapefile for upload
	shp_exts = ['.cpg','.dbf','.prj','.sbn','.sbx','.shp','.shx','dbf.xml','.shp.xml']
	up_files = []
	# Upload all files pertaining to data to child page
	for ext in shp_exts:
		fname = '{}{}'.format(os.path.splitext(data_name)[0],ext)
		if os.path.isfile(os.path.join(datapath,fname)):
			up_files.append(os.path.join(datapath,fname))
	# Upload files
	if verbose:
		print('UPLOADING: {} ...'.format(data_name))
	item = sb.upload_files_and_upsert_item(item, up_files) # upsert should "create or update a SB item"
	return item

def get_parent_bounds(sb, parent_id, verbose=False):
	item = sb.get_item(parent_id)
	kids = sb.get_child_ids(parent_id)
	if len(kids) > 0:
		# Initialize parent_bounds with first child
		i = 0
		found = False
		while not found:
			try:
				child = sb.get_item(kids[i])
			except:
				i += 1
				found = False
			if 'facets' in child:
				parent_bounds = child['facets'][0]['boundingBox']
				found = True
			elif 'spatial' in child:
				parent_bounds = child['spatial']['boundingBox']
				found = True
			else:
				i += 1
				print("Child item '{}'' does not have 'spatial' or 'facets' fields.".format(child['title']))
		if len(kids) > 1:
			# Loop through kids
			for cid in kids[1:]:
				child = sb.get_item(cid)
				if 'facets' in child:
					bbox = child['facets'][0]['boundingBox'] # {u'minX': -81.43, u'minY': 28.374, u'maxX': -80.51, u'maxY': 30.70}
				elif 'spatial' in child:
					bbox = child['spatial']['boundingBox']
				else:
					continue
				for corner in parent_bounds:
					if 'min' in corner:
						parent_bounds[corner] = min(bbox[corner], parent_bounds[corner])
					if 'max' in corner:
						parent_bounds[corner] = max(bbox[corner], parent_bounds[corner])
		# Update parent bounding box
		try:
			item['spatial']['boundingBox'] = parent_bounds
		except KeyError:
			item['spatial'] = {}
			item['spatial']['boundingBox'] = parent_bounds
		item = sb.updateSbItem(item)
		if verbose:
			print('Updated bounding box for parent "{}"'.format(item['title']))
		return parent_bounds

def get_idlist_bottomup(sb, top_id):
	tier1 = sb.get_child_ids(top_id)
	tier2 = []
	for t1 in tier1:
		tier2 += sb.get_child_ids(t1)
	tier3 = []
	for t2 in tier2:
		tier3 += sb.get_child_ids(t2)
	idlist_bottomup = tier3 + tier2 + tier1
	idlist_bottomup.append(top_id)
	return idlist_bottomup

def set_parent_extent(sb, top_id, verbose=False):
	pagelist = get_idlist_bottomup(sb,top_id)
	for page in pagelist:
		parent_bounds = get_parent_bounds(sb, page, verbose)
	return parent_bounds

def upload_all_previewImages(sb, parentdir, dict_DIRtoID=False, dict_IDtoJSON=False, verbose=False):
	# Upload all image files to their respective pages.
	# 1. find all image files in folder tree
	# 2. for each image, try to upload it to it
	for (root, dirs, files) in os.walk(parentdir):
		for d in dirs:
			imagelist = glob.glob(os.path.join(root,d,'*.png'))
			imagelist.extend(glob.glob(os.path.join(root,d,'*.jpg')))
			imagelist.extend(glob.glob(os.path.join(root,d,'*.gif')))
			for f in imagelist:
				sb = log_in(useremail)
				try:
					item = sb.get_item(dict_DIRtoID[d])
				except:
					title = d # dirname should correspond to page title
					item = sb.find_items_by_title(title)['items'][0]
				if verbose:
					print('UPLOADING: preview image to "{}"...\n\n'.format(d))
				item = sb.upload_file_to_item(item, f)
				dict_IDtoJSON[item['id']] = item
	return dict_IDtoJSON

def shp_to_new_child(sb, xml_file, parent, dr_doi=False, inheritedfields=False, replace=True, imagefile=False):
	# NOT USED as of 3/8/17
	# Get values
	parent_item = flexibly_get_item(sb, parent)
	# Get DOI link from parent_item
	if not dr_doi:
		dr_doi = get_DOI_from_item(parent_item)
	# Create (or find) new child page based on data title
	child_title = get_title_from_data(xml_file)
	child_item = find_or_create_child(sb, parentid, child_title, verbose=True)
	# Update XML file to include new child ID and DOI
	update_xml(xml_file, child_item['id'],dr_doi,parent_link) #if metadata.findall(formname_tagpath)[0].text == 'Shapefile':
	# Upload shapefile files (including xml)
	child_item = upload_shp(sb, child_item, xml_file, replace) # Either clear all files first or upload in addition.
	try:
		child_item = sb.upload_file_to_item(child_item, imagefile)
	except NameError: # If image file in directory, add it
		for f in os.listdir(datapath):
			if f.lower().endswith(('png','jpg','gif')):
				imagefile = os.path.join(parentdir,f)
		child_item = sb.upload_file_to_item(child_item, imagefile)
	# Modify child page to match certain fields from parent
	if "inheritedfields" in locals():
		child_item = inherit_SBfields(sb, child_item, inheritedfields)
	return child_item # Return new JSON

def update_datapage(sb, page, xml_file, inheritedfields=False, replace=True):
	#FIXME This is not currently being used. Why not?
	parent_item = flexibly_get_item(sb, page)
	if replace:
		item = sb.replace_file(xml_file,item) # replace_file() does not work well
	if inheritedfields:
		parent_item = sb.get_item(item['parentId'])
		item = inherit_SBfields(sb, item, inheritedfields)
	return item # Return new JSON

def update_subpages_from_landing(sb, parentdir, subparent_inherits, dict_DIRtoID, dict_IDtoJSON):
	# Find sub-parent container pages following directory hierarchy and copy-paste fields from landing page
	for (root, dirs, files) in os.walk(parentdir):
		for d in dirs:
			sb = log_in(useremail)
			subpage = sb.get_item(dict_DIRtoID[d])
			subpage = inherit_SBfields(sb, subpage, subparent_inherits)
			dict_IDtoJSON[subpage['id']] = subpage
	return dict_IDtoJSON

def update_pages_from_XML_and_landing(sb, dict_DIRtoID, data_inherits, subparent_inherits, dict_PARtoCHILDS):
	# Populate data pages
	for xmlpath, pageid in dict_DIRtoID.items():
		if len(os.path.split(xmlpath)) > 1: # If dict key is XML file
			item = update_datapage(sb, pageid, xmlpath, inheritedfields=data_inherits, replace=True)
		else: # If it's not an XML file, then it must be a directory
			item = sb.get_item(dict_DIRtoID[xmlpath])
			pageid = item['id']
			parentid = item['parentId']
			item = inherit_SBfields(sb, item, subparent_inherits)
		dict_IDtoJSON[pageid] = item
	#%% BOUNDING BOX
	bb_dict = set_parent_boundingBoxes(sb, dict_PARtoCHILDS)
	# Preview Images
	dict_IDtoJSON = upload_all_previewImages(sb, parentdir, dict_DIRtoID, dict_IDtoJSON)

def remove_all_files(sb, pageid, verbose=False):
	# Remove all files (and facets) from child page
	item = flexibly_get_item(sb, pageid)
	item['files'] = []
	item['facets'] = []
	item=sb.updateSbItem(item)
	if verbose:
		print('REMOVED: any files or facets on page "{}".'.format(item['title']))
	return item

def update_XML_from_SB(sb, parentdir, dict_DIRtoID, dict_IDtoJSON):
	# Populate metadata from SB pages
	# 1/17/17: no evidence that this fxn is being used
	xmllist = glob.glob(os.path.join(parentdir,'*.xml'))
	for f in os.listdir(parentdir):
		if f.lower().endswith(('xml')):
			xml_list = xmllist[1:]
	for xml_file in xml_list:
		if xml_file in dict_DIRtoID:
			child_id = dict_DIRtoID[xml_file]
			parentid = dict_IDtoJSON[child_id]['parentId']
		else:
			child_title = get_title_from_data(xml_file) # data title in XML should correspond to page title
			child_item = sb.find_items_by_title(child_title)['items'][0]
			child_id = child_item['id']
			parentid = child_item['parentId']
		parent_link = dict_IDtoJSON[parentid]['link']['url']
		# Update XML file to include new child ID and DOI
		update_xml(xml_file, child_id, dr_doi, parent_link)
		child_item = sb.replace_file(xml_file, item)
		dict_IDtoJSON[child_item['id']] = child_item
	return dict_IDtoJSON

def Update_XMLfromSB(sb, useremail, parentdir, fname_dir2id='dir_to_id.json', fname_id2json='id_to_json.json'):
	# read data
	# 1/17/17: no evidence that this fxn is being used
	with open(os.path.join(parentdir,fname_dir2id), 'r') as f:
		dict_DIRtoID = json.load(f)
	with open(os.path.join(parentdir,fname_id2json), 'r') as f:
		dict_IDtoJSON = json.load(f)
		# log into ScienceBase
	sb = log_in(useremail)
	# Populate XML with SB values
	dict_IDtoJSON = update_XML_from_SB(sb, parentdir, dict_DIRtoID, dict_IDtoJSON)
	# Update dictionary with JSON items
	with open(os.path.join(parentdir,'id_to_json.json'), 'w') as f:
		json.dump(dict_IDtoJSON, f)
	print("Dictionary saved as: {}".format(os.path.join(parentdir,'id_to_json.json')))
	return True

def update_existing_fields(sb, parentdir, data_inherits, subparent_inherits, fname_dir2id='dir_to_id.json', fname_id2json='id_to_json.json', fname_par2childs='parentID_to_childrenIDs.txt'):
	# Populate pages if SB page structure already exists.
	# read data
	with open(os.path.join(parentdir,fname_dir2id), 'r') as f:
		dict_DIRtoID = json.load(f)
	with open(os.path.join(parentdir,fname_par2childs), 'r') as f:
		dict_PARtoCHILDS = json.load(f)
		# Update SB fields
	dict_IDtoJSON = update_pages_from_XML_and_landing(sb, dict_DIRtoID, data_inherits, subparent_inherits, dict_PARtoCHILDS)
	# Update dictionary with JSON items
	with open(os.path.join(parentdir,fname_id2json), 'w') as f:
		json.dump(dict_IDtoJSON, f)
	print("Fields updated and values items stored in dictionary: {}".format(os.path.join(parentdir,fname_id2json)))
	return True

###################################################
#
# Apply functions to entire data release page tree
#
###################################################
def delete_all_children(sb, parentid, verbose=False):
	# Recursively delete all SB items that are descendants of the input page.
	cids = sb.get_child_ids(parentid)
	for cid in cids:
		try:
			delete_all_children(sb, cid)
		except Exception as e:
			print("EXCEPTION: {}".format(e))
	sb.delete_items(cids)
	ptitle = sb.get_item(parentid)['title']
	if len(cids) > 0:
		print("{} children hanging on in {}, \nbut they should vanish soon?".format(len(cids), ptitle))
	else:
		if verbose:
			print("Eradicated all kids from {}!".format(ptitle))
	return True

def remove_all_child_pages(useremail=False, landing_link=False):
	if not useremail:
		useremail = raw_input("SB username (should be entire USGS email): ")
	if not landing_link:
		landing_link = raw_input("Landing page URL: ")
	landing_id = os.path.split(landing_link)[1]
	sb = log_in(useremail)
	delete_all_children(sb, landing_id)
	return landing_id

def landing_page_from_parentdir(parentdir, parent_xml, previewImage, new_values):
	for f in os.listdir(parentdir):
		if f.lower().endswith('xml'):
			parent_xml = os.path.join(parentdir,f) # metadata file in landing directory = parent_xml
	#%% Populate landing page from metadata
	if "parent_xml" in locals():
		# Update XML file to include new parent ID and DOI
		parent_xml = update_xml(parent_xml, new_values)
		landing_item = new_values['landing_item']
		try: # upload XML to landing page
			landing_item = sb.upload_file_to_item(landing_item, parent_xml)
		except Exception as e:
			print(e)
		if 'body' not in landing_item.keys():
			try: # update SB landing page with specific fields from XML
				landing_item = get_fields_from_xml(sb, landing_item, parent_xml, landing_fields_from_xml)
				landing_item=sb.updateSbItem(landing_item)
			except Exception as e:
				print(e)
	if imagefile:
		try: # Add preview image to landing page
			landing_item = sb.upload_file_to_item(landing_item, imagefile)
		except Exception as e:
			print("Exception while trying to upload file {}: {}".format(imagefile, e))
	return landing_item, imagefile

def universal_inherit(sb, top_id, inheritedfields, verbose=False):
	# Given an SB ID, pass on selected fields to all descendants; doesn't look for parents
	for cid in sb.get_child_ids(top_id):
		citem = sb.get_item(cid)
		if verbose:
			print('Inheriting fields for "{}" from its parent page'.format(citem['title']))
		inherit_SBfields(sb, citem)
		try:
			universal_inherit(sb, cid, inheritedfields, verbose)
		except Exception as e:
			print("EXCEPTION: {}".format(e))
	return True

def apply_topdown(sb, top_id, function, verbose=False):
	# Given an SB ID, do function to all descendants; doesn't look for parents
	#FIXME: does it work to simply use function name as argument?
	for cid in sb.get_child_ids(top_id):
		citem = sb.get_item(cid)
		if verbose:
			print('Applying {} to page "{}"'.format(function, citem['title']))
		function(sb, citem)
		try:
			apply_topdown(sb, cid, function)
		except Exception as e:
			print("EXCEPTION: {}".format(e))
	return True

def apply_bottomup(sb, top_id, function, verbose=False):
	# Given an SB ID, do function to all ancestors; doesn't look for children
	#FIXME: does it work to simply use function name as argument?
	for cid in sb.get_child_ids(top_id):
		try:
			apply_bottomup(sb, cid, function, verbose)
		except Exception as e:
			print("EXCEPTION: {}".format(e))
		citem = sb.get_item(cid)
		if verbose:
			print('Applying {} to page "{}"'.format(function, citem['title']))
		function(sb, citem)
	return True
