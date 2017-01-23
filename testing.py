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


sb = log_in(useremail)
parentitem.keys() = flexibly_get_item(sb, dict_DIRtoID['NCwest'])
parentitem['webLinks']=[{'uri':'doi.gov/oinoknoinoinoinoinoinoin'}]
dr_doi = get_DOI_from_item(flexibly_get_item(sb, dict_DIRtoID[d]))
