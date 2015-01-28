
import requests, os, subprocess, time, shutil, json
from datetime import datetime, timedelta
from xml.etree import ElementTree as ET
from lxml import etree


def merge(old,new):
    print "merging"
    for k, v in new.items():
        if k not in old:
            old[k] = v
    return old


def daily(cid,tags=[]):
    # retrieve the catalogue record created by the daily journaltocs scrape
    print "getting catalogue record"
    try:
        rec = requests.get('http://localhost:9200/contentmine/catalogue/' + cid).json()['_source']
    except:
        return {"errors": "this ID does not exist in our catalogue"}
    
    d = '/opt/contentmine/src/site/portality/static/scraping/'
    outputdirectory = d + cid
    if not os.path.exists(outputdirectory): os.makedirs(outputdirectory)
    url = rec['link'][0]['url']

    # run quickscrape to get metadata
    print "quickscrape"
    co = [
        '/usr/bin/quickscrape',
        '--output',
        outputdirectory,
        '--scraper',
        '/opt/contentmine/src/journal-scrapers/scrapers/plos.json',
        '--url',
        url
    ]
    p = subprocess.Popen(co, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    out, err = p.communicate()        
    if err:
        print 'quickscrape error ', err
        return {"errors": err}
    else:
        slug = url.replace('://','_').replace('/','_').replace(':','')
        b = json.load(open(outputdirectory + '/' + slug + '/results.json','r'))
        rec = merge(rec,b)
        requests.post('http://localhost:9200/contentmine/catalogue/' + cid, data=json.dumps(rec))
        for fl in os.listdir(outputdirectory + '/' + slug):
            shutil.copy(os.path.join(outputdirectory + '/' + slug, fl), outputdirectory)
        shutil.rmtree(outputdirectory + '/' + slug)

    # run norma to get a normalised version of the xml file ready for processing
    print "norma"
    fulltext = outputdirectory + 'fulltext.xml'
    normal = outputdirectory + 'normalised.html'
    co = [
        'norma',
        '-i',
        fulltext,
        '-x',
        '/opt/contentmine/src/norma/src/main/resources/org/xmlcml/norma/pubstyle/nlm/toHtml.xsl',
        '-o',
        normal
    ]
    p = subprocess.Popen(co, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    out, err = p.communicate()
    if err:
        print 'norma error ', err
        return {"errors": err}

    # a list to start collecting facts in
    facts = []

    # run species
    print "species"
    co = [
        '/usr/bin/ami-species',
        '-i',
        normal,
        '-e',
        'xml'
    ]
    p = subprocess.Popen(co, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    out, err = p.communicate()
    if err:
        print 'ami-species error ', err
        return {"errors": err}
    shutil.move('target/fulltext.xml/results.xml', outputdirectory + 'species_results.xml')
    species_results = outputdirectory + 'species_results.xml'
    tree = ET.parse(species_results).getroot()
    elems = tree.find('results')[1:]
    for sub in elems:
        part = sub.find('eic')
        doc = {'eic': part.get('xpath')}
        doc["pre"] = part.find("pre").text
        doc["fact"] = part.find("value").text
        doc["post"] = part.find("post").text
        facts.append(doc)

    # run regex (using a concatenated file of all current regexes, which needs produced somehow)
    print "regex"
    co = [
        '/usr/bin/ami-regex',
        '-i',
        normal,
        '-g',
        '/opt/contentmine/src/site/portality/ami-regexes/concatenated.xml'
    ]
    p = subprocess.Popen(co, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    out, err = p.communicate()
    if err:
        print 'ami-regex error ', err
        return {"errors": err}
    shutil.move('target/fulltext.xml/results.xml', outputdirectory + 'regex_results.xml')
    regex_results = outputdirectory + 'regex_results.xml'
    ns = etree.FunctionNamespace("http://www.xml-cml.org/ami")
    ns.prefix = "zf"
    tree = etree.parse(regex_results)
    hits = tree.xpath('//zf:hit')
    for hit in hits:
        doc = {}
        doc["pre"] = hit.get("pre")
        doc["fact"] = hit.get("word")
        doc["post"] = hit.get("post")
        facts.append(doc)

    # send facts to the index
    print "facts"
    if 'daily' not in tags: tags.append('daily')
    timestamp = datetime.now().strftime("%Y%m%d")
    if timestamp not in tags: tags.append(timestamp)
    for fact in facts:
        if getkeywords:
            fact['keywords'] = requests.get('http://cottagelabs.com/parser?blurb="' + fact['pre'] + ' ' + fact['fact'] + ' ' + fact['post'] + '"').json()
            time.sleep(0.05)
        # send the fact to the fact api
        fact['tags'] = tags
        fact['source'] = cid
        requests.post('http://localhost:9200/contentmine/fact', data=json.dumps(fact))



def getdailies():
    print "getting dailies"
    dy = datetime.now() - timedelta(days=1)
    fdy = dy.strftime("%Y-%m-%d %H%M")
    q = {
        "query": {
            "filtered": {
                "filter": {
                    "bool": {
                        "must": [
                            {
                                "term": {
                                    "tags.exact": "daily"
                                }
                            },
                            {
                                "range": {
                                    "created_date": {
                                        "gte":  fdy
                                    }
                                }
                            }
                        ]
                    }
                }
            }
        },
        "sort": [{"created_date": {"order":"desc"}}],
        "fields": [],
        "size": 1000000
    }    
    results = requests.post('http://localhost:9200/contentmine/catalogue/_search', data=json.dumps(q))

    for result in results.json().get('hits',{}).get('hits',[]):
        print "processing " + str(result['id'])
        daily(result['id'])

        
getdailies()