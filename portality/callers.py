import uuid, subprocess, os, shutil, json, requests, time

from datetime import datetime
import portality.models as models
from portality.core import app

from xml.etree import ElementTree as ET

from lxml import etree


class callers(object):

    
    
    def __init__(self,scraperdir=False,storagedir=False,speciesdir=False,speciesoutput=False):
        route = os.path.dirname(os.path.abspath(__file__)).replace('/portality','/')
        if scraperdir:
            self.scraperdir = scraperdir
        else:
            self.scraperdir = route.replace('/site','') + app.config['SCRAPER_DIRECTORY']
        if storagedir:
            self.storagedir = storagedir
        else:
            self.storagedir = route + app.config['STORAGE_DIRECTORY']
        if not os.path.exists(self.storagedir):
            os.makedirs(self.storagedir)
        if speciesdir:
            self.speciesdir = speciesdir
        else:
            self.speciesdir = route + app.config['SPECIES_DIRECTORY']
        if not os.path.exists(self.speciesdir):
            os.makedirs(self.speciesdir)
        if speciesoutput:
            self.speciesoutput = speciesoutput
        else:
            self.speciesoutput = route + app.config['SPECIES_OUTPUT']
        if not os.path.exists(self.speciesoutput):
            os.makedirs(self.speciesoutput)
        
    
    @property
    def scrapers(self):
        try:
            return [ f.replace('.json','') for f in os.listdir(self.scraperdir) if (os.path.isfile(os.path.join(self.scraperdir,f)) and not f.startswith('.')) ]
        except:
            return ["check the route to the scrapers folder!"]

        
        
    def quickscrape(self,scraper=False,urls=[],update=False):
        # TODO: there should be a check to see if this is already in the catalogue
        # and if the files are already extracted
        # and if they have already been processed
        # then some sort of concept of when they are worth refreshing - if ever? 
        # the publication should not change except as a re-print so would get picked up in a new cycle
    
        # TODO: add some sanitation of user input here
        if len(urls) == 0 or ';' in scraper:
            return {"error": "You need to provide some URLs"}
        
        output = []

        for url in urls:
            # have a look and see if this url already exists in the catalogue
            check = models.Catalogue.query(q='url.exact:"' + url + '"')
            if check.get('hits',{}).get('total',0) > 0 and not update:
                res = check['hits']['hits'][0]['_source']
            else:
                res = self._process(url,scraper)
                print res
                if 'errors' in res:
                    return res
                else:
                    # look for duplicates
                    f = None
                    if 'doi' in res:
                        check = models.Catalogue.query(q='doi.exact:"' + res['doi'] + '"')
                        if check.get('hits',{}).get('total',0) > 0:
                            f = models.Catalogue.pull(check['hits']['hits'][0]['_source']['id'])
                    if 'title' in res and f is None:
                        check = models.Catalogue.query(q='title.exact:"' + res['title'] + '"')
                        if check.get('hits',{}).get('total',0) > 0:
                            f = models.Catalogue.pull(check['hits']['hits'][0]['_source']['id'])
                    # send the metadata to the catalogue API
                    if f is not None: 
                        nres = res['id']
                        res['id'] = f.id
                        # TODO: move the extracted content files to proper storage
                        for fl in os.listdir(self.storagedir + '/' + nres):
                            try:
                                shutil.copy(os.path.join(self.storagedir + '/' + nres + '/', fl), self.storagedir + '/' + f.id)
                            except:
                                pass
                        shutil.rmtree(self.storagedir + '/' + nres)
                    else:
                        f = models.Catalogue()
                    for k,v in res.items():
                        if (update or k not in f.data) and k not in ['submit','created_date']:
                            f.data[k] = v
                    f.save()
                    print f.id
            output.append({"metadata":res,"id":res['id'],"catalogued":"https://contentmine.org/api/catalogue/" + res['id']})
        return output
            
            
            
    def _process(self,url,scraper):
        print url, scraper
        # make an ident for this proces and create a dir to put the output
        d = self.storagedir
        ident = uuid.uuid4().hex
        outputdirectory = d + ident
        if not os.path.exists(outputdirectory): os.makedirs(outputdirectory)
        
        # look for quickscrape
        qs = app.config.get('QUICKSCRAPE_COMMAND','/usr/bin/quickscrape')
        if not os.path.exists(qs): qs = '/usr/bin/quickscrape'
        if not os.path.exists(qs): qs = '/usr/local/bin/quickscrape'
        if not os.path.exists(qs): return {"errors":['cannot find quickscrape']}
            
        # run quickscrape with provided params
        co = [
            qs,
            '--output',
            outputdirectory,
            '--outformat',
            'bibjson'
        ]
        if scraper:
            co.append('--scraper')
            co.append(self.scraperdir + scraper.replace('.json','') + '.json')
        else:
            co.append('--scraperdir')
            co.append(self.scraperdir)
        co.append('--url')
        co.append(url)
        p = subprocess.Popen(co, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        out, err = p.communicate()
        
        if err:
            print 'quickscrape error ', err
            return {"errors": err}

        # find and read the metadata file
        try:
            slug = url.replace('://','_').replace('/','_').replace(':','')
            b = json.load(open(outputdirectory + '/' + slug + '/bib.json','r'))
            b["output"] = "http://contentmine.org/static/scraping/" + slug + '/' + ident
            b['slug'] = slug
            b["id"] = ident

            # TODO: move the extracted content files to proper storage
            for fl in os.listdir(outputdirectory + '/' + slug):
                shutil.copy(os.path.join(outputdirectory + '/' + slug, fl), outputdirectory)
            shutil.rmtree(outputdirectory + '/' + slug)

            # return the result
            return b

        except Exception, e:
            return {"errors": [str(e)]}
                        




    def ami(self, cmd='species', input_file_location=False, ident=False, filetype='xml'):
    
        if not input_file_location and not ident:
            return {"errors": "You need to provide an input file or a contentmine catalogue id"}
        
        # make an ident for this proces and create a dir
        d = self.speciesdir
        if not ident:
            ident = uuid.uuid4().hex
        outputdirectory = d + ident
        if not os.path.exists(outputdirectory): os.makedirs(outputdirectory)
        
        # make a result object to populate
        result = {
            "output": "http://contentmine.org/" + app.config['SPECIES_DIRECTORY'].replace('portality/','') + ident
        }
        
        # TODO: if input file is a web address, get it. If a file address, get it from local storage
        
        if input_file_location:
            infile = input_file_location
        else:
            try:
                # TODO: there should be a check for this folder existence
                infile = self.storagedir + ident + '/fulltext.' + filetype
            except:
                # TODO: if the folder does not exist check the catalogue, maybe return more useful info or re-run quickscrape
                return {"errors": "The provided contentmine catalogue ID no longer matches any stored files to process"}
        
        # run code with provided params
        co = [
            'ami-' + cmd,
            '-i',
            infile,
            '-e',
            filetype
        ]
        p = subprocess.Popen(co, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        out, err = p.communicate()

        if err:
            return {"errors": err}

        # find and read the output file
        outputfile = self.speciesoutput + 'fulltext.xml/results.xml'
        #result['raw'] = open(outputfile,'r').read()
        try:
            result['facts'] = self._ami_species_xml_to_json(outputfile)
            for fact in result['facts']:
                # send the fact to the fact api
                fact['source'] = ident
                f = models.Fact()
                f.data = fact
                f.save()
        except Exception, e:
            result["errors"] = [str(e)]
                
        # then tidy up by removing the ident directory
        #shutil.rmtree(outputdirectory)
        
        # return the result object
        return result
        



    def _ami_species_xml_to_json(self,infile):
        results = []
        tree = ET.parse(infile).getroot()
        elems = tree.find('results')[1:]
        for sub in elems:
            part = sub.find('eic')
            doc = {
                'retrieved_by': 'ami-species',
                'retrieved_date': datetime.now().strftime("%Y-%m-%d %H%M"),
                'eic': part.get('xpath')
            }
            doc["pre"] = part.find("pre").text
            doc["fact"] = part.find("value").text
            doc["post"] = part.find("post").text
            results.append(doc)

        return results
        

        
    def regex(self, urls=[], regexfile=[], tags=[], getkeywords=False):
        if not isinstance(urls,list): urls = urls.split(',')
        if not isinstance(tags,list): tags = tags.split(',')
        if not isinstance(regexfile,list): regexfile = regexfile.split(',')

        for url in urls:
            for regex in regexfile:
                url = url.strip().replace('\n','')
                if not regex.startswith('http'): regex = '/opt/contentmine/src/site/portality/ami-regexes/' + regex + '.xml'
                co = [
                    'ami-regex',
                    '-i',
                    url,
                    '-g',
                    regex
                ]
                p = subprocess.Popen(co, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                out, err = p.communicate()

                if err:
                    return {"errors": err}
                else:
                    # find and read the output file
                    outputfile = '/opt/contentmine/src/site/target/null.xml/results.xml'

                    ns = etree.FunctionNamespace("http://www.xml-cml.org/ami")
                    ns.prefix = "zf"
                    tree = etree.parse(outputfile)
                    hits = tree.xpath('//zf:hit')
                    for hit in hits:
                        doc = {
                            'tags': tags,
                        }
                        doc["pre"] = hit.get("pre")
                        doc["fact"] = hit.get("word")
                        doc["post"] = hit.get("post")
                        doc['source'] = url
                        if getkeywords:
                            doc['keywords'] = requests.get('http://cottagelabs.com/parser?blurb="' + doc['pre'] + ' ' + doc['fact'] + ' ' + doc['post'] + '"').json()
                            time.sleep(0.05)
                        f = models.Fact()
                        f.data = doc
                        f.save()

        return {"processing": "please check the facts API for results"}


    
    def norma(self, url, xsl='/opt/contentmine/src/norma/src/main/resources/org/xmlcml/norma/pubstyle/nlm/toHtml.xsl', output='/opt/contentmine/src/norma/target/normatest'):
        co = [
            'norma',
            '-i',
            url,
            '-x',
            xsl,
            '-o',
            output
        ]
        p = subprocess.Popen(co, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        out, err = p.communicate()

        if err:
            return {"errors": err}
        else:
            return {"output": output }


