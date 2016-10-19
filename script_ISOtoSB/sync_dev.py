#!/usr/bin/env python
# encoding: utf-8
"""
update_keywords.py

Created by David L Blodgett on 2015-04-07.
"""

import sys
import os
import pysb
import shutil
from functions import get_item_iso_xml
from functions import put_item_iso_xml
from functions import clean_json
from lxml import etree
import argparse
import time

def putSbItemISO(iso_xml, parentId, sb):
    '''
        Invokes uploadFilesAndCreateItem then gets the item iso to make sure all is good.
    '''
    print 'putting item to SB'
    newItem = sb.uploadFilesAndCreateItem(parentId, iso_xml)
    print "Waiting..."
    time.sleep(5)
    try:
        addedFile=get_item_iso_xml(newItem,sb,'sb_iso_dev/')
    except Exception:
        print('error trying to get and reupload ' + newItem['id'])
    return newItem

def main():
    '''
        Removes all items from scienceBase dev and repopulates with what's on prod.
    '''
    import pysb
    import json
    import time
    parentId = '55240d6de4b0da4d0614a949' # beta sciencebase item id.
    sb = pysb.SbSession(env='beta').loginc("dblodgett@usgs.gov")
    query = sb._baseSbURL + "items?parentId=%s&format=json&max=1000" % (parentId)
    ret = sb._session.get(query)
    try:
      json = ret.json()
    except:
      raise Exception("Error parsing JSON response")
    for ident in json["items"]:
      item=sb.getSbItem(ident['id'])
      print 'deleting ' + ident['id']
      sb.deleteSbItem(item)
      time.sleep(1)
    if os.path.isdir('sb_iso_dev'):
        shutil.rmtree('sb_iso_dev')
    os.mkdir('sb_iso_dev')
    for iso in os.listdir('sb_iso'):
        if 'xml' in iso:
            iso=os.path.join('sb_iso',iso)
            item=putSbItemISO([iso], parentId, sb)

if __name__ == '__main__':
    
    main()