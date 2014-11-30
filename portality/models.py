
from datetime import datetime

from portality.core import app

from portality.dao import DomainObject as DomainObject

import requests

'''
Define models in here. They should all inherit from the DomainObject.
Look in the dao.py to learn more about the default methods available to the Domain Object.
When using portality in your own flask app, perhaps better to make your own models file somewhere and copy these examples
'''


class Fact(DomainObject):
    __type__ = ('fact')
    
    @property
    def parent(self):
        try:
            catalogue = Catalogue.pull(self.data['source'])
            return catalogue.json
        except:
            return False

    @property
    def siblings(self):
        try:
            count = self.query(q='source.exact:"' + self.data['source'] + '"')
            return count['hits']['total']
        except:
            return 0

    
class Catalogue(DomainObject):
    __type__ = 'catalogue'
        

# an example account object, which requires the further additional imports
# There is a more complex example below that also requires these imports
from werkzeug import generate_password_hash, check_password_hash
from flask.ext.login import UserMixin

class Account(DomainObject, UserMixin):
    __type__ = 'account'

    @classmethod
    def pull_by_email(cls,email):
        res = cls.query(q='email:"' + email + '"')
        if res.get('hits',{}).get('total',0) == 1:
            return cls(**res['hits']['hits'][0]['_source'])
        else:
            return None

    def set_password(self, password):
        self.data['password'] = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.data['password'], password)

    @property
    def is_super(self):
        return not self.is_anonymous() and self.id in app.config['SUPER_USER']
    
    def assign(self,ids=[]):
        ln = len(ids)
        if ln > 1000: ln = 1000
        tlen = ln - len(self.assigned)
        if tlen < 1:
            return []
        else:
            ids = ids[:tlen]
            assigned = []
            for iid in ids:
                check = Catalogue.pull(iid)
                if check is not None and 'assigned_to' not in check.data:
                    check.data['assigned_to'] = self.id
                    check.data['assigned_date'] = datetime.now().strftime("%Y-%m-%d %H%M")
                    check.save()
                    assigned.append(iid)
            return assigned
    
    def unassign(self):
        for iid in self.assigned:
            a = Catalogue.pull(iid)
            if a.data.get('assigned_to',False) == self.id:
                del a.data['assigned_to']
                del a.data['assigned_date']
                a.save()
    
    @property
    def assigned(self):
        return [i['_source']['id'] for i in Catalogue.query(q='assigned_to.exact:"' + self.id + '"', size=1000).get('hits',{}).get('hits',[])]
    

# a typical record object, with no special abilities
class Record(DomainObject):
    __type__ = 'record'

    
# a special object that allows a search onto all index types - FAILS TO CREATE INSTANCES
class Everything(DomainObject):
    __type__ = 'everything'

    @classmethod
    def target(cls):
        t = 'http://' + str(app.config['ELASTIC_SEARCH_HOST']).rstrip('/') + '/'
        t += app.config['ELASTIC_SEARCH_DB'] + '/'
        return t


# a page manager object, with a couple of extra methods
class Pages(DomainObject):
    __type__ = 'pages'

    @classmethod
    def pull_by_url(cls,url):
        res = cls.query(q={"query":{"term":{'url.exact':url}}})
        if res.get('hits',{}).get('total',0) == 1:
            return cls(**res['hits']['hits'][0]['_source'])
        else:
            return None

    def update_from_form(self, request):
        newdata = request.json if request.json else request.values
        for k, v in newdata.items():
            if k == 'tags':
                tags = []
                for tag in v.split(','):
                    if len(tag) > 0: tags.append(tag)
                self.data[k] = tags
            elif k in ['editable','accessible','visible','comments']:
                if v == "on":
                    self.data[k] = True
                else:
                    self.data[k] = False
            elif k not in ['submit']:
                self.data[k] = v
        if not self.data['url'].startswith('/'):
            self.data['url'] = '/' + self.data['url']
        if 'title' not in self.data or self.data['title'] == "":
            self.data['title'] = 'untitled'

    def save_from_form(self, request):
        self.update_from_form(request)
        self.save()
    

