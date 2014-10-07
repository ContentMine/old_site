'''
The contentmine API.
'''

import json, urllib2

from flask import Blueprint, request, abort, make_response, redirect
from flask.ext.login import current_user

from functools import wraps
from flask import g, request, redirect, url_for

from portality.view.query import query as query
import portality.models as models
from portality.core import app
import portality.util as util
from portality.callers import callers as callers

from datetime import datetime

from os import listdir
from os.path import isfile, join



blueprint = Blueprint('api', __name__)


# add auth control
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if g.user is None:
            return redirect(url_for('login', next=request.url))
        return f(*args, **kwargs)
    return decorated_function
    
    
    
# return the API instructions --------------------------------------------------
@blueprint.route('/<path:path>', methods=['GET','POST'])
@blueprint.route('/', methods=['GET','POST'])
@util.jsonp
def api():
    resp = make_response( json.dumps({
        "README": {
            "description": "Welcome to the ContentMine API. The endpoints listed here are available for their described functions. Append the name of each endpoint to the /api/ URL to gain access to each one.",
            "version": "0.1",
            "documentation": "http://contentmine.org/docs"
        },
        "processor": {
            "description": "Lists all available processors (crawlers, scrapers, visitors, or combinations of those) with further instructions for how to use them. Visitors are used to extract certain types of fact from contents. For example once a crawler has identified the metadata of an article from a web page, and a scraper has retrieved the full-text content object, various visitors may be appropriate to run on the content to extract facts. Extracted facts can then be uploaded to the fact API.",
            "note": "It is not mandatory nor even expected that all visitors will run directly at ContentMine. However this API will list the visitors we know about and will make them available for execution on contents that are publicly accessible. Individual users are encouraged to download and run visitors (or to create their own) themselves across the contents that they have scraped and that they wish to mine, then they can upload extracted facts directly to the fact API."

        },
        "catalogue": {
            "description": "Provides access to all the metadata of all the items crawled or scraped by ContentMine. New catalogue records can be uploaded too, either as the output of ContentMine scraping or of any other process deemed appropriate. The catalogue provides powerful search features too.",
            "note": "Any useful article metadata is welcome to the catalogue API, whether it was retrieved as a result of ContentMine crawling either by ContentMine or by users locally. We will endeavour to store and make available all such metadata for use as a growing and eventually comprehensive catalogue of academic materials."
        },
        "fact": {
            "description": "THE MAIN EVENT! Here is access to the facts extracted and stored by ContentMine. Also, new facts can be uploaded for storage. Any process that extracts a fact can send such fact (or batch of facts) to this API and it will then become available via the ContentMine stream. The fact API also provides powerful search features too. Long term storage of facts may not be provided - it is hoped to be, but to be decided later in the project.",
            "note": "There will also be access to daily lists of extracted facts, and perhaps larger dumps such as weeklies."
        },
        "queue": {
            "description": "The queue provides various ways to get hold of article metadata and assign them to user accounts for processing. This enables users - human or machine - to claim articles for certain tasks, to help avoid duplication of effort"
        }
    }) )
    resp.mimetype = "application/json"
    return resp




# provide access to the listing of available processors --------------------------
@blueprint.route('/processor/<path:path>', methods=['GET','POST'])
@blueprint.route('/processor', methods=['GET','POST'])
@blueprint.route('/processor/', methods=['GET','POST'])
@util.jsonp
def crawler():
    # TODO: each processor should be made available in the crawler folder
    # each one should be able to report what it does
    # each crawler should then be accessible via /api/processor/NAME
    # and should have specified inputs and outputs
    # should also make an effort to conventionalise the IOs required
    # For now quickscrape has been manually added so that it can be used as demo
    resp = make_response( json.dumps({
        "description": "Lists all the processors that are available so they can be accessed. \
        Processors tend to do one or more of crawling (finding articles), scraping (retrieving the \
        documents that contain the content of articels), structuring (normalising the strucutre of the \
        content of an article), or visiting (searching the article content for facts and extracting them). \
        Append the processor name to the processor/ url to access each one and read more about what they do.",
        "processors": ["quickscrape"]
    }) )
    resp.mimetype = "application/json"
    return resp

@blueprint.route('/processor/quickscrape', methods=['GET','POST'])
@util.jsonp
def quickscrape():
    if request.method == 'GET' and 'url' not in request.values:
        # show the instructions
        scraperdir = '/opt/contentmine/src/journal-scrapers/scrapers/'
        try:
            scrp = [ f.replace('.json','') for f in listdir(scraperdir) if isfile(join(scraperdir,f)) ]
        except:
            try:
                scraperdir = '/Users/one/Code/contentmine/src/journal-scrapers/scrapers/'
                scrp = [ f.replace('.json','') for f in listdir(scraperdir) if isfile(join(scraperdir,f)) ]
            except:
                scrp = ["check the route to the scrapers folder!"]
        resp = make_response( json.dumps({
            "description": "The quickscrape processor.",
            "type": ["crawler","scraper"],
            "GET": "GETs this instruction page",
            "POST": "POST your instructions to the crawler and receive answers. Can scrape by trying to choose automatically from the listed scrapers, or specify one in the provided options. See the example_POST and use the url parameter as either a single URL string or a list of URLs. Make sure your POST specifices the Content-Type:application/json",
            "example_POST": {
                "url": ["https://peerj.com/articles/384"],
                "scraper": "peerj"
            },
            "available_scrapers": scrp
        }) )
        resp.mimetype = "application/json"
        return resp
        
    else:
        params = request.json if request.json else request.values
        if params.get('url',False):
            if isinstance(params['url'],list):
                urls = params['url']
            else:
                urls = [params['url']]
            try:
                output = callers().quickscrape(scraper=params.get('scraper',False),urls=urls)
            except Exception, e:
                resp = make_response(json.dumps({'errors': [str(e)]}))
                resp.mimetype = "application/json"
                return resp, 400

        else:
            output = {"error": "Sorry, your request was missing a url! So there is nothing to do"}

        resp = make_response( json.dumps(output) )
        resp.mimetype = "application/json"
        return resp
    
    
    

# call the species visitor
@blueprint.route('/processor/species', methods=['GET','POST'])
@util.jsonp
def species():
    if request.method == 'GET' and 'ident' not in request.values:
        # show the instructions
        resp = make_response( json.dumps({
            "description": "The species processor",
            "type": ["visitor"],
            "GET": "GETs this instruction page",
            "POST": "POST your instructions to the visitor and receive answers.",
            "example_POST": {
                "url": ["https://peerj.com/articles/384"]
            },
        }) )
        resp.mimetype = "application/json"
        return resp
        
    else:
        params = request.json if request.json else request.values
        try:
            output = callers.ami(cmd='species', **params)
        except:
            output = {"errors": "Sorry, your request was missing one of the main params (url, scraper), or something else went wrong calling AMI."}

        resp = make_response( json.dumps(output) )
        resp.mimetype = "application/json"
        return resp



# provide access to catalogue of article metadata ------------------------------
@blueprint.route('/catalogue', methods=['GET','POST'])
@blueprint.route('/catalogue/', methods=['GET','POST'])
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
        if current_user.is_anonymous():
            abort(401)
        else:
            f = models.Catalogue()
            if request.json:
                for k in request.json.keys():
                    if k not in ['submit']:
                        f.data[k] = request.json[k]
            else:
                for k, v in request.values.items():
                    if k not in ['submit']:
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
        if current_user.is_anonymous():
            abort(401)
        else:
            inp = {}
            if request.json:
                for k in request.json.keys():
                    if k not in ['submit']:
                        inp[k] = request.json[k]
            else:
                for k, v in request.values.items():
                    if k not in ['submit']:
                        inp[k] = v
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
@blueprint.route('/storage/<path:path>', methods=['GET','POST'])
@blueprint.route('/storage', methods=['GET','POST'])
@util.jsonp
@login_required
def content():
    if request.method == 'GET':
        # TODO: this should become a listing of stored content
        # perhaps with a paging / search facility
        resp = make_response( json.dumps({
            "description": "Temporary storage for items during processing."
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
        if current_user.is_anonymous():
            abort(401)
        else:
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
        if current_user.is_anonymous():
            abort(401)
        else:
            inp = {}
            if request.json:
                for k in request.json.keys():
                    if k not in ['submit']:
                        inp[k] = request.json[k]
            else:
                for k, v in request.values.items():
                    if k not in ['submit']:
                        inp[k] = v
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
    

# queue up article metadata records that need processing -----------------------
@blueprint.route('/queue', methods=['GET','POST'])
@util.jsonp
def queue():
    qry = {
        'query': {
            'bool': {
                'must_not': [
                    {
                        'exists': {
                            'field': 'processing'
                        }
                    }
                ]
            }
        },
        'sort': [{"created_date.exact":{"order":"desc"}}]
    }
    # TODO: enable query paging parameters through the queue
    r = query(path='Fact',qry=qry,raw=True)
    res = [i['_source'] for i in r.get('hits',{}).get('hits',[])]
    resp = make_response( json.dumps(res) )
    resp.mimetype = "application/json"
    return resp

@blueprint.route('/queue/assign', methods=['GET','POST'])
@util.jsonp
@login_required
def assign():
    try:
        ids = request.json
    except:
        try:
            ids = request.values['ids'].split(',')
        except:
            qry = {
                'query': {
                    'bool': {
                        'must_not': [
                            {
                                'exists': {
                                    'field': 'processing'
                                }
                            }
                        ]
                    }
                },
                'sort': [{"processing.created_date.exact":{"order":"desc"}}],
                'size': 1
            }
            # TODO: allow for accepting query params here
            r = query(path='Record',qry=qry,raw=True)
            ids = [i['_source']['id'] for i in r.get('hits',{}).get('hits',[])]

    if request.method == 'POST':
        assigned = []
        for rid in ids:
            rec = models.Catalogue().pull(rid)
            if rec is None:
                abort(404)
            elif not rec.data.get('processing',False):
                rec.data['processing'] = {'assigned_date':datetime.datetime.now(), 'assigned_to':current_user.id}
                rec.save()
                assigned.append(rec.id)
    else:
        assigned = ids
        
    resp = make_response( json.dumps(assigned) )
    resp.mimetype = "application/json"
    return resp

@blueprint.route('/queue/assigned', methods=['GET'])
@blueprint.route('/queue/assigned/<userid>', methods=['GET'])
@util.jsonp
def assigned(userid=False):
    qry = {
        'query': {
            'bool': {
                'must': [
                    {
                        'exists': {
                            'field': 'processing'
                        }
                    }
                ]
            }
        },
        'sort': [{"processing.assigned_date.exact":{"order":"desc"}}]
    }
    if userid:
        qry['query']['bool']['must'].append({
            'term': {
                'processing.assigned_to.exact': current_user.id
            }
        })

    r = query(path='Record',qry=qry,raw=True)
    res = [i['_source']['id'] for i in r.get('hits',{}).get('hits',[])]

    resp = make_response( json.dumps(res) )
    resp.mimetype = "application/json"
    return resp

@blueprint.route('/queue/next', methods=['GET','POST'])
@util.jsonp
def next():
    qry = {
        'query': {
            'bool': {
                'must_not': [
                    {
                        'exists': {
                            'field': 'processing'
                        }
                    }
                ]
            }
        },
        'sort': [{"processing.created_date.exact":{"order":"desc"}}],
        'size': 1
    }
    r = query(path='Record',qry=qry,raw=True)
    
    try:
        next = r['hits']['hits'][0]['_source']['id']
    except:
        abort(404)

    if request.method == 'POST':
        if current_user.is_anonymous():
            abort(401)
        else:
            rec = models.article.pull(next)
            rec.data['processing'] = {'assigned_date':datetime.datetime.now(), 'assigned_to':current_user.id}
            rec.save()

    resp = make_response( next )
    resp.mimetype = "application/json"
    return resp

    
    

