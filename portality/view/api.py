'''
The contentmine API.
'''

import json, urllib2

from flask import Blueprint, request, abort, make_response, redirect
from flask.ext.login import current_user

from functools import wraps
from flask import g, request, redirect, url_for

import portality.models as models
import portality.util as util
from portality.callers import callers as callers

from datetime import datetime


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
        "process": {
            "description": "The process queue lists catalogue entries by their processing status, so that they can be quickly queried to provide lists of articles to perform various processing tasks upon"
        },
        "catalogue": {
            "description": "Provides access to all the metadata of all the items crawled or scraped by ContentMine. New catalogue records can be uploaded too, either as the output of ContentMine scraping or of any other process deemed appropriate. The catalogue provides powerful search features too.",
            "note": "Any useful article metadata is welcome to the catalogue API, whether it was retrieved as a result of ContentMine crawling either by ContentMine or by users locally. We will endeavour to store and make available all such metadata for use as a growing and eventually comprehensive catalogue of academic materials."
        },
        "fact": {
            "description": "THE MAIN EVENT! Here is access to the facts extracted and stored by ContentMine. Also, new facts can be uploaded for storage. Any process that extracts a fact can send such fact (or batch of facts) to this API and it will then become available via the ContentMine stream. The fact API also provides powerful search features too. Long term storage of facts may not be provided - it is hoped to be, but to be decided later in the project.",
            "note": "There will also be access to daily lists of extracted facts, and perhaps larger dumps such as weeklies."
        }
    }) )
    resp.mimetype = "application/json"
    return resp




# provide access to the listing of available processors --------------------------
@blueprint.route('/processor')
@util.jsonp
def processor():
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
        "processors": ["quickscrape","species"],
        "crawlers": "Crawlers find and list web pages. They must produce at least a link to a resource. They may also produce metadata about that resources. A crawler should create a Catalogue record as output. Crawlers and scrapers are similar and a processor may well be a crawler and a scraper",
        "scrapers": "Scrapers should produce metadata about a given resource, and should also provide a link to the full text of a resource in the various formats available (if any). A scraper should create a Catalogue record as output, along with links to files (or files themselves) containing the full resource",
        "visitors": "Visitors extract facts from resources. They should operate on the full text of an item that has a ContentMine catalogue entry. A visitor could operate remotely on an full text item not stored or availabl to ContentMine, but in this case the first thing it must do before providing creating Fact records in ContentMine is to check if a Catalogue record exists for the resource, and if not then create one. Facts must have a Catalogue record parent."
    }) )
    resp.mimetype = "application/json"
    return resp

@blueprint.route('/processor/quickscrape', methods=['GET','POST'])
@util.jsonp
def quickscrape():
    if request.method == 'GET' and 'url' not in request.values:
        # show the instructions
        resp = make_response( json.dumps({
            "description": "The quickscrape processor.",
            "type": ["crawler","scraper"],
            "GET": "GETs this instruction page (or, given a url query parameter, emulates the POST)",
            "POST": "POST your instructions to the crawler and receive answers. Can scrape by trying to choose automatically from the listed scrapers, or specify one in the provided options. See the example_POST and use the url parameter as either a single URL string or a list of URLs. Make sure your POST specifices the Content-Type:application/json",
            "example_POST": {
                "url": ["https://peerj.com/articles/384"],
                "scraper": "peerj"
            },
            "available_scrapers": callers().scrapers
        }) )
        resp.mimetype = "application/json"
        return resp
        
    else:
        params = request.json if request.json else request.values
        if params.get('url',False):
            if isinstance(params['url'],list):
                urls = params['url']
            elif ',' in params['url']:
                urls = params['url'].split(',')
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
            "description": "The species processor. Searches a resource for species names",
            "type": ["visitor"],
            "GET": "GETs this instruction page (or, provided at least a catalogue parameter, emulates the POST)",
            "POST": "POST your instructions to the visitor and receive answers.",
            "example_POST": {
                "catalogue": "<CATALOGUE_IDENTIFIER>"  #https://peerj.com/articles/384
            }
        }) )
        resp.mimetype = "application/json"
        return resp
        
    else:
        params = request.json if request.json else request.values
        try:
            output = callers().ami(
                cmd='species', 
                ident=params['ident']
                #filetype=params.get('filetype','xml')
            )
        except Exception, e:
            resp = make_response(json.dumps({'errors': [str(e)]}))
            resp.mimetype = "application/json"
            return resp, 400

        resp = make_response( json.dumps(output) )
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
                "POST": "POST a JSON payload following the bibJSON metadata convention (www.okfnlabs.org/bibjson), and it will be saved in the ContentMine. This saved object will be returned and from this the ID can be extracted, thus providing the object address at /api/catalogue/ID"
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
            resp = make_response( f.json )
            resp.mimetype = "application/json"
            return resp

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
    resp = make_response( json.dumps(models.Catalogue.query(q=qs)) )
    resp.mimetype = "application/json"
    return resp
    
    
# provide access to facts ------------------------------------------------------
@blueprint.route('/fact', methods=['GET','POST'])
@util.jsonp
def fact():
    if request.method == 'GET':
        resp = make_response( json.dumps({
            "README": {
                "description": "The ContentMine fact API. The endpoints listed here are available for their described functions. Append the name of each endpoint to the /api/fact/ URL to gain access to each one.",
                "GET": "Returns this documentation page",
                "POST": "POST a JSON payload following the fact metadata convention (err, which does not exist yet), and it will be saved in the ContentMine. NOTE: a fact MUST include the parent parameter, and that must be the ID of a ContentMine Catalogue record"
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
    resp = make_response( json.dumps(models.Fact.query(q=qs)) )
    resp.mimetype = "application/json"
    return resp

@blueprint.route('/fact/daily', methods=['GET','POST'])
@util.jsonp
def factdaily():
    qry = {
        'query': {
            'range': {
                'created_date': {
                    'gte': datetime.now().strftime("%Y-%m-%d")
                }
            }
        },
        'sort': [{"created_date.exact":{"order":"desc"}}]
    }
    r = models.Fact.query(q=qry)
    # TODO: decide if any control keys should be removed before displaying facts
    res = [i['_source'] for i in r.get('hits',{}).get('hits',[])]
    resp = make_response( json.dumps(res) )
    resp.mimetype = "application/json"
    return resp
    

# queue up article metadata records that need processing -----------------------
@blueprint.route('/process')
@util.jsonp
def process():
    resp = make_response( json.dumps({
        "README": {
            "description": "The ContentMine process queue API. Returns a list of Catalogue metadata record IDs that have yet to be processed by a given (or all) processor. By default this shows records ever processed, but can be filtered by passing the since parameter with a datetime value",
            "GET": "Returns this documentation page",
            "Assignment": "If you want to track which records are being processed, it is possible to assign and unasssign records to user accounts. To filter by unassigned records just add unassigned=true to the URL parameters"
        },
        "assign": {
            "GET": "emulates the POST, accepts ids parameter with a CSV list of Catalogue identifiers",
            "POST": "provided a list of Catalogue record identifiers in the ids parameter, marks them as assigned to the current user. Use the Catalogue query if you wish to find identifiers for specific records. Returns a list of the identifiers of records that actually were assigned (in case some were assigned in the interim)"
        },
        "assigned": {
            "GET": "returns the list of IDs assigned to the current user"
        },
        "unassign": {
            "GET": "unassigns all records assigned to the current user"
        },
        "next": {
            "GET": "returns the next record available for assignment - i.e. the Catalogue record most recently created but not assigned to anyone",
            "POST": "assigns the next record available to the current user"
        }
    }) )
    resp.mimetype = "application/json"
    return resp

@blueprint.route('/process/assign')
@util.jsonp
def assign():
    vals = request.json if request.json else request.values
    if 'ids' in vals:
        if ',' in vals['ids']:
            vl = vals['ids'].split(',')
        elif '[' not in vals['ids']:
            vl = [vals['ids']]
        else:
            vl = vals['ids']
        resp = make_response( json.dumps( current_user.assign(ids=vl) ) )
        resp.mimetype = "application/json"
        return resp
    else:
        abort(404)
        

@blueprint.route('/process/assigned')
@util.jsonp
def assigned():
    resp = make_response( json.dumps( current_user.assigned ) )
    resp.mimetype = "application/json"
    return resp

@blueprint.route('/process/unassign')
@util.jsonp
def unassign():
    current_user.unassign()
    resp = make_response( json.dumps( [] ) )
    resp.mimetype = "application/json"
    return resp

@blueprint.route('/process/next')
@util.jsonp
def next():
    res = models.Catalogue.query(q={
        'query': {
            'filtered': {
                'filter': {
                    'missing': {
                        'field': 'assigned_to'
                    }
                }
            }
        },
        'sort': {'created_date.exact': 'desc'},
        'size': 1
    })
    try:
        rec = res['hits']['hits'][0]['_source']
        if request.method == 'POST' or request.values.get('haveit',False):
            current_user.assign(ids=[rec['id']])
        resp = make_response( json.dumps( rec ) )
        resp.mimetype = "application/json"
        return resp
    except:
        abort(404)
