# science-base-automation
Experiments with automating data releases
README for sb_automation.py
Automatically create ScienceBase pages with updated metadata
By: Emily Sturdivant, esturdivant@usgs.gov
Last modified: 11/17/16

README for sb_automation.py	1
Overview	1
Overall process	2
Limitations	2
How to execute, from the top:	2
1. Set up a local directory structure for your data release.	2
2. Set up a ScienceBase landing page.	2
3. Get the script and modify parameters.	3
4. Install python modules.	3
Requirements	3
How:	3
5. Run the script!	4
What the script is doing:	4
Background	4
Terms	4
Directory structure	5
Local directories and files	5
ScienceBase pages	6
ScienceBase features	6

Overview
Given a local top directory with metadata and data files in sub-directories and a ScienceBase (SB) landing page, this script creates SB pages mimicking the directory structure, updates the XML files with new SB links, populates the SB pages from the data. 

This How-to is written for OSX, but there should only be a few adjustments for it to run on Windows.

Below is an overview of terms I use and notes on ScienceBase features. 
Overall process
Set up a local directory structure for your data release. 
Set up a ScienceBase landing page. 
Get the script and modify parameters.
Install python modules.
Run.
Check ScienceBase pages and make manual modifications. 
Limitations
(besides soon-to-be-discovered bugs)
It only uploads shapefile (including dbf) and XML files. This will be easy to modify; it just hasn’t been done yet. 
The metadata population routine is hard-coded to a specific metadata template, which should match the structure created by TKME.
The bounding box routine is not consistently successful. 
The script will overwrite XML files. In the future, it may include a means to archive the original XML files. 
How to execute, from the top:
1. Set up a local directory structure for your data release. 
See below for an explanation of how SB pages will mimic the directory structure.
Each directory name will become the title of a ScienceBase page except for the top directory/landing page. 
Ensure there is one and only one XML file for each desired SB page. These XML files should pass MP error checking. 
NOTE: The script will overwrite XML files. You may want to save a separate archive of the original XML files. 
2. Set up a ScienceBase landing page. 
Create the data release landing page before running the script. 
Begin either by uploading an XML file to the File section, which SB will use to automatically populate fields or go straight to working manually with the page. Make manual revisions, such as to the citation, the body, the purpose, etc. If desired, create a preview image by uploading an image to the File section; this will automatically be used as the preview image. You can choose any of these fields to be copied over to child pages (including the preview image). 
It is also possible for the script to automatically create the SB page from an XML file. If desired, that file should be checked for errors using MP and placed in the top directory. 
3. Modify parameters in configuration script.
Open config_autoSB.py in your Python/text editor and revise the value of each input variable as indicated in the comments.
Input variables that must be updated before running: 
useremail (SB username)
landing_link (URL for SB landing page)
parentdir (path to top directory)
OSX
Windows
dr_doi (data release DOI)
Specify which fields will be “inherited” between pages in the following optional lists:
landing_fields_from_xml – landing page fields that will populate from the top XML
subparent_inherits – fields that aggregate pages copy (inherit) from the landing page
data_inherits – fields that data pages inherit from their immediate parent page
Choose which processes to conduct. The default values will suit most purposes, but these fields allow you to tune the processes to save time. 
update_landing_page
replace_subpages 
update_subpages 
update_XML 
update_data 
4. Install python modules (lxml, pysb).
sb_automation was written and tested in Python 2.7 on both OSX and Windows. Python packages required that are not automatically included in python installation are lxml and pysb. It uses the standard python modules os, glob, json, pickle, and sys. Install lxml and pysb using pip and git.
>>> easy_install pip
>>> pip install lxml 
>>> pip install -e git+https://my.usgs.gov/stash/scm/sbe/pysb.git#egg=pysb

Using Conda (install Anaconda or Miniconda; requires Git)
On OSX, in Terminal:
conda create -n sciencebase python=2.7 lxml 
source activate sciencebase
pip install -e git+https://my.usgs.gov/stash/scm/sbe/pysb.git#egg=pysb
	On Windows, in cmd: 
		conda create -n sciencebase python=2.7 lxml 
activate sciencebase
pip install -e git+https://my.usgs.gov/stash/scm/sbe/pysb.git#egg=pysb
5. Run script sb_automation.py! 
In your bash console: 
>>> cd [script_dir = path to script]
>>> python sb_automation.py
From Finder.
Right click and run with your python launcher of choice. 
In your Python IDE of choice:
Open the script and run it line by line or however you choose. 
What the script does:
Starts a ScienceBase session. 
Works in the landing page and top directory as specified by the input parameters.
Loops through the sub-directories to create or find a matching SB page. 
For each sub-directory, it checks for a matching child page (child title==directory name and parent page=parent directory). If the child does not already exist, it creates a new page. For each page (regardless of whether it already existed), it copies fields from the landing page, as indicated in the input parameters. 
Loops through the XML files to create or find a data page. For each XML file (excluding the landing page XML), it 
creates (or finds) a data page, 
revises the XML to include the URL of the data page, the DOI, and the URL of the landing page, 
uploads the shapefile files to the new page, and 
copies fields from the parent page to the data page as indicated in the input parameters.
Sets bounding box coordinates for parents based on the spatial extent of the data in their child pages. 
During processing it stores values in three dictionaries, which are then saved in the top directory as a time-saving measure for future processing. 

Background
Terms
landing page: the top-level ScienceBase page of the data release. The DOI will direct here. Corresponds to the local top directory.
top directory: the top local directory housing all files in the data release. Corresponds to the SB landing page.
data pages: the final page/s in a page chain that holds the data files. 
[aggregate] pages: the mid-level pages that organize data pages
parent and child [pages or directories]: relational terms for page at any level of the hierarchy. Parent always contains the child. Corresponds to __ and __ directories
item: SB JSON item. The JSON-formatted version of a given page.
field: One piece of a SB page. Fields include title, citation, body… Field values will be displayed under the headings on a SB page. Examples:
citation – Recommended citation for the data release. ScienceBase will automatically populate using the XML, but this may not agree with our format. 
body = abstract. The summary will automatically be created from body.
purpose
previewImage – aka. browse graphic. SB will automatically use an image file uploaded to the page. 
summary – this is automatically populated based on the body.
element: One piece of an XML file. XML holds nested elements that are specified by tags. Also a class in lxml. Elements can be referenced by the tags and the values are the text __ property of the element. 

Directory structure
Each directory will become a ScienceBase page within your data release. The directories will maintain their hierarchy. Each (error-free) XML file will populate a ScienceBase page. If a directory contains a single XML file, the corresponding ScienceBase page will be populated with that XML file. If the directory contains multiple XML files, each XML will become a child page linked on the page corresponding to its parent directory. ScienceBase pages that correspond to directories will use the directory name as their title. ScienceBase pages that correspond to XML files will use the Title in the metadata (Identity Information > Citation > Citation Information > Title) as their title. Pages that correspond to directories with a single XML file will still use the directory name rather than the metadata title. Here is an example of how a local file structure will become a ScienceBase page structure:
Local directories and files
DATA_RELEASE_1 - top directory
> North Carolina - sub-directory
      > NC Central - sub-directory
> NCcentral_baseline.cpg - 1st data file
	> NCcentral_baseline.dbf - 1st data file
	> NCcentral_baseline.prj - 1st data file
	> NCcentral_baseline.sbn - 1st data file
	> NCcentral_baseline.shp - 1st data file
	> NCcentral_baseline.shp.xml - metadata for 1st data file
		“<idinfo><citation><citeinfo><title>Coastal baseline for North Carolina…</title></citeinfo></citation></idinfo>” - excerpt of title element from within metadata file
	> NCcentral_baseline.shx - 1st data file
> NCcentral_shorelines.cpg - 2nd data file
	> NCcentral_shorelines.dbf - 2nd data file
	> NCcentral_shorelines.prj - 2nd data file
	> NCcentral_shorelines.sbn - 2nd data file
	> NCcentral_shorelines.shp - 2nd data file
	> NCcentral_shorelines.shp.xml - metadata for 2nd data file
		“<idinfo><citation><citeinfo><title>Shorelines of North Carolina…</title></citeinfo></citation></idinfo>” - excerpt of title element from within metadata file
	> NCcentral_shorelines.shx - 2nd data file
ScienceBase pages
Shorelines of U.S. Atlantic - landing page
> North Carolina - sub-page
     > NC Central - sub-page
	> Coastal baseline for North Carolina… - data page
> Shorelines of North Carolina… - data page
ScienceBase features
Intelligent content from uploaded files
ScienceBase automatically detects the file type and in some cases the contents of uploaded files and makes intelligent decisions about how to use them. For instance, an image file uploaded to a page will be used as the preview image. It will pull information from an XML file to populate fields, and it will detect components of a shapefile or raster file and present them as a shapefile or raster “facet”, which can be downloaded as a package. Even if an XML file is later removed from the Files, the fields populated from it will remain.
Direct download 
SB has a URL for direct download of all files from a page. It is https://www.sciencebase.gov/catalog/file/get/[item ID] 
There is also the option for direct download of a single file, which adds a query onto the get file URL: https://www.sciencebase.gov/catalog/file/get/[item ID]/?name=[file name]. However, this should only be used when the data has been zipped before upload to ensure that a user retrieves all necessary files (including metadata). 
If a facet was created, a URL for direct download of the all files in the facets can be retrieved from the JSON item.
