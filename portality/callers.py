import uuid, subprocess, os, shutil, json, requests

import portality.models as models


class callers(object):

    def quickscrape(self,scraper=False,urls=[]):
        # TODO: add some sanitisation of user input here
        if len(urls) == 0 or ';' in scraper:
            return {"error": "You need to provide some URLs"}

        # this is just a demo, so just hardcoding some locations for now
        d = '/opt/contentmine/src/scraping/'
        dd = '/opt/contentmine/src/journal-scrapers/scrapers/'
        
        # make an ident for this proces and create a dir
        ident = uuid.uuid4().hex
        directory = d + ident
        if not os.path.exists(directory): os.makedirs(directory)
        
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
            directory
        ]
        if scraper:
            co.append('--scraper')
            co.append(dd + scraper.replace('.json','') + '.json')
        else:
            co.append('--scraperdir')
            co.append(dd)
        if len(urls) == 1:
            co.append('--url')
            co.append(urls[0])
        else:
            fl = open(directory + '/urllist','w')
            for u in urls:
                fl.write(u + '\n')
            fl.close()
            co.append('--urllist')
            co.append(directory + '/urllist')
        p = subprocess.Popen(co, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        out, err = p.communicate()
        
        if err:
            return {"errors": err}

        # find and read the metadata file
        try:
            # TODO: note this should operate on all the listed URLs...
            slug = urls[0].replace('://','_').replace('/','_')
            m = json.load(open(directory + '/' + slug + '/results.json','r'))
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
            f.save()
        except Exception, e:
            result["errors"] = [str(e)]
            del result["catalogued"]
        
        # then send the extracted content files to the content API
        result["content"] = "This part has not been implemented yet, but once complete then this will be a list of the file objects extracted by quickscrape and placed in the content API for use in further processing."
        
        # then tidy up by removing the ident directory
        shutil.rmtree(directory)
        
        # return the result object
        return result
        



    def species(self, input_file=False):
    
        if not input_file:
            return {"error": "You need to provide some input text or an input file"}

        # this is just a demo, so just hardcoding some locations for now
        d = '/opt/contentmine/src/xhtml2stmdev/'
        
        # make an ident for this proces and create a dir
        ident = uuid.uuid4().hex
        directory = d + ident
        if not os.path.exists(directory): os.makedirs(directory)
        
        # make a result object to populate
        result = {
        }
        
        # run quickscrape with provided params
        co = [
            'sh',
            d + 'appassembler/bin/species',
            '-i',
            input_file,
            '-o',
            directory
        ]
        p = subprocess.Popen(co, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        out, err = p.communicate()
        
        if err:
            return {"error": "Sorry, something went wrong during processing"}

        # find and read the metadata file
        result['facts'] = []
        if 1==1:
            # read the result file and make fact objects and save them all
            for a in []:
                b = {}
                result['facts'].append(b)
                # send the facts to the fact api
                api = "http://contentmine.org/api/fact/"
                result["catalogued"] = api + ident
                f = models.fact()
                f.data = b
                f.save()
        else:
            result["metadata"] = {"error": "Something went wrong getting metadata"}
            del result["catalogued"]
                
        # then tidy up by removing the ident directory
        shutil.rmtree(directory)
        
        # return the result object
        return result
        

        
        
