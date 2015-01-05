
from flask import Flask, request, abort, render_template, make_response
from flask.views import View
from flask.ext.login import login_user, current_user

import portality.models as models
import portality.util as util
from portality.core import app, login_manager

from portality.view.account import blueprint as account
from portality.view.nav import blueprint as nav
from portality.view.media import blueprint as media
from portality.view.query import blueprint as query
from portality.view.stream import blueprint as stream
from portality.view.hooks import blueprint as hooks
from portality.view.api import blueprint as api
from portality.view.pagemanager import blueprint as pagemanager
from portality.view.feed import blueprint as feed


app.register_blueprint(account, url_prefix='/account')
app.register_blueprint(nav, url_prefix='/nav')
app.register_blueprint(media, url_prefix='/media')
app.register_blueprint(query, url_prefix='/query')
app.register_blueprint(stream, url_prefix='/stream')
app.register_blueprint(hooks, url_prefix='/hooks')
app.register_blueprint(api, url_prefix='/api')
app.register_blueprint(feed)
app.register_blueprint(pagemanager)


@login_manager.user_loader
def load_account_for_login_manager(userid):
    out = models.Account.pull(userid)
    return out

@app.context_processor
def set_current_context():
    """ Set some template context globals. """
    return dict(current_user=current_user, app=app)

@app.before_request
def standard_authentication():
    """Check remote_user on a per-request basis."""
    remote_user = request.headers.get('REMOTE_USER', '')
    try:
        apik = request.headers['API_KEY']
    except:
        try:
            apik = request.headers['api_key']
        except:
            try:
                apik = request.json['API_KEY']
            except:
                try:
                    apik = request.json['api_key']
                except:
                    try:
                        apik = request.values['API_KEY']
                    except:
                        try:
                            apik = request.values['api_key']
                        except:
                            apik = False
    if remote_user:
        user = models.Account.pull(remote_user)
        if user:
            login_user(user, remember=False)
    # add a check for provision of api key
    elif apik:
        res = models.Account.query(q='api_key:"' + apik + '"')['hits']['hits']
        if len(res) == 1:
            user = models.Account.pull(res[0]['_source']['id'])
            if user is not None:
                login_user(user, remember=False)


@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

@app.errorhandler(401)
def page_not_found(e):
    return render_template('401.html'), 401
        

@app.route('/docs')
def docs():
    return render_template('docs.html')


@app.route('/catalogue')
@app.route('/catalogue/<rid>')
def record(rid=False):
    if rid:
        record = models.Catalogue.pull(rid.replace('.json',''))
        if record is None:
            abort(404)
        elif util.request_wants_json():
            resp = make_response( record.json )
            resp.mimetype = "application/json"
            return resp
        else:
            return render_template('catalogue.html',record=record)
    else:
        return render_template('catalogue.html')

    
@app.route('/fact')
@app.route('/fact/<rid>')
def fact(rid=False):
    if rid:
        record = models.Fact.pull(rid.replace('.json',''))
        if record is None:
            abort(404)
        elif util.request_wants_json():
            resp = make_response( record.json )
            resp.mimetype = "application/json"
            return resp
        else:
            return render_template('fact.html',record=record)
    else:
        return render_template('fact.html')


if __name__ == "__main__":
    app.run(host='0.0.0.0', debug=app.config['DEBUG'], port=app.config['PORT'])

