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

__all__ = ['get_title_from_data', 'map_newvals2xml', 'find_and_replace_text', 'update_xml', 'json_from_xml', 'get_fields_from_xml', 'log_in', 'flexibly_get_item', 'get_DOI_from_item', 'inherit_SBfields', 'find_or_create_child', 'upload_shp', 'get_parent_bounds', 'get_idlist_bottomup', 'upload_all_previewImages', 'shp_to_new_child', 'update_datapage', 'update_subpages_from_landing', 'update_pages_from_XML_and_landing', 'remove_all_files', 'update_XML_from_SB', 'Update_XMLfromSB', 'update_existing_fields', 'delete_all_children', 'remove_all_child_pages', 'universal_inherit', 'apply_topdown', 'apply_bottomup']


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

def map_newvals2xml(xml_file, new_values):
	# Create dictionary that maps new values to values that will be used to locate the XML element
	"""
	To update XML elements with new text:
		for newval, elemfind in val2xml.items():
			for elempath, i in elemfind.items():
				metadata_root.findall(elempath)[i].text = newval
	Currently hard-wired; will need to be adapted to match metadata scheme.
	Alternative: Search for 'xxx' in XML and replace with relevant value. Requires that values that need to be replaced have 'xxx'
	from VeeAnn:
	citeinfo/onlink citelink 1. DOI link; 2. child page URL; 3. data direct download URL (if possible)
	lworkcit/onlink lwork_link 1. DOI link; 2. link to landing page (optional)
	distinfo/.../networkr networkr 1. data direct download; 2. child page URL; 3. landing page URL (not necessary)
	"""
	val2xml = {} # initialize storage dictionary
	# Hard-wire path in metadata to each element
	seriesid = './idinfo/citation/citeinfo/serinfo/issue' # Citation / Series / Issue Identification
	citelink = './idinfo/citation/citeinfo/onlink' # Citation / Online Linkage
	lwork_link = './idinfo/citation/citeinfo/lworkcit/citeinfo/onlink' # Larger Work / Online Linkage
	lwork_serID = './idinfo/citation/citeinfo/lworkcit/citeinfo/serinfo/issue' # Larger Work / Series / Issue Identification
	networkr = './distinfo/stdorder/digform/digtopt/onlinopt/computer/networka/networkr' # Network Resource Name
	edition = './idinfo/citation/citeinfo/edition' # Citation / Edition
	metadate = './metainfo/metd' # Metadata Date
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
		landing_link = 'https://www.sciencebase.gov/catalog/item/{}'.format(landing_id)
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
	# Date and time of update
	now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
	val2xml[now_str] = {metadate: 0}
	return val2xml

def find_and_replace_text(fname, findstr='http:', replacestr='https:'):
    with open(fname, 'r') as f1:
        with open(fname+'.tmp', 'w') as f2:
            for line in f1:
                f2.write(line.replace(findstr, replacestr))
    os.rename(fname+'.tmp', fname)
    return fname

def update_xml(xml_file, new_values):
	# update XML file to include new child ID and DOI
	# uses dictionary of newval:{findpath:index}, e.g. {DOI:XXXXX:{'./idinfo/.../issue':0}}
	try:
		tree = etree.parse(xml_file) # parse metadata using etree
		metadata_root=tree.getroot()
		elem2newvalue = map_newvals2xml(xml_file, new_values)
		for newval,elemfind in elem2newvalue.items(): # Update elements with new ID text
			for fstr,i in elemfind.items():
				try:
					metadata_root.findall(fstr)[i].text = newval
				except IndexError:
					try:
						container, tag = os.path.split(fstr)
						elem = metadata_root.findall(container)[0]
						elem.append(etree.Element(tag))
						metadata_root.findall(fstr)[i].text = newval
					except:
						pass
				except:
					pass
		tree.write(xml_file) # Overwrite XML file with new XML
		return xml_file
	except Exception as e:
		print "Exception while trying to parse XML file: {}".format(e)
		return False

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
	item=sb.updateSbItem(item)
	return item

###################################################
#
# SB helper functions
#
###################################################
def log_in(username=False):
	if not username:
		username = raw_input("SB username (should be entire USGS email): ")
	if 'password' in globals():
		try:
			sb = pysb.SbSession(env=None).login(username,password)
		except NameError:
			sb = pysb.SbSession(env=None).loginc(username)
	else:
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
	while not doi:
		doi = item['webLinks'][i]['uri']
		if 'doi' in doi.lower():
			doi = doi[-16:]
		else:
			doi = False
			i += 1

def inherit_SBfields(sb, child_item, inheritedfields=['citation']):
	if inheritedfields:
		parentid, parent_link, parent_item = flexibly_get_item(sb, child_item['parentId'])
		for field in inheritedfields:
			try:
				child_item[field] = parent_item[field]
			except KeyError:
				print("KeyError in inherit_SBfields(). Field '{}' not inherited.".format(field))
				pass
		child_item = sb.updateSbItem(child_item)
	return child_item

def find_or_create_child(sb, parentid, child_title, skip_search=False, verbose=False):
	# Find or create new child page
	#if not skip_search:
	for child_id in sb.get_child_ids(parentid): # Check if child page already exists
		child_item = sb.get_item(child_id)
		if child_item['title'] == child_title:
			if verbose:
				print("Page with title '{}' was located.".format(child_title))
			break
	else: # If child doesn't already exist, create
		child_item = {}
		child_item['parentId'] = parentid
		child_item['title'] = child_title
		child_item = sb.create_item(child_item)
		if verbose:
			print("Creating page '{}' because it was not found in page {}.".format(child_title, parentid))
	return child_item

def upload_shp(sb, item, xml_file, replace=True, verbose=False):
	# Upload shapefile files to SB page, optionally remove all present files
	data_name = os.path.splitext(os.path.split(xml_file)[1])[0]
	datapath = os.path.split(xml_file)[0]
	if replace:
		# Remove all files (and facets) from child page
		item['files'] = []
		item['facets'] = []
		item=sb.updateSbItem(item)
		if verbose:
			print('All files and facets removed from page "{}".'.format(item['title']))
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
		print('Uploading "{}" shapefile files.'.format(data_name))
	item = sb.upload_files_and_upsert_item(item, up_files)
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
		get_parent_bounds(sb, page, verbose)

def upload_all_previewImages(sb, parentdir, dict_DIRtoID=False, dict_IDtoJSON=False, verbose=False):
	# Upload all image files to their respective pages.
	for (root, dirs, files) in os.walk(parentdir):
		for d in dirs:
			imagelist = glob.glob(os.path.join(root,d,'*.png'))
			imagelist.extend(glob.glob(os.path.join(root,d,'*.jpg')))
			imagelist.extend(glob.glob(os.path.join(root,d,'*.gif')))
			for f in imagelist:
				if not sb.is_logged_in():
					print('Logging back in...')
					sb = pysb.SbSession(env).login(useremail,password)
				try:
					item = sb.get_item(dict_DIRtoID[d])
				except:
					title = d # dirname should correspond to page title
					item = sb.find_items_by_title(title)['items'][0]
				if verbose:
					print('Uploading preview image to "{}"'.format(d))
				item = sb.upload_file_to_item(item, f)
				dict_IDtoJSON[item['id']] = item
	return dict_IDtoJSON

def shp_to_new_child(sb, xml_file, parent, dr_doi=False, inheritedfields=False, replace=True, imagefile=False):
	# Get values
	parentid, parent_link, parent_item = flexibly_get_item(sb, parent)
	# Get DOI link from parent_item
	if not dr_doi:
		dr_doi = get_DOI_from_item(parent_item)
	# Create (or find) new child page based on data title
	child_title = get_title_from_data(xml_file)
	child_item = find_or_create_child(sb, parentid, child_title, True)
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
	parentid, parent_link, parent_item = flexibly_get_item(sb, page)
	if replace:
		item = sb.replace_file(xml_file,item)
	if inheritedfields:
		parent_item = sb.get_item(item['parentId'])
		item = inherit_SBfields(sb, item, inheritedfields)
	return item # Return new JSON

def update_subpages_from_landing(sb, parentdir, subparent_inherits, dict_DIRtoID, dict_IDtoJSON):
	# Find sub-parent container pages following directory hierarchy and copy-paste fields from landing page
	for (root, dirs, files) in os.walk(parentdir):
		for d in dirs:
			if not sb.is_logged_in():
				print('Logging back in...')
				sb = pysb.SbSession(env).login(useremail,password)
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
	page_id,link,item = flexibly_get_item(sb, pageid)
	item['files'] = []
	item['facets'] = []
	item=sb.updateSbItem(item)
	if verbose:
		print('All files and facets removed from page "{}".'.format(item['title']))
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
	if not sb.is_logged_in():
		print('Logging back in...')
		sb = pysb.SbSession(env).loginc(useremail)
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
def delete_all_children(sb, parentid):
	cids = sb.get_child_ids(parentid)
	for cid in cids:
		try:
			delete_all_children(sb, cid)
		except Exception as e:
			print("EXCEPTION: {}".format(e))
	sb.delete_items(cids)
	if len(cids) > 0:
		print("{} children hanging on in {}, \nbut they should vanish soon?".format(len(cids), sb.get_item(parentid)['title']))
	else:
		print("Eradicated all kids from {}!".format(parentid))
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

def universal_inherit(sb, top_id, inheritedfields, verbose=False):
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
	for cid in sb.get_child_ids(top_id):
		try:
			apply_bottomup(sb, cid, function)
		except Exception as e:
			print("EXCEPTION: {}".format(e))
		citem = sb.get_item(cid)
		if verbose:
			print('Applying {} to page "{}"'.format(function, citem['title']))
		function(sb, citem)
	return True
