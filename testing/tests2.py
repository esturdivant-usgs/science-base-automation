

in_metadata = r"D:\DeepDive\5_datarelease_packages\vol1\sb_upload_test\fiis14\DisMOSH and others\FI15_DisMOSH_Cost_MOSHShoreline_meta.xml"

#%% Remove digforms with fills
xml_file = in_metadata
metadata_root, tree, xml_file = get_root_flexibly(in_metadata)
# Wait up to 5 seconds for the child items to be deleted
start = datetime.datetime.now()
duration = 0
while duration < 6:
    duration = (datetime.datetime.now() - start).seconds
    try:
        remove_xml_element(metadata_root, './distinfo/stdorder/digform', "XXX")
        break
    except:
        pass
tree.write(xml_file)





#%% Get values from data item for each digform
for distlink in data_item['distributionLinks']:
    uri = distlink['uri']
    title = distlink['title']
    print([title, uri])
    if title == 'Download Attached Files':
        formname = 'ZIP'
        sz = sum([f['size'] for f in distlink['files']]) / 1000000
        print([formname, sz])
