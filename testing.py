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
import sciencebasepy as pysb
import os
import glob
from lxml import etree
import json
import pickle
import datetime
import sys
try:
	sb_auto_dir = os.path.dirname(os.path.realpath(__file__))
except:
	sb_auto_dir = os.path.dirname(os.path.realpath('sb_automation.py'))
	sb_auto_dir = r'/Users/esturdivant/GitHub/science-base-automation'
sys.path.append(sb_auto_dir) # Add the script location to the system path just to make sure this works.
from autoSB import *
from config_autoSB import * # Input sciencebase password
# from Tkinter import *
import getpass

password = getpass.getpass('ScienceBase password: ')
# sb = log_in(useremail)
if not sb.is_logged_in():
	print('Logging back in...')
	try:
		sb = pysb.SbSession(env=None).login(useremail, password)
	except NameError:
		sb = pysb.SbSession(env=None).loginc(useremail)
cnt=0

#%% get JSON item for parent page
landing_item = sb.get_item(landing_id)
new_values = {'landing_id':landing_item['id'], 'doi':dr_doi}
if 'pubdate' in locals():
	new_values['pubdate'] = pubdate
if 'find_and_replace' in locals():
	new_values['find_and_replace'] = find_and_replace
if 'metadata_additions' in locals():
	new_values['metadata_additions'] = metadata_additions
if "metadata_replacements" in locals():
	new_values['metadata_replacements'] = metadata_replacements
if "remove_fills" in locals():
	new_values['remove_fills'] = remove_fills
new_values

try:
	sb = pysb.SbSession(env=None).login(useremail, password)
	print('logged in with saved password')
except NameError:
	sb = pysb.SbSession(env=None).loginc(useremail)
	print('logged in with input password')

if not "dict_DIRtoID" in locals():
	with open(os.path.join(parentdir,'dir_to_id.json'), 'r') as f:
	dict_DIRtoID = json.load(f)
if not "dict_IDtoJSON" in locals():
	with open(os.path.join(parentdir,'id_to_json.json'), 'r') as f:
		dict_IDtoJSON = json.load(f)
xmllist = glob.glob(os.path.join(parentdir, '**/*.xml'), recursive=True)
xml_file = xmllist[48]
os.path.basename(xml_file)


# def remove_files(parentdir, pattern='**/*.xml_orig'):
#     # Recursively remove files matching pattern
#     xmllist = glob.glob(os.path.join(parentdir, pattern), recursive=True)
#     for xml_file in xmllist:
#     	os.remove(xml_file)
#     return(parentdir)
#
# if remove_original_xml:
#     remove_files(parentdir, pattern='**/*.xml_orig')


#%% Test find and replace
os.path.basename(xml_file)
update_xml(xml_file, new_values, verbose=True)

#%% Check max size
# List all files in directory, except original xml and other bad apples
datadir = os.path.dirname(xml_file)
up_files = [os.path.join(datadir, fn) for fn in os.listdir(datadir)
			if not fn.endswith('_orig')
			and not fn.endswith('DS_Store')
			and not fn.endswith('.lock')
			and os.path.isfile(os.path.join(datadir, fn))]
bigfiles = []
for fn in up_files:
	print(os.path.basename(fn))

for fn in up_files:
	if os.path.getsize(fn) > max_MBsize*1000000: # convert megabytes to bytes
		bigfiles.append(os.path.basename(fn))
		up_files.remove(fn)
for fn in up_files:
	print([os.path.basename(fn), os.path.getsize(fn)/1000000])
print('\n'.join([os.path.basename(fn) for fn in up_files]))

#%%
#%% Change folder name to match XML title

parentdir = r'/Volumes/stor/Projects/DeepDive/5_datarelease_packages/vol1_v4_xmlonly'
rename_dirs_from_xmls(parentdir)

restore_original_xmls(parentdir)

xmllist = glob.glob(os.path.join(parentdir, '**/*.xml'), recursive=True)
imagefile = False
dict_DIRtoID, dict_IDtoJSON = setup_subparents(sb, parentdir, landing_id, xmllist, imagefile)







#%% Perform upload_files for one data page, based on the XML file.
datadir = os.path.dirname(xml_file)
pageid = dict_DIRtoID[os.path.relpath(datadir, os.path.dirname(parentdir))]
data_title = get_title_from_data(xml_file)
if [len(glob.glob(os.path.join(datadir, '**/*.xml'), recursive=True)) == 1
	and not [fn for fn in os.listdir(datadir) if os.path.isdir(os.path.join(datadir,fn))]]:
	# Change subparent title to data title
	data_item = flexibly_get_item(sb, pageid)
	orig_title = data_item['title']
	data_item['title'] = data_title
	data_item = sb.update_item(data_item)
	print("RENAMED: page '{}' in place of '{}'".format(trunc(data_title), orig_title))
# Or create/find a new page to match the XML file
else:
	# Create (or find) data page based on title
	data_item = find_or_create_child(sb, pageid, data_title, verbose=verbose)
landing_item = sb.get_item(landing_id)
new_values = {'landing_id':landing_item['id'], 'doi':dr_doi}
if 'pubdate' in locals():
	new_values['pubdate'] = pubdate
try:
	# If pubdate in new_values, set it as the date for the SB page
	data_item["dates"][0]["dateString"]= new_values['pubdate'] #FIXME add this to a function in a more generalized way?
except:
	pass
data_item, bigfiles1 = upload_files(sb, data_item, xml_file, max_MBsize=max_MBsize, replace=True, verbose=verbose)
dict_DIRtoID[xml_file] = data_item['id']
dict_IDtoJSON[data_item['id']] = data_item
# started: 3:37
# completed:

#%% Add browse graphic title to page - Not working. The change to the JSON item is not taking effect.
# Create function get_browsedesc_from_xml()
def get_browsedesc_from_xml(xml_file, metadata_root=False):
	try:
	if not metadata_root:
	tree = etree.parse(xml_file) # parse metadata using etree
	metadata_root=tree.getroot()
	title = metadata_root.findall('./idinfo/browse/browsed')[0].text # Get title of child from XML
	return(title)
	except Exception as e:
	print("Exception while trying to parse XML file ({}): {}".format(xml_file, e), file=sys.stderr)
	return(False)

xml_file = r'/Volumes/stor/Projects/DeepDive/5_datarelease_packages/vol1_v2_4sb/Edwin B. Forsythe NWR, NJ, 2010/DC_DT_SLpts/ebf10_DC_DT_SLpts_meta.xml'
browse_title = get_browsedesc_from_xml(xml_file)

page_id = '5c6dc479e4b0fe48cb4024ae'
data_item = sb.get_item(page_id)

# Change title
data_item['previewImage']['original']
data_item['previewImage']['original']['title'] = 'browse_title'
data_item['previewImage']['original']['title'] # --> 'browse_title'
data_item = sb.update_item(data_item)
data_item = sb.get_item(page_id)
data_item['previewImage']['original']['title'] # --> Not 'browse_title'

#%% Working with browse graphic population... Looking at section of for loop.
new_values ={'child_id':'5c65dffde4b0fe48cb3907b2'}
new_values['browse_file'] = '000'
new_values.pop('browse_file', None) # remove value from past iteration
new_values
datadir = os.path.dirname(xml_file)
imagelist = glob.glob(os.path.join(datadir,'*browse*.png'))
imagelist.extend(glob.glob(os.path.join(datadir,'*browse*.jpg')))
imagelist.extend(glob.glob(os.path.join(datadir,'*browse*.gif')))
# reldirpath = os.path.join(os.path.relpath(root, os.path.dirname(parentdir)), d)
if len(imagelist) > 0:
	new_values['browse_file'] = os.path.basename(imagelist[0])
else:
	print("Note: No browse graphic uploaded because no files matched the pattern.".format(data_title))

xml_file = r'/Volumes/stor/Projects/DeepDive/5_datarelease_packages/CeI10_DisMOSH_Cost_MOSHShoreline_meta.xml'
update_xml(xml_file, new_values, verbose=verbose) # new_values['pubdate']



with open(os.path.join(parentdir,'dir_to_id.json'), 'r') as f:
	dict_DIRtoID = json.load(f)
with open(os.path.join(parentdir,'id_to_json.json'), 'r') as f:
	dict_IDtoJSON = json.load(f)
# Preview Image
# org_map['IDtoJSON'] = upload_all_previewImages(sb, parentdir, org_map['DIRtoID'], org_map['IDtoJSON'])
dict_IDtoJSON = upload_all_previewImages(sb, parentdir, dict_DIRtoID, dict_IDtoJSON)

# Save dictionaries
# with open(os.path.join(parentdir,'org_map.json'), 'w') as f:
# 	json.dump(org_map, f)
with open(os.path.join(parentdir,'dir_to_id.json'), 'w') as f:
	json.dump(dict_DIRtoID, f)
with open(os.path.join(parentdir,'id_to_json.json'), 'w') as f:
	json.dump(dict_IDtoJSON, f)




#%% Change find_and_replace so that keys are searchstr and values are replacestr
find_and_replace = {'https://doi.org/{}'.format(dr_doi): ['https://doi.org/10.5066/***'],
	'DOI:{}'.format(dr_doi): ['DOI:XXXXX'],
	'xxx': ['**ofrDOI**'],
	# 'E.R. Thieler': ['E. Robert Thieler', 'E. R. Thieler'],
	# 'https:': 'http:',
	'doi.org': 'dx.doi.org'
	}
fr2 = {'https://doi.org/10.5066/***':'https://doi.org/{}'.format(dr_doi),
	'DOI:XXXXX':'DOI:{}'.format(dr_doi),
	'**ofrDOI**':'xxx',
	# 'E.R. Thieler': ['E. Robert Thieler', 'E. R. Thieler'],
	# 'https:': 'http:',
	'dx.doi.org':'doi.org'
	}




datadir = os.path.dirname(xml_file)
sub_xmllist = glob.glob(os.path.join(datadir, '**/*.xml'), recursive=True)
innerdirs = [fn for fn in os.listdir(datadir) if os.path.isdir(os.path.join(datadir,fn))]
if len(sub_xmllist) == 1 and not innerdirs:
	print("One XML and no sub-directories...")

datadir = os.path.dirname(xml_file)
if [len(glob.glob(os.path.join(datadir, '**/*.xml'), recursive=True)) == 1
	and not [fn for fn in os.listdir(datadir) if os.path.isdir(os.path.join(datadir,fn))]]:
	print("One XML and no sub-directories...")
# convert the subparent into the data page

pageid = dict_DIRtoID[os.path.relpath(datadir, os.path.dirname(parentdir))]
# get subparent item that will become data page
data_item = flexibly_get_item(sb, pageid)

# Get title of data from XML and change title
data_title = get_title_from_data(xml_file)
data_item['title'] = data_title
data_item = sb.update_item(data_item)

#%% values that could be extracted from the SB item:
page_url = data_item['link']['url']
facets = [fi['name'] for fi in data_item['facets']]


[print(key) for key in data_item.keys()]

data_item['browseTypes']
data_item['browseCategories']
for fi in data_item['files']:
	print(fi['name'])
for fi in data_item['facets']:
	print(fi['name'])


for link in data_item['distributionLinks']:
	print(link['title'])
	print(link['uri'])

data_item['distributionLinks'][1]['uri']



wayne_item = flexibly_get_item(sb, '5a946742e4b069906068fb47')
wayne_item['distributionLinks'][1]['uri']

soduspt_item = flexibly_get_item(sb, '5b1ede6ce4b092d965254a3f')
soduspt_item['distributionLinks'][0]['uri']

sp_item_dist = sb.get_item('5b1ede6ce4b092d965254a3f', params={'fields':'distributionLinks'})
sp_item_dist








#%% Upload all XML files without updating them.
parentdir = r'/Volumes/ThunderVant/Projects/UAS_BlackBeach/Publishing/Data_publishing/data_release_revisedSept' # OSX Desktop
with open(os.path.join(parentdir,'dir_to_id.json'), 'r') as f:
	dict_DIRtoID = json.load(f)

replace_files_by_ext(sb, parentdir, dict_DIRtoID, match_str='*.xml') # only replaces the file if the file is already on the data page.

#%% Temp: upload images.zip
xml_file = '/Volumes/ThunderVant/Projects/UAS_BlackBeach/Publishing/Data_publishing/data_release_revisedSept/Field Data (images and reference points)/bb20160318_UAS_images_meta.xml'
d = 'Field Data (images and reference points)'

if not sb.is_logged_in():
	print('Logging back in...')
	try:
	sb = pysb.SbSession(env=None).login(useremail,password)
	except NameError:
	sb = pysb.SbSession(env=None).loginc(useremail)

with open(os.path.join(parentdir,'dir_to_id.json'), 'r') as f:
	dict_DIRtoID = json.load(f)

parentid = dict_DIRtoID[d]
# Create (or find) new data page based on title in XML
data_title = get_title_from_data(xml_file) # get title from XML
data_item = find_or_create_child(sb, parentid, data_title, verbose=verbose) # Create (or find) data page based on title
# Upload to ScienceBase
data_item, bigfiles1 = upload_files_matching_xml(sb, data_item, xml_file, max_MBsize=2000, replace=True, verbose=verbose)



#%% DEM

xml_file = '/Volumes/ThunderVant/Projects/UAS_BlackBeach/Publishing/Data_publishing/data_release_4upload_3/SfM products (point cloud, orthomosaic, and DEM)/bb20160318_sfm_dem_meta.xml'
d = 'SfM products (point cloud, orthomosaic, and DEM)'
if not sb.is_logged_in():
	print('Logging back in...')
	try:
	sb = pysb.SbSession(env=None).login(useremail,password)
	except NameError:
	sb = pysb.SbSession(env=None).loginc(useremail)
parentid = dict_DIRtoID[d]
new_values['doi'] = dr_doi if 'dr_doi' in locals() else get_DOI_from_item(flexibly_get_item(sb, parentid))
# Create (or find) new data page based on title in XML
data_title = get_title_from_data(xml_file) # get title from XML
data_item = find_or_create_child(sb, parentid, data_title, verbose=verbose) # Create (or find) data page based on title
try: #FIXME: add this to a function in a more generalized way?
	data_item["dates"][0]["dateString"]= new_values['pubdate']
	#data_item["dates"][1]["dateString"]= {"type": "Info", "dateString": "2016", "label": "Time Period"} # What should the time period value reflect?
except:
	pass
# Upload to ScienceBase
data_item, bigfiles1 = upload_files_matching_xml(sb, data_item, xml_file, max_MBsize=2000, replace=True, verbose=verbose)

# sb, xml_file, directory, dict_DIRtoID, new_values,

#%%QC
if quality_check_pages:
	qcfields_dict = {'contacts':4, 'webLinks':0, 'facets':1}
	print('Checking that each page has: \n{}'.format(qcfields_dict))
	pagelist = check_fields2_topdown(sb, landing_id, qcfields_dict, verbose=False)

landing_item = sb.get_item(landing_id)
child_id = '58b89028e4b01ccd5500c263'
child_item = sb.get_item(child_id)

# Revise the XML, except for the values created by SB
# Recursively list all XML files in parentdir
xmllist = []
for root, dirs, files in os.walk(parentdir):
	for d in dirs:
	xmllist += glob.glob(os.path.join(root,d,'*.xml'))

#%% Count XML files and modify metadata
xmllist = []
for root, dirs, files in os.walk(parentdir):
	for d in dirs:
	xmllist += glob.glob(os.path.join(root,d,'*.xml'))
xml_cnt = len(xmllist)
# for xml_file in xmllist:
# 	tree = etree.parse(xml_file)
# 	metadata_root = tree.getroot()
# 	if "remove_fills" in locals():
# 		[remove_xml_element(metadata_root, path, ftext) for path, ftext in remove_fills.items()])
# 	if "metadata_additions" in locals():
# 		[add_element_to_xml(metadata_root, new_elem, containertag) for containertag, new_elem in metadata_additions.items()]
# 	if "metadata_replacements" in locals():
# 		[replace_element_in_xml(metadata_root, new_elem, containertag) for containertag, new_elem in metadata_replacements.items()]
# 	tree.write(xml_file)
# 	find_and_replace_text(xml_file, 'http:', 'https:') 		    # Replace 'http:' with 'https:'
# 	find_and_replace_text(xml_file, 'dx.doi.org', 'doi.org') 	# Replace 'dx.doi.org' with 'doi.org'

xml_file = '/Volumes/ThunderVant/Projects/UAS_BlackBeach/Publishing/Data_publishing/data_release_revisedSept_sb/SfM products (point cloud, orthomosaic, and DEM)/bb20160318_sfm_orthomosaic_meta.xml'
os.path.basename(os.path.dirname(xml_file))
cnt = 0
# for xml_file in xmllist:
cnt += 1
if not sb.is_logged_in():
	print('Logging back in...')
	try:
		sb = pysb.SbSession(env=None).login(useremail,password)
	except NameError:
		sb = pysb.SbSession(env=None).loginc(useremail)
d = os.path.basename(os.path.dirname(xml_file))
parentid = dict_DIRtoID[d]
new_values['doi'] = dr_doi if 'dr_doi' in locals() else get_DOI_from_item(flexibly_get_item(sb, parentid))
# Create (or find) new data page based on title in XML
data_title = get_title_from_data(xml_file) # get title from XML
data_item = find_or_create_child(sb, parentid, data_title, verbose=verbose) # Create (or find) data page based on title
try:
	data_item["dates"][0]["dateString"]= new_values['pubdate'] #FIXME add this to a function in a more generalized way?
	#data_item["dates"][1]["dateString"]= {"type": "Info", "dateString": "2016", "label": "Time Period"} # What should the time period value reflect?
except:
	pass
# 2. MAKE UPDATES
# Update XML
if update_XML:
	# Check for Browse graphic
	dataname = xml_file.split('.')[0]
	dataname = dataname.split('_meta')[0]
	browse_file = glob.glob(dataname + '*browse*')[0]
	if len(browse_file) > 0:
		new_values['browse_file'] = browse_file
	# add SB UID to be updated in XML
	new_values['child_id'] = data_item['id']
	update_xml(xml_file, new_values, verbose=verbose) # new_values['pubdate']
# Upload to ScienceBase
if update_data:
	# Upload all files in dir that match basename of XML file
	# data_item = upload_data(sb, data_item, xml_file, replace=True, verbose=verbose)
	data_item, bigfiles1 = upload_files_matching_xml(sb, data_item, xml_file, max_MBsize=max_MBsize, replace=True, verbose=verbose)
	if bigfiles1:
		if not 'bigfiles' in locals():
			bigfiles = []
		else:
			bigfiles += bigfiles1
elif update_XML:
	# If XML was updated, but data was not uploaded, replace only XML.
	try:
		sb.replace_file(xml_file, data_item) # Does not update SB page to match metadata
	except e:
		print('Retry with update_data = True. pysb.replace_file() is not working for this use. Returned: \n'+e)
	# sb.upload_files_and_upsert_item(data_item, [xml_file])
if verbose:
	now_str = datetime.datetime.now().strftime("%H:%M:%S on %Y-%m-%d")
	print('Completed {} out of {} xml files at {}.\n'.format(cnt, xml_cnt, now_str))


"""
Tkinter learning
"""
# Button widget with counter
counter = 0
def counter_label(label):
  def count():
	global counter
	counter += 1
	label.config(text=str(counter))
	label.after(1000, count)
  count()

root = Tk() # Tk root widget initializes Tkinter. Appears as window with title bar after calling root.mainloop()
root.title("Counting Seconds")
label = Label(root, fg="green")
label.pack()
counter_label(label)
button = Button(root, text='Stop', width=25, command=root.destroy)
button.pack()

# Entry widget
master = Tk()
Label(master, text="First Name").grid(row=0)
Label(master, text="Last Name").grid(row=1)

e1 = Entry(master)
e2 = Entry(master)

e1.grid(row=0, column=1)
e2.grid(row=1, column=1)

mainloop( )

string = 'string'
json = {'json':1, 'hi':2}
type(string)
type(json)

#%% 1/9/18
# Orig:
xmllist = []
for root, dirs, files in os.walk(parentdir):
	for d in dirs:
	xmllist += glob.glob(os.path.join(root, d, '*.xml'))
d
root

# Revise the XML, except for the values created by SB
# Recursively list all XML files in parentdir
parentdir = r'/Volumes/stor/Projects/iPlover/iPlover_DR_2016/test_dir4upload' # OSX format
xmllist = glob.glob(os.path.join(parentdir, '**/*.xml'), recursive=True)
xml_file = xmllist[0]
xml_file
os.path.basename(os.path.split(xml_file)[0])
searchstr = xml_file.split('.')[0].split('_meta')[0] + '*browse*'
searchstr
browse_file = glob.glob(searchstr)[0]
new_values['browse_file'] = browse_file.split('/')[-1]


# Using pathlib
from pathlib import Path
p = Path(parentdir)
xmllist = list(p.glob('**/*.xml'))
xmllist
xml_file = xmllist[0]
xml_file
xml_file.parts
xml_file.root
xml_file.parent
xml_file.parents[1]
xml_file.parent.stem
xml_file.stem
xml_file.name

# Search for browse
searchstr = xml_file.stem.split('_meta')[0] + '*browse*'
try:
	browse_file = sorted(xml_file.parent.glob(searchstr))[0]
except:
	print("Couldn't find file matching the pattern '{}' in directory {} to add as browse image.".format(searchstr, xml_file.parent.stem))

searchstr = dataname + '*browse*'
xml_file.parent / searchstr

browse_file = glob.glob(xml_file.parent / searchstr)[0]

new_values ={}
new_values['browse_file'] = browse_file.name
new_values



####
#%% 2/14/18 - Restructure function to be more intuitive: go through each section of FGDC metadata
def map_newvals2xml(new_values):
# Create dictionary of {new value: {XPath to element: position of element in list retrieved by XPath}}
"""
To update XML elements with new text:
	for newval, elemfind in val2xml.items():
	for elempath, i in elemfind.items():
	metadata_root.findall(elempath)[i].text = newval
Currently hard-wired; will need to be adapted to match metadata scheme.
"""
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
accinstr = './distinfo/stdorder/digform/digtopt/onlinopt/accinstr'
metadate = './metainfo/metd' # Metadata Date
browsen = './idinfo/browse/browsen'
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
	val2xml[landing_link] = {lwork_link: 1}
# Data page URL
if 'child_id' in new_values.keys():
	# get URLs
	page_url = 'https://www.sciencebase.gov/catalog/item/{}'.format(new_values['child_id']) # data_item['link']['url']
	directdownload_link = 'https://www.sciencebase.gov/catalog/file/get/{}'.format(new_values['child_id'])
	# add values
	val2xml[page_url] = {citelink: 1, networkr: 0}
	val2xml[directdownload_link] = {networkr:1}
	access_str = 'The first link is to the page containing the data, the second link downloads all data available from the page as a zip file, and the third link is to the publication landing page.'
	val2xml[access_str] = {accinstr: 0}
	# Browse graphic
	if 'browse_file' in new_values.keys():
	browse_link = '{}/?name={}'.format(directdownload_link, new_values['browse_file'])
	val2xml[browse_link] = {browsen:0}
# Edition
if 'edition' in new_values.keys():
	val2xml[new_values['edition']] = {edition:0}
if 'pubdate' in new_values.keys():
	val2xml[new_values['pubdate']] = {pubdate:0, lwork_pubdate:0} # removed caldate
# Date and time of update
now_str = datetime.datetime.now().strftime("%Y%m%d")
val2xml[now_str] = {metadate: 0}

return val2xml




# digital transfer information
networkr = './distinfo/stdorder/digform/digtopt/onlinopt/computer/networka/networkr' # Network Resource Name
accinstr = './distinfo/stdorder/digform/digtopt/onlinopt/accinstr'
i = 0
acc_inst = 'The URLs in the network address section provide the following, respectively: '
if 'child_id' in new_values.keys():
	# link to containing page
	page_url = 'https://www.sciencebase.gov/catalog/item/{}'.format(new_values['child_id']) # data_item['link']['url']
	i = i
	update_xml_tagtext(metadata_root, page_url, networkr, i)
	acc_inst += 'Link number {} is to the page containing the data. '.format(i+1)
	# direct download everything on page
	directdownload_link = 'https://www.sciencebase.gov/catalog/file/get/{}'.format(new_values['child_id'])
	i += 1
	update_xml_tagtext(metadata_root, directdownload_link, networkr, i)
	acc_inst += 'Link number {} downloads all data available from the page as a zip file. '.format(i+1)
# link DOI, landing page
doi_url = "https://doi.org/{}".format(new_values['doi'])
i += 1
update_xml_tagtext(metadata_root, doi_url, networkr, i)
acc_inst += 'Link number {} downloads all data available from the page as a zip file. '.format(i+1)
