# ========================
# MAIN SETTINGS

# make this something secret in your overriding app.cfg
SECRET_KEY = "default-key"

# contact info
ADMIN_NAME = "Cottage Labs"
ADMIN_EMAIL = ""

# service info
SERVICE_NAME = "ContentMine"
SERVICE_TAGLINE = ""
HOST = "0.0.0.0"
DEBUG = True
PORT = 5014

# elasticsearch settings
ELASTIC_SEARCH_HOST = "http://127.0.0.1:9200" # remember the http:// or https://
ELASTIC_SEARCH_DB = "contentmine"
INITIALISE_INDEX = True # whether or not to try creating the index and required index types on startup

# list of superuser account names
SUPER_USER = ["test","peter"]

# Can people register publicly? If false, only the superuser can create new accounts
PUBLIC_REGISTER = False

# can anonymous users get raw JSON records via the query endpoint?
PUBLIC_ACCESSIBLE_JSON = True 


# ========================
# MAPPING SETTINGS

# a dict of the ES mappings. identify by name, and include name as first object name
# and identifier for how non-analyzed fields for faceting are differentiated in the mappings
FACET_FIELD = ".exact"
MAPPINGS = {
    "record" : {
        "record" : {
            "date_detection": False,
            "dynamic_templates" : [
                {
                    "default" : {
                        "match" : "*",
                        "match_mapping_type": "string",
                        "mapping" : {
                            "type" : "multi_field",
                            "fields" : {
                                "{name}" : {"type" : "{dynamic_type}", "index" : "analyzed", "store" : "no"},
                                "exact" : {"type" : "{dynamic_type}", "index" : "not_analyzed", "store" : "yes"}
                            }
                        }
                    }
                }
            ]
        }
    }
}
MAPPINGS['account'] = {'account':MAPPINGS['record']['record']}
MAPPINGS['pages'] = {'pages':MAPPINGS['record']['record']}
MAPPINGS['catalogue'] = {'catalogue':MAPPINGS['record']['record']}
MAPPINGS['fact'] = {'fact':MAPPINGS['record']['record']}
MAPPINGS['assignment'] = {'assignment':MAPPINGS['record']['record']}


# ========================
# QUERY SETTINGS

# list index types that should not be queryable via the query endpoint
NO_QUERY = ['account']

# list additional terms to impose on anonymous users of query endpoint
# for each index type that you wish to have some
# must be a list of objects that can be appended to an ES query.bool.must
# for example [{'term':{'visible':True}},{'term':{'accessible':True}}]
ANONYMOUS_SEARCH_TERMS = {
    "pages": [{'term':{'visible':True}},{'term':{'accessible':True}}]
}

# a default sort to apply to query endpoint searches
# for each index type that you wish to have one
# for example {'created_date' + FACET_FIELD : {"order":"desc"}}
DEFAULT_SORT = {
    "pages": {'created_date' + FACET_FIELD : {"order":"desc"}}
}


# ========================
# MEDIA SETTINGS

# location of media storage folder
MEDIA_FOLDER = "media"


# ========================
# PAGEMANAGER SETTINGS

# folder name for storing page content
# will be added under the templates/pagemanager route
CONTENT_FOLDER = "content"

# etherpad endpoint if available for collaborative editing
COLLABORATIVE = 'http://pads.cottagelabs.com'

# when a page is deleted from the index should it also be removed from 
# filesystem and etherpad (if they are available in the first place)
DELETE_REMOVES_FS = False # True / False
DELETE_REMOVES_EP = False # MUST BE THE ETHERPAD API-KEY OR DELETES WILL FAIL

# disqus account shortname if available for page comments
COMMENTS = ''


# ========================
# CALLERS SETTINGS
# expected to be relative to wherever the contentmine site/API service is cloned and running
# e.g. /opt/contentmine/src/site/

SCRAPER_DIRECTORY = 'journal-scrapers/scrapers/'
STORAGE_DIRECTORY = 'portality/static/scraping/'
SPECIES_DIRECTORY = 'portality/static/species/'
SPECIES_OUTPUT = 'target/'

# ========================
# HOOK SETTINGS

REPOS = {
    "contentMine.wiki": {
        "path": "/opt/contentmine/src/contentmine/portality/templates/pagemanager/content/contentMine.wiki"
    }
}


# ========================
# FEED SETTINGS

BASE_URL = "http://contentmine.org"
FEED_TITLE = "ContentMine"

# Maximum number of feed entries to be given in a single response.  If this is omitted, it will
# default to 20
MAX_FEED_ENTRIES = 100

# Maximum age of feed entries (in seconds) (default value here is 30 days).
MAX_FEED_ENTRY_AGE = 2592000

# NOT USED IN THIS IMPLEMENTATION
# Which index to run feeds from
#FEED_INDEX = "journal"

# Licensing terms for feed content
FEED_LICENCE = "(c) ContentMine 2014. CC-BY."

# name of the feed generator (goes in the atom:generator element)
FEED_GENERATOR = "CottageLabs feed generator"

# Larger image to use as the logo for all of the feeds
FEED_LOGO = "http://contentmine.org/static/favicon.ico"
