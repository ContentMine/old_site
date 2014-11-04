
function contentmine(options) {
    var about = {
        version: 0.1,
        author: "Mark MacGillivray",
        created: "21102014",
        description: "A javascript client that operates against the ContentMine API"
    };
    var defaults = {
        api: 'https://contentmine.org/api',
        api_key: ''
    };
    this.options = $.extend(defaults, options);
    this.response = {};
}

contentmine.prototype = {
    send: function(action, o) {
        var type = 'POST';
        o.type ? type = o.type : false;
        this.options.api_key && !o.data.api_key ? o.data.api_key = this.options.api_key : false;
        var vars = {
            type: type,
            url: this.options.api + '/' + action,
            cache: false,
            context: this
        }
        if ( o.type == 'POST' && o.data ) {
            vars.contentType = 'application/json';
            vars.dataType = 'JSON';
            vars.processData = false;
            vars.data = JSON.stringify(o.data);
        } else if ( o.type == 'GET' && o.data ) {
            vars.dataType = 'JSONP';
            if ( 'query' in o.data ) {
                vars.url += '?source=' + JSON.stringify(o.data);
            } else {
                vars.url += '?' + $.param(o.data);
            }
        }
        vars.success = function(res) {
            this.response = res;
            if ( !this.options.api_key && res.api_key ) {
                this.options.api_key = res.api_key;
            }
            if ( !this.options.username && res.username ) {
                this.options.username = res.username;
            }
            typeof o.success == 'function' ? o.success(res) : false;
        }
        typeof o.error == 'function' ? vars.error = o.error : false;
        $.ajax(vars);
    },
    process: function(o) {
        var addr = 'process';
        // process can be one of unprocessed, processor name, CSV list of processor name, assign, unassign, assigned
        o.process ? addr += '/' + o.process : false;
        !o.process && !o.type ? o.type = 'GET' : false;
        this.send(addr, o);
    },
    catalogue: function(o) {
        var addr = 'catalogue';
        // catalogue can be query or a catalogue record ID
        o.catalogue ? addr += '/' + o.catalogue : false;
        this.send(addr, o);
    },
    processor: function(o) {
        var addr = 'processor';
        o.processor ? addr += '/' + o.processor : false;
        this.send(addr, o);
    },
    fact: function(o) {
        var addr = 'fact';
        // o.fact could be one of query, daily or a fact ID
        o.fact ? addr += '/' + fact : false;
        this.send(addr, o);
    }
}


