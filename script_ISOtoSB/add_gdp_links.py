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

def link_check(item_json):
    change=False
    if 'webLinks' in item_json.keys():
        for i, link in enumerate(item_json['webLinks']):
            if 'client/catalog' in item_json['webLinks'][i]['uri']:
                print item_json['webLinks'][i]['uri']
                item_json['webLinks'][i]['uri']=item_json['webLinks'][i]['uri'].replace('client/catalog', 'client/#!catalog')
                print item_json['webLinks'][i]['uri']
                change=True
    return {'item_json':item_json,'changed':change}

def link_check_add(link_dict,item_json):
    change=False
    found = False
    url=link_dict['uri']
    if 'webLinks' in item_json.keys():
        for i, link in enumerate(item_json['webLinks']):
            if link['type']=='webLink' and link['uri']==url:
                if found:
                    del item_json['webLinks'][i]
                    print 'removed a dup'
                    change=True
                else:
                    found=True
    else:
        item_json['webLinks']=[]
    if not found:
        item_json['webLinks'].append(link_dict)
        change=True
    return {'item_json':item_json,'changed':change}


def main():
    workingDir = '/Users/dblodgett/Documents/Projects/GDP/4_Code/pysb_gdp_catalog'
    os.chdir(workingDir)
    sb = pysb.SbSession(env=env).loginc("dblodgett@usgs.gov")
    items=sb.findSbItems({'parentId':topLevelItemId,'max':'200'})
    print 'Found ' + str(len(items['items'])) + ' items.'
    for item in items['items']:
        change=False
        # Get the item_json
        item_json=sb.getSbItem(item['id'])
        gdp_url='http://cida.usgs.gov/gdp/client/catalog/gdp/dataset/'+item['id']
        sb_url='https://www.sciencebase.gov/catalog/item/'+item['id']+'?community=Geo+Data+Portal+Catalog'
        link_dicts=[{'type':'webLink','typeLabel':'Web Link','uri':gdp_url,'title':'Access Dataset in the Geo Data Portal','hidden':False},
                    {'type':'webLink','typeLabel':'Web Link','uri':sb_url,'title':'Access Additional Dataset Metadata','hidden':False}]
        for link_dict in link_dicts:
            link_add=link_check_add(link_dict, item_json)
            item_json=link_add['item_json']
            if not change:
                change=link_add['changed']
        link_change=link_check(item_json)
        item_json=link_change['item_json']
        if not change:
            change=link_change['changed']
        print item_json['webLinks']
        if change:
            print 'change'
            item_json=sb.updateSbItem(item_json)


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