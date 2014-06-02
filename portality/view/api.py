'''
The contentmine API.
'''

import json, urllib2

from flask import Blueprint, request, abort, make_response, redirect
from flask.ext.login import current_user

from portality.view.query import query as query
import portality.models as models
from portality.core import app
import portality.util as util

from datetime import datetime


blueprint = Blueprint('api', __name__)


# TODO: add auth control


# return the API instructions --------------------------------------------------
@blueprint.route('/<path:path>', methods=['GET','POST'])
@blueprint.route('/', methods=['GET','POST'])
@util.jsonp
def api():
    resp = make_response( json.dumps({
        "README": {
            "description": "Welcome to the ContentMine API. The endpoints listed here are available for their described functions. Append the name of each endpoint to the /api/ URL to gain access to each one.",
            "version": "0.1"
        },
        "crawler": {
            "description": "Lists all available crawlers, with further instructions for how to use them. Crawlers are used to crawl across some location or dataset, say a website of a given publisher or a listing of articles provided by an organisation. Each crawler has a specific target and operating process for that target. The purpose of a crawler is to extract metadata from these sources, and that metadata can then be uploaded to the catalogue API.",
            "note": "It is not mandatory nor even expected that all crawlers will run directly at ContentMine. However this API will list the crawlers we know about and will make them available for execution on sources that can be accessed publicly. Individual users are instead encouraged to download and run crawlers (or to create their own) themselves across their own permitted access connections to the various useful resources they wish to scrape, then they can crawl those contents for facts that can then be uploaded directly to the fact API."
        },
        "scraper": {
            "description": "Lists all available scrapers, with further instructions for how to use them. Scrapers act on the metadata output of crawlers, and are used to extract content from the sources described by said metadata. For example a particular scraper may know how to extract the full-text article content from a given website or perhaps to retrieve a particular file format. The content retrieved by a scraper can be uploaded to the content API - BUT ONLY IF it is permissible to do so; otherwise it should only be stored and processed locally.",
            "note": "It is not mandatory nor even expected that all scrapers will run directly at ContentMine. However this API will list the scrapers we know about and will make them available for execution on crawled sources that are publicly accessible. Individual users are encouraged to download and run scrapers (or to create their own) themselves across the contents that they have access to and that they wish to mine, then they can upload extracted facts directly to the fact API."

        },
        "visitor": {
            "description": "Lists all available visitors, with further instructions for how to use them. Visitors are used to extract certain types of fact from contents. For example once a crawler has identified the metadata of an article from a web page, and a scraper has retrieved the full-text content object, various visitors may be appropriate to run on the content to extract facts. Extracted facts can then be uploaded to the fact API.",
            "note": "It is not mandatory nor even expected that all visitors will run directly at ContentMine. However this API will list the visitors we know about and will make them available for execution on contents that are publicly accessible. Individual users are encouraged to download and run visitors (or to create their own) themselves across the contents that they have scraped and that they wish to mine, then they can upload extracted facts directly to the fact API."

        },
        "catalogue": {
            "description": "Provides access to all the metadata of all the items crawled or scraped by ContentMine. New catalogue records can be uploaded too, either as the output of ContentMine scraping or of any other process deemed appropriate. The catalogue provides powerful search features too.",
            "note": "Any useful article metadata is welcome to the catalogue API, whether it was retrieved as a result of ContentMine crawling either by ContentMine or by users locally. We will endeavour to store and make available all such metadata for use as a growing and eventually comprehensive catalogue of academic materials."
        },
        "content": {
            "description": "Lists all the content items currently stored for processing by ContentMine. Content objects such as article PDFs can also be uploaded to the content API, BUT ONLY IF it is permissible to do so, and only if absolutely necessary.",
            "note": "The aim of ContentMine is to extract facts rather than to archive content, so this feature is only available to assist in that service and is not guaranteed to be a reliable long term storage service. The content API is therefore just a useful place to temporarily make some content available after crawling and scraping for visitors to run on."
        },
        "fact": {
            "description": "THE MAIN EVENT! Here is access to the facts extracted and stored by ContentMine. Also, new facts can be uploaded for storage. Any process that extracts a fact can send such fact (or batch of facts) to this API and it will then become available via the ContentMine stream. The fact API also provides powerful search features too. Long term storage of facts may not be provided - it is hoped to be, but to be decided later in the project.",
            "note": "There will also be access to daily lists of extracted facts, and perhaps larger dumps such as weeklies."
        },
        "activity": {
            "description": "Intended to be a useful API for checking what processes are going on in the ContentMine. Probably not useful in general, but will be useful for development debugging and perhaps for technically proficient API users to check on progress of processes."
        }
    }) )
    resp.mimetype = "application/json"
    return resp




# provide access to the listing of available crawlers --------------------------
@blueprint.route('/crawler/<path:path>', methods=['GET','POST'])
@blueprint.route('/crawler', methods=['GET','POST'])
@util.jsonp
def crawler():
    # TODO: each crawler should be made available in the crawler folder
    # each one should be able to report what it does
    # see the bibserver codebase for something similar
    # each crawler should then be accessible via /api/crawler/NAME
    # and should have specified inputs and outputs
    # should also make an effort to conventionalise the IOs required
    resp = make_response( json.dumps({
        "description": "Will eventually list all the crawlers and explain what they do and how to call them."
    }) )
    resp.mimetype = "application/json"
    return resp




# provide access to the list of available scrapers -----------------------------
@blueprint.route('/scraper/<path:path>', methods=['GET','POST'])
@blueprint.route('/scraper', methods=['GET','POST'])
@util.jsonp
def scraper():
    # TODO: each scraper should be made available in the scraper folder
    # each one should be able to report what it does
    # see the bibserver codebase for something similar
    # each scraper should then be accessible via /api/scraper/NAME
    # and should have specified inputs and outputs
    # should also make an effort to conventionalise the IOs required
    resp = make_response( json.dumps({
        "description": "Will eventually list all the scrapers and explain what they do and how to call them."
    }) )
    resp.mimetype = "application/json"
    return resp
    
    
    
    
# provide access to the list of available visitors -----------------------------
@blueprint.route('/visitor/<path:path>', methods=['GET','POST'])
@blueprint.route('/visitor', methods=['GET','POST'])
@util.jsonp
def visitor():
    # TODO: each visitor should be made available in the visitor folder
    # each one should be able to report what it does
    # see the bibserver codebase for something similar
    # each visitor should then be accessible via /api/visitor/NAME
    # and should have specified inputs and outputs
    # should also make an effort to conventionalise the IOs required
    resp = make_response( json.dumps({
        "description": "Will eventually list all the visitors and explain what they do and how to call them."
    }) )
    resp.mimetype = "application/json"
    return resp




# provide access to catalogue of article metadata ------------------------------
@blueprint.route('/catalogue', methods=['GET','POST'])
@util.jsonp
def catalogue():
    if request.method == 'GET':
        resp = make_response( json.dumps({
            "README": {
                "description": "The ContentMine catalogue API. The endpoints listed here are available for their described functions. Append the name of each endpoint to the /api/catalogue/ URL to gain access to each one.",
                "GET": "Returns this documentation page",
                "POST": "POST a JSON payload following the bibJSON metadata convention (www.bibjson.org), and it will be saved in the ContentMine. This action redirects to the saved object, so the location/URL/ID of the object can be known."
            },
            "<identifier>": {
                "GET": "GET /api/catalogue/SOME_IDENTIFIER will return the identified catalogue entry in (bib)JSON format",
                "PUT": "PUT to an existing identified catalogue entry at /api/catalogue/SOME_IDENTIFIER will completely overwrite with the provided properly content-typed JSON payload",
                "POST": "POST to an existing identified catalogue entry at /api/catalogue/SOME_IDENTIFIER will update the entry with the provided key-value pairs. POST should provide a properly content-typed JSON payload."
            },
            "query": {
                "description": "A query endpoint which gives full access to the power of elasticsearch querying on all of the article metadata stored in the ContentMine catalogue.",
                "note": "Some examples of how to write queries will be provided, but for now just see the elasticsearch documentation at www.elasticsearch.org"
            }
        }) )
        resp.mimetype = "application/json"
        return resp
        
    elif request.method == 'POST':
        f = models.Catalogue()
        if request.json:
            for k in request.json.keys():
                f.data[k] = request.json[k]
        else:
            for k, v in request.values.items():
                f.data[k] = v
        f.save()
        return redirect('/api/catalogue/' + f.id)

@blueprint.route('/catalogue/<ident>', methods=['GET','PUT','POST'])
@util.jsonp
def cataloguedirect(ident):
    # TODO: consider allowing PUT/POST of new objects to provided IDs in 
    # addition to users being able to send them to /catalogue and having an ID
    # created for them. Do we want people to be able to specify their own IDs?
    try:
        f = models.Catalogue.pull(ident)
    except:
        abort(404)
    if request.method == 'GET':
        resp = make_response( f.json )
        resp.mimetype = "application/json"
        return resp
    elif request.method in ['PUT','POST']:
        inp = {}
        if request.json:
            inp = request.json
        else:
            for k, v in request.values.items():
                inp[k] = v
        # TODO: strip any control keys that get passed in, 
        # if they should generally be ignored
        if request.method == 'PUT':
            f.data = inp
        else:
            for k in inp.keys():
                f.data[k] = inp[k]
        f.save()
        return redirect('/api/catalogue/' + ident)    

@blueprint.route('/catalogue/query', methods=['GET','POST'])
@util.jsonp
def cataloguequery():
    if request.method == "POST":
        if request.json:
            qs = request.json
        else:
            qs = dict(request.form).keys()[-1]
    elif 'q' in request.values:
        qs = {'query': {'query_string': { 'query': request.values['q'] }}}
    elif 'source' in request.values:
        qs = json.loads(urllib2.unquote(request.values['source']))
    else: 
        qs = {'query': {'match_all': {}}}
    return query(path='Catalogue',qry=qs)




# provide access to retrieved content objects that can and have been stored ----
@blueprint.route('/content/<path:path>', methods=['GET','POST'])
@blueprint.route('/content', methods=['GET','POST'])
@util.jsonp
def content():
    if request.method == 'GET':
        # TODO: this should become a listing of stored content
        # perhaps with a paging / search facility
        resp = make_response( json.dumps({
            "description": "Will eventually list all the content stored in ContentMine for processing."
        }) )
        resp.mimetype = "application/json"
        return resp
        
    elif request.method == 'POST':
        # TODO: this should save POSTed content to wherever we are saving stuff
        # probably the saving of stuff should be handled by an archive class
        pass    
    
    
    
    
# provide access to facts ------------------------------------------------------
@blueprint.route('/fact', methods=['GET','POST'])
@util.jsonp
def fact():
    if request.method == 'GET':
        resp = make_response( json.dumps({
            "README": {
                "description": "The ContentMine fact API. The endpoints listed here are available for their described functions. Append the name of each endpoint to the /api/fact/ URL to gain access to each one.",
                "GET": "Returns this documentation page",
                "POST": "POST a JSON payload following the fact metadata convention (err, which does not exist yet), and it will be saved in the ContentMine"
            },
            "<identifier>": {
                "GET": "GET /api/fact/SOME_IDENTIFIER will return the identified fact in JSON format",
                "PUT": "PUT to an existing identified fact at /api/fact/SOME_IDENTIFIER will completely overwrite the fact with the provided properly content-typed JSON payload",
                "POST": "POST to an existing fact at /api/fact/SOME_IDENTIFIER will update the fact with the provided key-value pairs. POST should provide a properly content-typed JSON payload."
            },
            "query": {
                "description": "A query endpoint which gives full access to the power of elasticsearch querying on all of the facts stored in ContentMine.",
                "note": "Some examples of how to write queries will be provided, but for now just see the elasticsearch documentation at www.elasticsearch.org"
            },
            "daily": {
                "description": "Provides a listing of all facts discovered so far for the current day."
            }
        }) )
        resp.mimetype = "application/json"
        return resp
                
    elif request.method == 'POST':
        f = models.Fact()
        if request.json:
            for k in request.json.keys():
                f.data[k] = request.json[k]
        else:
            for k, v in request.values.items():
                f.data[k] = v        
        f.save()
        return redirect('/api/fact/' + f.id)

@blueprint.route('/fact/<ident>', methods=['GET','POST'])
@util.jsonp
def factdirect(ident):
    # TODO: consider allowing PUT/POST of new objects to provided IDs in 
    # addition to users being able to send them to /catalogue and having an ID
    # created for them. Do we want people to be able to specify their own IDs?
    try:
        f = models.Fact.pull(ident)
    except:
        abort(404)
    if request.method == 'GET':
        resp = make_response( f.json )
        resp.mimetype = "application/json"
        return resp
    elif request.method in ['PUT','POST']:
        inp = {}
        if request.json:
            inp = request.json
        else:
            for k, v in request.values.items():
                inp[k] = v
        # TODO: strip any control keys that get passed in, 
        # if they should generally be ignored
        if request.method == 'PUT':
            f.data = inp
        else:
            for k in inp.keys():
                f.data[k] = inp[k]
        f.save()
        return redirect('/api/fact/' + ident)    

@blueprint.route('/fact/query', methods=['GET','POST'])
@util.jsonp
def factquery():
    if request.method == "POST":
        if request.json:
            qs = request.json
        else:
            qs = dict(request.form).keys()[-1]
    elif 'q' in request.values:
        qs = {'query': {'query_string': { 'query': request.values['q'] }}}
    elif 'source' in request.values:
        qs = json.loads(urllib2.unquote(request.values['source']))
    else: 
        qs = {'query': {'match_all': {}}}
    return query(path='Fact',qry=qs)

@blueprint.route('/fact/daily', methods=['GET','POST'])
@util.jsonp
def factdaily():
    # TODO: should this accept user-provided queries too? So people can search 
    # on the daily list? If so, just check the incoming query and build one 
    # with a MUST that includes the following date-based restriction.
    qry = {
        'query': {
            'query_string': {
                'query': datetime.now().strftime("%Y-%m-%d"),
                'default_field':'created_date'
            }
        },
        'sort': [{"created_date.exact":{"order":"desc"}}]
    }
    r = query(path='Fact',qry=qry,raw=True)
    # TODO: decide if any control keys should be removed before displaying facts
    res = [i['_source'] for i in r.get('hits',{}).get('hits',[])]
    resp = make_response( json.dumps(res) )
    resp.mimetype = "application/json"
    return resp
    


    
# list running activities ------------------------------------------------------
@blueprint.route('/activity/<path:path>', methods=['GET','POST'])
@blueprint.route('/activity', methods=['GET','POST'])
@util.jsonp
def activity():
    # TODO: useful stuff here
    resp = make_response( json.dumps({
    }) )
    resp.mimetype = "application/json"
    return resp
    
    

