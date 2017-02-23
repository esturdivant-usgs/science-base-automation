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
import pysb # Install on OSX with "pip install -e git+https://my.usgs.gov/stash/scm/sbe/pysb.git#egg=pysb"
import os
import glob
from lxml import etree
import json
import pickle
import sys
#sb_auto_dir = os.path.dirname(os.path.realpath(__file__))
sb_auto_dir = os.path.dirname(os.path.realpath('sb_automation.py'))
sys.path.append(sb_auto_dir) # Add the script location to the system path just to make sure
from autoSB import *
from config_autoSB import *


os.path.join(parentdir,'id_to_json.json')

os.path.isfile(os.path.join(parentdir,'id_to_json.json'))
