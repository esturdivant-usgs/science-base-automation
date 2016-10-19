#!/usr/bin/env python
# encoding: utf-8
"""
update_keywords.py

Created by David L Blodgett on 2015-04-07.
"""

import sys
import os
import pysb
from functions import get_item_iso_xml
from functions import put_item_iso_xml
from functions import clean_json
from lxml import etree
import argparse
import time

def main():
    '''
    Loops over items in the catalog, gets the ISO XML, parses it, 
    Loops over the keywords in the metadata and removes ones from the removeKeywordsLike list.
    Then re-ups the item-json and iso xml with updated keywords.
    '''
    keyword_list=[]
    workingDir = '/Users/dblodgett/Documents/Projects/GDP/4_Code/pysb_gdp_catalog'
    os.chdir(workingDir)
    sb = pysb.SbSession(env=env).loginc("dblodgett@usgs.gov")
    items=sb.findSbItems({'parentId':topLevelItemId,'max':'200'})
    print 'Found ' + str(len(items['items'])) + ' items.'
    for item in items['items']:
        changed_record=False
        # Get the item_json
        item_json=sb.getSbItem(item['id'])
        # Get the item_iso
        item_iso=get_item_iso_xml(item_json, sb, isoDir)
        # Loop through the keywords and remove onews in the removeKeywordsLike list.
        root=etree.parse(item_iso).getroot()
        for keyword in root.findall('{http://www.isotc211.org/2005/gmd}identificationInfo/{http://www.isotc211.org/2005/gmd}MD_DataIdentification/{http://www.isotc211.org/2005/gmd}descriptiveKeywords/{http://www.isotc211.org/2005/gmd}MD_Keywords/{http://www.isotc211.org/2005/gmd}keyword'):
            remove=False
            children=keyword.getchildren()
            for child in children:
                for pattern in removeKeywordsLike:
                    if child.text is not None and child.text==pattern:
                        remove=True
                        print 'remove ' + child.text + ' from xml'
                try: #change the keyword if it is in the keys of the changeKeyWordsTo dictionary.
                    temp=child.text
                    child.text=changeKeywordsTo[child.text]
                    print temp + ' changed to ' + child.text
                    changed_record=True
                except KeyError:
                    pass
            if remove==False: # Build a list of keywords that are left.
                keyword_list.append(child.text)
            item_json=sb.getSbItem(item['id'])
            tag_id=0
            for tag in item_json['tags']:
                for pattern in removeKeywordsLike:
                    if tag['name']==pattern:
                        print 'remove ' + tag['name'] + ' from json'
                        del item_json['tags'][tag_id]
                        changed_record=True
                try: #change the keyword if it is in the keys of the changeKeyWordsTo dictionary.
                    temp=tag['name']
                    item_json['tags'][tag_id]['name']=changeKeywordsTo[item_json['tags'][tag_id]['name']]
                    print temp + ' changed to ' + item_json['tags'][tag_id]['name']
                    changed_record=True
                except KeyError:
                    pass
            if remove: # actually remove from the xml.
                keyword.getparent().remove(keyword)
                changed_record=True
        for MD_keywords in root.findall('{http://www.isotc211.org/2005/gmd}identificationInfo/{http://www.isotc211.org/2005/gmd}MD_DataIdentification/{http://www.isotc211.org/2005/gmd}descriptiveKeywords/{http://www.isotc211.org/2005/gmd}MD_Keywords'):
            if len(MD_keywords.getchildren())==1 and MD_keywords.getchildren()[0].getchildren()[0].text==None:
                # Remove the empty MD_keywords section.
                print 'Removing empty keywords element' 
                MD_keywords.getparent().remove(MD_keywords)
                changed_record=True
        text_file = open(item_iso, "w")
        text_file.write(etree.tostring(root))
        text_file.close()
        # Note that put_item_iso_xml also uploads any changes to the item_json.
        if changed_record:
            item_json=put_item_iso_xml(item_json, sb, isoDir)
            item_json=clean_json(sb, item_id=item['id'])
        else:
            print 'No Change to: '+item['id']
    print keyword_list

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
    removeKeywordsLike=['gov.usgs.cida.gdp.wps.algorithm', 'Blodgett', 'CIDA', 'Center for Integrated', 'U.S. Department of the Interior', 'None', 
    'longitude', 'latitude', 'gov.usgs.cida.gdp.wps.algorithm.FeatureWeightedGridStatisticsAlgorithm',
    'gov.usgs.cida.gdp.wps.algorithm.FeatureGridStatisticsAlgorithm','gov.usgs.cida.gdp.wps.algorithm.FeatureCoverageOPeNDAPIntersectionAlgorithm',
    'featurecoverageopendapintersectionalgorithm', 'cida','gov.usgs.cida.gdp.wps.algorithm.featureweightedgridstatisticsalgorithm',
    'gov.usgs.cida.gdp.wps.algorithm.featuregridstatisticsalgorithm','gov.usgs.cida.gdp.wps.algorithm.featurecoverageopendapintersectionalgorithm',
    'projection_y_coordinate','projection_x_coordinate','A2','Air','April snowpack','Atmosphere','Atmospheric','Development','EARTH SCIENCE','EPSCoR Data','Growth','homogenization',
    'kriging','Maximum','METDATA','Minimum','Model','None','Prediction','Rise','Surface','time','United States','Various','Atmosphere,']
    changeKeywordsTo={'rain':'precipitation',
                      'temperature':'air temperature atmosphere',
                      'air_temperature':'air temperature',
                      'air temperature atmosphere':'air temperature',
                      'Air Temperature Atmosphere':'air temperature',
                      'Atmosphere > Precipitation > Precipitation Amount   Atmosphere > Precipitation > Rain':'precipitation',
                      'Atmospheric Temperature':'air temperature',
                      'Atmospheric Temperature > Air Temperature Atmosphere > Precipitation > Rain > Maximum Daily Temperature > Minimum Daily Temperature':'air temperature',
                      'Atmospheric Winds':'wind',
                      'CIG':'Climate Impacts Group University of Washington College of the Environment',
                      'daily downward shortwave solar radiation':'downward shortwave solar radiation',
                      'daily maximum relative humidity':'maximum relative humidity',
                      'daily maximum temperature':'maximum temperature',
                      'daily minimum relative humidity':'minimum relative humidity',
                      'daily minimum temperature':'minimum temperature',
                      'daily precipitation':'precipitation',
                      'daily precipitation duration':'precipitation duration',
                      'daily specific humidity':'specific humidity',
                      'daily wind direction':'wind direction',
                      'daily wind speed':'wind speed',
                      'Downscaled Climate Projection':'downscaled climate projection',
                      'Dynamical Downscaling':'dynamical downscaling',
                      'Gridded Hydrological Data':'gridded hydrological data',
                      'Gridded Meteorological Data':'gridded meteorological data',
                      'LAND SURFACE':'landscape',
                      'LAND USE/LAND COVER':'land use / land cover',
                      'Maximum Daily Temperature':'maximum temperature',
                      'Minimum  Daily Temperature':'minimum temperature',
                      'PNW':'Pacific Northwest',
                      'Precipitation':'precipitation',
                      'precipitation_amount':'precipitation',
                      'precipitation_flux':'precipitation',
                      'Rain':'precipitation',
                      'Sea Level Rise':'sea level rise',
                      'Sea-Level':'sea level rise',
                      'specific_humidity':'specific humidity',
                      'Surface Winds Atmosphere':'wind',
                      'surface_downwelling_shortwave_flux_in_air':'downward shortwave solar radiation',
                      'Temperature':'air temperature',
                      'Urbanization':'urbanization',
                      'Western U.S.':'Western United States',
                      'wind_speed':'wind speed',
                      'Winds':'wind',
                      'Atmosphere > Precipitation > Precipitation Amount Atmosphere > Precipitation > Rain':'precipitation',
                      'Temperature,':'air temperature',
                      'Precipitation,':'precipitation'}
                      
    main()