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


"<crossref>
			<citeinfo>
				<origin>Robert A. Morton</origin>
				<origin>Tara L. Miller</origin>
				<pubdate>2005</pubdate>
				<title>National Assessment of Shoreline Change: Part 2 Historical Shoreline Changes and Associated Coastal Land Loss along the U.S. Southeast Atlantic Coast</title>
				<serinfo>
					<sername>Open-File Report</sername>
					<issue>2005-1401</issue>
				</serinfo>
				<pubinfo>
					<pubplace>Reston, VA</pubplace>
					<publish>U.S. Geological Survey</publish>
				</pubinfo>
				<onlink>http://pubs.usgs.gov/of/2005/1401/</onlink>
			</citeinfo>
		</crossref>"
