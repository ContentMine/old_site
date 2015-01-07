import json, requests, uuid, time, subprocess
from datetime import datetime
from lxml import etree

urls = open('anadarko','r')
regexurl = 'company_tagger.xml'
target = 'http://localhost:9200/contentmine/fact/'

'''try:
    toremove = requests.get(target + '_search?size=1000000&q=berlin.exact:"yes"').json()
    print 'deleting ', toremove['hits']['total']
    for r in toremove['hits']['hits']:
        if 'id' in r['_source'] and r['_source']['id']:
            requests.delete(target + str(r['_source']['id']))
except:
    pass'''

counter = 0
ranonurls = 0
amisuccess = 0
hitscore = 0
failures = []

for url in urls:
    counter += 1
    url = url.strip().replace('\n','')
    print counter, url
    # call AMI on the url if it is an htm or xml
    if url.endswith('.htm') or url.endswith('.xml'):
        ranonurls += 1
        # run AMI on the file
        co = [
            'ami-regex',
            '-i',
            url,
            '-g',
            regexurl
        ]
        p = subprocess.Popen(co, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        out, err = p.communicate()

        if err:
            failures.append(url)
        else:
            amisuccess += 1
            # find and read the output file
            outputfile = 'target/null.xml/results.xml'        

            ns = etree.FunctionNamespace("http://www.xml-cml.org/ami")
            ns.prefix = "zf"
            tree = etree.parse(outputfile)
            hits = tree.xpath('//zf:hit')
            for hit in hits:
                hitscore += 1
                doc = {
                    'retrieved_by': 'ami-regex-berlin',
                    'retrieved_date': datetime.now().strftime("%Y-%m-%d %H%M")
                }
                doc["pre"] = hit.get("pre")
                doc["fact"] = hit.get("word")
                doc["post"] = hit.get("post")
                doc['id'] = uuid.uuid4().hex
                doc['file'] = url
                doc['berlin'] = 'yes'
                doc['company'] = 'yes'
                doc['keywords'] = requests.get('http://cottagelabs.com/parser?blurb="' + doc['pre'] + ' ' + doc['fact'] + ' ' + doc['post'] + '"').json()
                requests.post(target + str(doc['id']), data=json.dumps(doc))
                time.sleep(0.05)

print ranonurls, amisuccess
print hitscore
print len(failures)