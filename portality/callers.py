import uuid, subprocess, os, shutil, json, requests

import portality.models as models


class callers(object):

    def quickscrape(self,scraper=False,urls=[]):
        # TODO: there should be a check to see if this is already in the catalogue
        # and if the files are already extracted
        # and if they have already been processed
        # then some sort of concept of when they are worth refreshing - if ever? 
        # the publication should not change except as a re-print so would get picked up in a new cycle
    
        # TODO: add some sanitisation of user input here
        if len(urls) == 0 or ';' in scraper:
            return {"error": "You need to provide some URLs"}

        # this is just a demo, so just hardcoding some locations for now
        scraperdir = '/opt/contentmine/src/journal-scrapers/scrapers/'
        
        # make an ident for this proces and create a dir to put the output
        d = '/opt/contentmine/src/site/portality/static/scraping/'
        ident = uuid.uuid4().hex
        outputdirectory = d + ident
        if not os.path.exists(outputdirectory): os.makedirs(outputdirectory)
        
        # make a result object to populate
        result = {
            "metadata": "this will be the metadata object",
            "catalogued": "this will store the catalogue entry URL",
            "content": ["this will be a list of the extracted content object URLs"]
        }
        
        # run quickscrape with provided params
        co = [
            '/usr/bin/quickscrape',
            '--output',
            outputdirectory
        ]
        if scraper:
            co.append('--scraper')
            co.append(scraperdir + scraper.replace('.json','') + '.json')
        else:
            co.append('--scraperdir')
            co.append(scraperdir)
        if len(urls) == 1:
            co.append('--url')
            co.append(urls[0])
        else:
            fl = open(outputdirectory + '/urllist','w')
            for u in urls:
                fl.write(u + '\n')
            fl.close()
            co.append('--urllist')
            co.append(outputdirectory + '/urllist')
        p = subprocess.Popen(co, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        out, err = p.communicate()
        
        if err:
            return {"errors": err}

        # find and read the metadata file
        try:
            # TODO: note this should operate on all the listed URLs...
            slug = urls[0].replace('://','_').replace('/','_').replace(':','')
            result['slug'] = slug
            result["output"] = "http://contentmine.org/static/scraping/" + ident + '/' + slug
            m = json.load(open(outputdirectory + '/' + slug + '/results.json','r'))
            # TODO: process the metadata into bibjson (this should perhaps happen in the scraper proper)
            b = {}
            for obj in m:
                for k, v in obj.items():
                    if k in b:
                        if not isinstance(b[k],list):
                            b[k] = [b[k]]
                        b[k].append(v)
                    else:
                        b[k] = v
            b["id"] = ident
            b["NOTE"] = "this should be proper bibJSON, but it is not yet."
            # maybe not append all the metadata if it is being pushed to content
            result["metadata"] = b
            # send the metadata to the catalogue API
            api = "http://contentmine.org/api/catalogue/"
            result["catalogued"] = api + ident
            f = models.Catalogue()
            f.data = b
            f.id = ident
            f.save()
        except Exception, e:
            result["errors"] = [str(e)]
            del result["catalogued"]
        
        # TODO: move the extracted content files to proper storage
        
        # then tidy up by removing the ident directory
        #shutil.rmtree(outputdirectory)
        
        # return the result object
        return result
        




    def ami(self, cmd='species', input_file_location=False, ident=False, slug=False, filetype='xml'):
        # TODO: this should not need slug long term
    
        if not input_file_location and not ident:
            return {"errors": "You need to provide an input file or a contentmine catalogue id"}
        
        # make an ident for this proces and create a dir
        d = '/opt/contentmine/src/site/portality/static/species/'
        if not ident:
            ident = uuid.uuid4().hex
        outputdirectory = d + ident
        if not os.path.exists(outputdirectory): os.makedirs(outputdirectory)
        
        # make a result object to populate
        result = {
            "output": "http://contentmine.org/static/ami/" + ident
        }
        
        # TODO: if input file is a web address, get it. If a file address, get it from local storage
        
        if input_file_location:
            infile = input_file_location
        else:
            try:
                # TODO: there should be a check for this folder existence
                infile = '/opt/contentmine/src/site/portality/static/scraping/' + ident + '/' + slug + '/fulltext.' + filetype
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
        outputfile = '/opt/contentmine/src/xhtml2stm/target/xml.xml/results.xml'
        result['facts'] = []
        try:
            # read the result file and make fact objects and save them all
            m = open(outputfile,'r').read()
            o = _xml_to_dict(m)
            result['facts'] = o
            # TODO: properly handle the xml output and save some facts
            '''for a in []:
                b = {}
                
                result['facts'].append(b)
                # send the facts to the fact api
                api = "http://contentmine.org/api/fact/"
                result["catalogued"] = api + ident
                f = models.Fact()
                f.data = b
                f.id = ident
                f.save()'''
        except Exception, e:
            result["errors"] = [str(e)]
                
        # then tidy up by removing the ident directory
        #shutil.rmtree(outputdirectory)
        
        # return the result object
        return result
        

        
        
from collections import defaultdict

def _xml_to_dict(t):
    d = {t.tag: {} if t.attrib else None}
    children = list(t)
    if children:
        dd = defaultdict(list)
        for dc in map(_xml_to_dict, children):
            for k, v in dc.iteritems():
                dd[k].append(v)
        d = {t.tag: {k:v[0] if len(v) == 1 else v for k, v in dd.iteritems()}}
    if t.attrib:
        d[t.tag].update(('@' + k, v) for k, v in t.attrib.iteritems())
    if t.text:
        text = t.text.strip()
        if children or t.attrib:
            if text:
              d[t.tag]['#text'] = text
        else:
            d[t.tag] = text
    return d