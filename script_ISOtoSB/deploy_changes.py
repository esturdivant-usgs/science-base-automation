#!/usr/bin/env python
# encoding: utf-8
"""
update_keywords.py

Created by David L Blodgett on 2015-04-07.
"""

import sys
import os
import pysb
import json
import shutil
from functions import get_item_iso_xml
from functions import put_item_iso_xml
from functions import clean_json
from lxml import etree
import argparse
import time

def updateItem(item_json, sb, isoDir):
    try:
        item_json=sb.updateSbItem(item_json)
        item_json=put_item_iso_xml(item_json, sb, isoDir)
        item_json=clean_json(sb, item_id=item_json['id'])
    except Exception:
        print 'something is wrong with ' + item_json['id']

def main():
    '''
        Pushes up all the records in the sb_iso directory or the one that is passed in.
    '''
    parser = argparse.ArgumentParser()
    parser.add_argument('tier', type=str)
    parser.add_argument('--itemID', type=str, default='none', required=False)
    args = parser.parse_args()
    tier_name = args.tier.lower()
    itemID = args.itemID
    if tier_name == 'beta':
        env='beta'
        topLevelItemId = '55240d6de4b0da4d0614a949'
        isoDir='sb_iso_dev/'
        print 'Using beta sciencebase.'
    elif tier_name == 'prod':
        env=None
        topLevelItemId = '54dd2326e4b08de9379b2fb1'
        isoDir='sb_iso/'
        print 'This may edit the production catalog, you better be sure.'
    else:
        raise Exception('You must choose "beta" or "prod".')
    sb = pysb.SbSession(env=env).loginc("dblodgett@usgs.gov")
    if itemID!='none':
        item_json=sb.getSbItem(itemID)
        print itemID
        updateItem(item_json, sb, isoDir)
    else:
        items=sb.findSbItems({'parentId':topLevelItemId,'max':'200'})
        print 'Found ' + str(len(items['items'])) + ' items.'
        for item in items['items']:
            print item['id']
            # Get the item_json
            item_json=sb.getSbItem(item['id'])
            updateItem(item, sb, isoDir)
        
if __name__ == '__main__':
    
    main()
