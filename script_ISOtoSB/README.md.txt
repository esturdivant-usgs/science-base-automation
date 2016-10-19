Scripts to push new and changed records for the Geo Data Portal catalog to ScienceBase.
To set up venv:

mkdir venv
virtualenv -p /usr/bin/python2.7 venv
source venv/bin/activate
pip install -r requirements.txt


There are three functions defined in functions.py that get ISO XML from a record, put ISO XML into a record, and a third that cleans up in case ScienceBase does something wrong.
old_scripts contains scripts that are for reference, used in the past but no longer re-usable in particular.
sb_iso contains the ISO files that are currently in the GDP catalog on ScienceBase. These should be checked in after every change.
sb_iso_dev contains ISO files from the beta sciencebase GDP community, they may not be in sync with beta but are there for development purposes.