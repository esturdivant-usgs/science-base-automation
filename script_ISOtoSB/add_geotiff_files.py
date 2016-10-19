#!/usr/bin/env python
# encoding: utf-8
"""
add_gdp_links.py

Created by David L Blodgett on 2015-09-01.
Copyright (c) 2015 __MyCompanyName__. All rights reserved.
"""

import sys
import os
import argparse
import pysb
from functions import put_item_geotiff

def main():
    workingDir = '/Users/dblodgett/Documents/Projects/GDP/4_Code/pysb_gdp_catalog'
    os.chdir(workingDir)
    sb = pysb.SbSession(env=env).loginc("dblodgett@usgs.gov")
    items=sb.findSbItems({'parentId':topLevelItemId,'max':'200'})
    print 'Found ' + str(len(items['items'])) + ' items.'
    for item in items['items']:
        # Get the item_json
        item_json=sb.getSbItem(item['id'])
        item_json=put_item_geotiff(item_json, sb, 'geotiffs')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('tier', type=str)
    args = parser.parse_args()
    tier_name = args.tier.lower()
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
    main()