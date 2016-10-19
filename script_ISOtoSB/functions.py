#!/usr/bin/env python
# encoding: utf-8
"""
functions.py

Created by David L Blodgett on 2015-04-07.
Copyright (c) 2015 __MyCompanyName__. All rights reserved.
"""

import sys
import os
from owslib.etree import etree
import pysb
import time

def get_item_iso_xml(item_json, sb, isoDir):
    '''Get an iso xml file from a record and do some cleanup along the way.

        This function will try to get a file from a sciencebase item with a contentType
        of "application/vnd.iso.19115+xml". If one does not exist, it will look for an
        existing iso xml file that has the same id as the sciencebase item in question
        and attempt to upload it. If it finds one, it downloads the file and makes sure that
        it will parse and has an identifier that matches the ScienceBase ID. If the sciencebase
        id and the iso file id don't match, it will make them match and upload the file.
        It will then write the file to disk in the sb_iso folder.

        Positional Arguments:
        item_json -- The pysb json for an item.
        sb -- An initialized pysb object.
        isoDir -- A directory where the iso files are stored.
    '''
    outFile=isoDir+item_json['id']+'.xml'
    fileID=0
    found=False
    try:
        while found==False:
            if item_json['files'][fileID]['contentType'] == "application/vnd.iso.19115+xml":
                found=True
            else:
                fileID+=1
    except (IndexError, KeyError):
        print 'ISO file not found, trying to add one if we have it.'
        if os.path.isfile(outFile):
            print outFile
            item_json=sb.uploadFileToItem(item_json, outFile)
        else:
            raise Exception("ISO file not found and we don't have one to replace it with, item "+item_json['id'])
    workingFile=sb.downloadFile(item_json['files'][fileID]['url'],outFile)
    parsedFile=etree.parse(workingFile)
    root=parsedFile.getroot()
    check=0
    changed=False
    for el in root.findall('{http://www.isotc211.org/2005/gmd}fileIdentifier/{http://www.isotc211.org/2005/gco}CharacterString'):
        if el.text!=item_json['id']:
            if check>1:
                raise Exception('too many fileIdentifiers!')
            el.text=item_json['id']
            print 'modified id of item ' + item_json['id']
            changed=True
        text_file = open(outFile, "w")
        text_file.write(etree.tostring(root))
        text_file.close()
        if changed==True:
            item_json=put_item_iso_xml(item_json, sb, isoDir)
        check+=1
    if check != 1:
        raise Exception('A metadata record without a fileIdentifier was found in item '+item['id'])
    return outFile

def put_item_iso_xml(item_json, sb, isoDir):
    '''Put an ISO XML file to a ScienceBase item that already has one.

        This function looks for a file with contentType "application/vnd.iso.19115+xml"
        in a sciencebase item. It then tries to remove the file from the item and
        reuploads the matching one from disk. It will do nothing and exit if it can't
        find a corresponding file on disk.

        Positional Arguments:
        item_json -- The pysb json for an item.
        sb -- An initialized pysb object.
        isoDir -- A directory where the iso files are stored.
    '''
    files=[]
    iso_file=item_json['id']+'.xml'
    outFile=isoDir+iso_file
    if 'files' in item_json:
        found=False
        fileID=0
        while found==False:
            if item_json['files'][fileID]['contentType'] == "application/vnd.iso.19115+xml":
                item_json['files'].pop(fileID)
                found=True
            else:
                fileID+=1
        if os.path.isfile(outFile)==False:
            raise Exception('There is no file that matches this item!!!')
        try:
            # print 'removing file'
            item_json=sb.updateSbItem(item_json)
            # print 'reuploading file'
            item_json=sb.uploadFileToItem(item_json, outFile)
        except Exception:
            print 'something went wrong reuploading '+iso_file + ' Trying to upload a few more times.'
            success=False
            tries=0
            while success==False:
                try:
                    item_json=sb.uploadFileToItem(item_json, outFile)
                    success=True
                except Exception:
                    tries=tries+1
                    time.sleep(5)
                if tries>10:
                    raise Exception('failed to upload file to the item')

    else:
        if os.path.isfile(outFile)==False:
            raise Exception('something went very wrong, no iso file found in the existing record.')
        else:
            print 'missing xml file in is record, trying to upload one we have file'
            item_json=sb.uploadFileToItem(item_json, outFile)
    return item_json

def put_item_geotiff(item_json, sb, geotiffDir):
    '''Put geotiff file to a ScienceBase item as a RasterFacet.

        This function looks for an OPeNDAP facet url then searches for a
        geotiff file that matches the geo data portal pattern for such
        files. It uploads the geotiff file and an sld to go with it then moves
        the pair into a new RasterFacet.

        Positional Arguments:
        item_json -- The pysb json for an item.
        sb -- An initialized pysb object.
        geotiffDir -- A directory where the geotiff files are stored.
    '''
    facet_id=0
    print(item_json['id'])
    while facet_id < len(item_json['facets']):
        if 'url' in item_json['facets'][facet_id].keys() and 'dodsC' in item_json['facets'][facet_id]['url']:
            found=False
            lookupStr=item_json['facets'][facet_id]['url'].split('dodsC')[-1][1:]
            filename=lookupStr.replace('/','_')+'.tif'
            geotiffFile=os.path.join(geotiffDir, lookupStr.replace('/','_')+'.tif')
            sldFile=os.path.join(geotiffDir, 'ColorRamp.SLD')
            if os.path.isfile(geotiffFile):
                print(geotiffFile)
                geotiff_facet_id=0
                # Look for pre-existing geotiff facet.
                while geotiff_facet_id < len(item_json['facets']):
                    if item_json['facets'][geotiff_facet_id]['className'] == 'gov.sciencebase.catalog.item.facet.RasterFacet':
                        if item_json['facets'][geotiff_facet_id]['files'][0]['name'] == filename:
                            print('found')
                            found=True
                    geotiff_facet_id+=1
                if not found:
                    # Upload but don't replace the item_json. Note that the sleeps are to give sciencebase a chance to do its thing in the background.
                    temp_json=sb.uploadFileToItem(item_json, geotiffFile)
                    time.sleep(2)
                    # Upload an sld to the temp_json
                    temp_json=sb.uploadFileToItem(temp_json, sldFile)
                    time.sleep(2)
                    # Build a new RasterFacet
                    facet = {}
                    facet['className'] = 'gov.sciencebase.catalog.item.facet.RasterFacet'
                    facet['rasterType'] = 'GeoTIFF'
                    facet['name'] = lookupStr.replace('/','_')
                    facet['files']=[]
                    add=False # These are defensive checks for something out of place that needs to be fixed by hand.
                    addSLD=False
                    for file_json in temp_json['files']: # looping over the files in the item. Note assumptions in Exceptions.
                        if file_json['name']=="file" and file_json['contentType']=="image/tiff":
                            if add:
                                raise Exception('Assumes only one geotiff file named file at a time.')
                            file_json['name']=filename
                            facet['files'].append(file_json)
                            add=True
                        if file_json['name']=="ColorRamp.SLD" and file_json['contentType']=="application/sld+xml":
                            if addSLD:
                                raise Exception('Assumes only one SLD file named file at a time.')
                            file_json['name']=filename+'-'+'ColorRamp.SLD'
                            facet['files'].append(file_json)
                            addSLD=True
                    if 'facets' not in item_json.keys():
                        item_json['facets']=[]
                    item_json['facets'].append(facet)
                    item_json=sb.updateSbItem(item_json)
                    time.sleep(2)
        facet_id+=1
    return item_json


def clean_json(sb, item_id=None,item_json=None):
    '''Cleans up after a bug in sciencebase.

    It looks at facets with URLs and capabilitiesUrls.
    If it has seen the url before it removes the facet and reuploads the item json.
    It also checks to see if there are two or more iso records in the item. It deletes all but the newest one.

    Positional Arguments:
    sb -- An initialized pysb object.

    Keyword Arguments:
    item_id -- A ScienceBase Item ID. (Default: None)
    item_json -- The pysb json for an item. (Default: None)
    '''
    if item_id is not None:
        item_json=sb.getSbItem(item_id)
    elif item_json is None:
        raise Exception('Must give clean_json something to work with.')
    facet_urls=[]
    facet_id=0
    change=False
    while facet_id < len(item_json['facets']):
        if 'url' in item_json['facets'][facet_id]:
            if 'dods://' in item_json['facets'][facet_id]['url']:
                item_json['facets'][facet_id]['url']=item_json['facets'][facet_id]['url'].replace('dods://','http://')
                # print 'changed dods'
            if any(item_json['facets'][facet_id]['url'] in u for u in facet_urls):
                # print 'Found a duplicate facet. Removing it.'
                # print 'Removing ' + item_json['facets'][facet_id]['url']
                del item_json['facets'][facet_id]
                change=True
            else:
                facet_urls.append(item_json['facets'][facet_id]['url'])
                # print 'leaving ' + item_json['facets'][facet_id]['url'] + ' in.'
                facet_id=facet_id+1
                # print facet_urls
        elif 'capabilitiesUrl' in item_json['facets'][facet_id]:
            if any(item_json['facets'][facet_id]['capabilitiesUrl'] in u for u in facet_urls):
                # print 'Removing ' + item_json['facets'][facet_id]['capabilitiesUrl']
                del item_json['facets'][facet_id]
                change=True
            else:
                facet_urls.append(item_json['facets'][facet_id]['capabilitiesUrl'])
                # print 'leaving ' + item_json['facets'][facet_id]['capabilitiesUrl'] + ' in.'
                facet_id=facet_id+1
                # print facet_urls
        else:
            # print 'no url in facet'
            facet_id=facet_id+1
    fileId=0
    found=False
    if 'files' in item_json:
        while fileId < len(item_json['files']):
            if found==True:
                # print 'found a duplicate ISO record for this item, deleting it.'
                del item_json['files'][fileId]
                fileId+=1
            elif item_json['files'][fileId]['contentType'] == "application/vnd.iso.19115+xml":
                found=True
                fileId+=1

    if change==True:
        # print 'putting item_json'
        item_json=sb.updateSbItem(item_json)