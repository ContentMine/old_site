/*
 * jquery.graphview.js
 *
 * displays graph data results retrieved by querying a specified index
 * 
 * created by Mark MacGillivray - mark@cottagelabs.com
 *
 * copyheart 2013
 *
 * VERSION 0.3.0
 *
 *
 */


/* this software comes with some defaults for building a UI on the page, for 
binding actions to that UI, for reading and sending a query to the target, 
for building results onto the page when the response is retrieved. All of these 
can be overwritten. See the defaults for some overview and look at the individual 
default functions defined below to figure out how to copy and augment one.

For example provide custom uitemplate and uibindings functions to build specific 
UIs. Then provide custom query and executequery functions to read the query from 
the UI and to execute it with some cleaning. Then provide custom showresults to 
put them on the page as desired. Or some combination of the lot. */


// Deal with indexOf issue in <IE9
// provided by commentary in repo issue - https://github.com/okfn/facetview/issues/18
if (!Array.prototype.indexOf) {
    Array.prototype.indexOf = function(searchElement /*, fromIndex */ ) {
        "use strict";
        if (this == null) {
            throw new TypeError();
        }
        var t = Object(this);
        var len = t.length >>> 0;
        if (len === 0) {
            return -1;
        }
        var n = 0;
        if (arguments.length > 1) {
            n = Number(arguments[1]);
            if (n != n) { // shortcut for verifying if it's NaN
                n = 0;
            } else if (n != 0 && n != Infinity && n != -Infinity) {
                n = (n > 0 || -1) * Math.floor(Math.abs(n));
            }
        }
        if (n >= len) {
            return -1;
        }
        var k = n >= 0 ? n : Math.max(len - Math.abs(n), 0);
        for (; k < len; k++) {
            if (k in t && t[k] === searchElement) {
                return k;
            }
        }
        return -1;
    }
}


(function($){
    $.fn.graphview = function(options) {


        // ===============================================
        // ===============================================
        //
        // set defaults
        //
        // ===============================================
        // ===============================================

        var defaults = {
            "target": 'http://localhost:5005/everything', // the ES _search endpoint address to query
            "ajaxtype": "GET",
            "datatype": "JSONP", // ajax datatype
            
            // probably remove graphable from example altogether, as it relies on CL backend stuff.
            "graphable": { // if customised graphable endpoint is available, configure it here
                "enabled": false,
                "ignore":[], 
                "only":[], 
                "promote":{'record':['keywords','tags']}, 
                "links":{'wikipedia':['topic'],'reference':['_parents'],'record':['children']},
                "ignoreisolated":false,
                "dropfacets":true,
                "drophits":true,
                "remote_source": "http://129.67.24.26:9200/test/record/_search"
            },

            "suggestsize": 100, // how many suggestions to show in search area dropdowns
            "nodesize": 100, // default number of nodes of each type to show
            "titlefield": "title.exact", // which field from result object is default title field
            
            "defaultquery": { // define the starting query here - see ES docs
                "query": {
                    "bool": {
                        "must":[]
                    }
                },
                "fields": "*",
                "partial_fields": [],
                "from":0,
                "size":100,
                "facets":{
                    // ES facet settings, plus suggest:true to add to freetext dropdown controller
                    // and node:true to add as a node type for viewing in the graphview
                    "journals": {"term":{"field":"journal.name.exact","suggest": true, "node": true}},
                    "authors": {"term":{"field":"author.name.exact","suggest": true, "node": true}},
                    "titles": {"term":{"field":"title.exact","suggest": true, "node": true}},
                    "keywords": {"term":{"field":"keyword.exact","suggest": true, "node": false}},
                    "range": {"date_histogram": {"interval": "month", "field": "date"}}
                }
            },

            "nested": [],
            "sort":[],
            "default_operator": "AND", // ES default operator param
            "query_string_fuzzify": "*", // this and default_operator are used by default query function

            "fill": "a function that provides colors to be used on the bubbles. default defined below",

            "showresults": "a function that displays the query results - takes data obj as param (default defined below)",
            "response": "the default showresults writes the query results object into this key, for further access",
            "nodes": "for building a force graph, the node data is required. the default showresults calculates and stores here",
            "links": "links data is also required for the default force graph. default showresults calculates and stores here",
            "linksindex": "and similarly an index of links and what nodes they attach to, at various depths",
            "afterresults": false, // define a callback function to run once the default showresults is finished
            
            "dragging": false, // the default UI and query allow nodes to be dragged on the search. A dragged node can be found here
            "query": "is a function that returns the current query object (default defined below)",
            "executequery": "the function to run when a query should be executed (the default is defined below)",
            
            "uitemplate": "a function that returns a template (e.g. a bunch of html) for the UI controls to be created (default defined below)",
            "uibindings": "things to be bound to the ui template once it has been appended to the target element. Limit the bindings to obj",
            
            "sharesave": true, // shows a button that provides the current query for copying
            "sharesave_include_facets": false, // include facets in above or not (longer querystring)
            
            "searchonload": true, // run default search as soon as page loads
            "pushstate": false, // put current query state in url whenever it updates
            "focusdepth": 1 // how many nodes removed to highlight during hover
            // more than depth 1 is probably a bad idea unless the depths are calculated server-side...
            // if there are sufficiently complex relations it can take a long time to process in the client
            
        };





        // ===============================================
        // ===============================================
        // 
        // force directed network graph functions
        //
        // these are used by the default results display
        //
        // ===============================================
        // ===============================================

        defaults.fill = d3.scale.category10();

        var label = function(d) {
            // calculate a label
            var label = '';
            if ( d.value ) { d.value > 1 ? label += '(' + d.value + ') ' : false; }
            if ( d.className ) {
                if ( isNaN(d.className) ) {
                    label += d.className;//.substr(0,35);
                    if ( d.className.length == 0 || d.className == "\n" ) {
                        label += 'No title';
                    }
                    d.className.length > 35 ? label += '...' : false;
                } else if ( Date.parse(d.className) ) {
                    var date = new Date(d.className);
                    label += date.getDate() + '/' + (date.getMonth() + 1) + '/' + date.getFullYear();
                } else if (date = new Date(d.className) ) {
                    if ( date.getDate() && date.getMonth() && date.getFullYear() ) {
                        label += date.getDate() + '/' + (date.getMonth() + 1) + '/' + date.getFullYear();
                    } else {
                        label += d.className;
                    }
                } else {
                    label += d.className;
                }
            }
            return label;
        }
    
        var force = function() {

            // a function to check the dict of linked things
            function isConnected(a, b) {
                return options.linksindex.d1[a.index + "," + b.index] || options.linksindex.d1[b.index + "," + a.index] || a.index == b.index || options.linksindex.d2[a.index + "," + b.index] || options.linksindex.d2[b.index + "," + a.index] || options.linksindex.d3[a.index + "," + b.index] || options.linksindex.d3[b.index + "," + a.index];
            }
            // when a node is hovered, opacify any nodes / links not connected to it
            var highlight = function(opacity) {
                return function(d) {
                    //$('.nodetitle').remove();
                    node.style("stroke","transparent").style("stroke", function(o) {
                        thisOpacity = d === o && opacity != 1 ? "#333" : "transparent";
                        //opacity != 1 && thisOpacity == "#333" ? showtitle(this) : false;
                        return thisOpacity;
                    });

                    link.style("stroke", function(o) {
                        return opacity == 1 ? "#ccc" : "#333";
                    }).style("stroke", function(o) {
                        return isConnected(d,o.source) && isConnected(d,o.target) && opacity != 1 ? "#333" : "#ccc";
                    }).style("stroke-width", function(o) {
                        return opacity == 1 ? 1 : 1.5;
                    }).style("stroke-width", function(o) {
                        return isConnected(d,o.source) && isConnected(d,o.target) && opacity != 1 ? 1.5 : 1;
                    });
                    opacity == .1 ? setTimeout(function() {options.dragging = false;}, 200) : false;
                };
            };

            // build the vis area
            var w = obj.width();
            var h = obj.height();
            var vis = d3.select(".graphview_panel")
                .append("svg:svg")
                .attr("width", w)
                .attr("height", h)
                .attr("pointer-events", "all")
                .append('svg:g')
                .call(d3.behavior.zoom().on("zoom", redraw))
                .append('svg:g');

            vis.append('svg:rect')
                .attr('width', w)
                .attr('height', h)
                .attr('fill', 'transparent');

            // fade in whenever transitions occur
            vis.style("opacity", 1e-6)
                .transition()
                .duration(1000)
                .style("opacity", 1);

            // redraw on zoom
            function redraw() {
                vis.attr("transform",
                    "translate(" + d3.event.translate + ")"
                    + " scale(" + d3.event.scale + ")"
                );
            }

            // start the force layout
            var force = d3.layout.force()
                .charge(-160)
                .linkDistance(100)
                .nodes(options.nodes)
                .links(options.links)
                .size([w, h])
                .start();

            // put links on it
            var link = vis.selectAll("line.link")
                .data(options.links)
                .enter().append("svg:line")
                .attr("class", "link")
                .attr("stroke", "#ddd")
                .attr("stroke-opacity", 0.8)
                .style("stroke-width", function(d) { return Math.sqrt(d.value); })
                .attr("x1", function(d) { return d.source.x; })
                .attr("y1", function(d) { return d.source.y; })
                .attr("x2", function(d) { return d.target.x; })
                .attr("y2", function(d) { return d.target.y; });

            // put the nodes on it
            var dom = d3.extent(options.nodes, function(d) {
                return d.value;
            });
            var cr = d3.scale.sqrt().range([5, 25]).domain(dom);
            var node = vis.selectAll("circle.node")
                .data(options.nodes)
                .enter().append("svg:circle")
                .attr("class", "node")
                .attr("name", function(d) { return label(d); })
                .attr("cx", function(d) { return d.x; })
                .attr("cy", function(d) { return d.y; })
                .attr("r", function(d) { return cr(d.value); })
                .style("fill", function(d) { return options.fill(d.group); })
                .call(force.drag)
                .on("mouseover", highlight(.1))
                .on("mouseout", highlight(1))
                .on("mousedown",function(d) { options.dragging = d });

            // put a hover a label on
            node.append("svg:title")
                .text(function(d) { return label(d); });

            // make the cursor a click pointer whenever hovering a node
            $('.node').css({"cursor":"pointer"});

            // put a label next to each node
            // TODO: change this to be part of highlight so that only hovered / related nodes have labels
            /*var texts = vis.selectAll("text.label")
                .data(options.nodes)
                .enter().append("text")
                .attr("class", "svglabel")
                .attr("fill", "#bbb")
                .text(function(d) {  return label(d); });*/

            // define the changes that happen when the diagram ticks over
            force.on("tick", function() {
                link.attr("x1", function(d) { return d.source.x; })
                    .attr("y1", function(d) { return d.source.y; })
                    .attr("x2", function(d) { return d.target.x; })
                    .attr("y2", function(d) { return d.target.y; });

                node.attr("cx", function(d) { return d.x; })
                    .attr("cy", function(d) { return d.y; });

                /*texts.attr("transform", function(d) {
                    return "translate(" + (d.x - cr(d.value) + 15) + "," + (d.y + cr(d.value) + 5) + ")";
                });*/

            });
        
        };
        





        // ===============================================
        // ===============================================
        //
        // visualisation data prep functions
        //
        // ===============================================
        // ===============================================

        // loop  over an object with a dot notation route to its value if found
        // used in the following setnodesandlinks() function
        var findthis = function(routeparts,o,matcher) {
            // first check if there is a field named with the concatenation of parts, which can be the case with specified fields
            if ( o[routeparts[0]] ) {
                if ( typeof(o[routeparts[0]]) == 'object' ) {
                    if ( $.isArray(o[routeparts[0]]) ) {
                        if ( typeof(o[routeparts[0]][0]) == 'object' ) {
                            var matched = false;
                            for ( var i in o[routeparts[0]] ) {
                                !matched ? matched = findthis(routeparts.slice(1),o[routeparts[0]][i],matcher) : false;
                            }
                            return matched;
                        } else {
                            if ( o[routeparts[0]].indexOf(matcher) != -1 ) {
                                return true;
                            } else {
                                return false;
                            }
                        }
                    } else {
                        return findthis(routeparts.slice(1),o[routeparts[0]],matcher);
                    }
                } else {
                    if ( $.isArray(o[routeparts[0]]) ) {
                        if ( typeof(o[routeparts[0]][0]) == 'object' ) {
                            var matched = false;
                            for ( var i in o[routeparts[0]] ) {
                                !matched ? matched = findthis(routeparts.slice(1),o[routeparts[0]][i],matcher) : false;
                            }
                            return matched;
                        } else {
                            if ( o[routeparts[0]].indexOf(matcher) != -1 ) {
                                return true;
                            } else {
                                return false;
                            }
                        }
                    } else if ( matcher == o[routeparts[0]] ) {
                        return true;
                    } else {
                        return false;
                    }
                }
            } else if ( o[routeparts.join('.')] ) {
                return findthis([routeparts.join('.')],o,matcher);
            } else {
                return false;
            }
        }

        // calculate nodes and links from a result set
        var setnodesandlinks = function() {
            options.nodes = [];
            for ( var i in options.response.hits.hits ) {
                //var rec = options.response.hits.hits[i]._source;
                //rec == undefined ? rec = options.response.hits.hits[i].fields : false;
                var rec = options.response.hits.hits[i]._source !== undefined ? options.response.hits.hits[i]._source : options.response.hits.hits[i].fields;
                rec === undefined ? rec = {} : false;
                rec[options.titlefield] === undefined ? rec[options.titlefield] = "No name" : false;
                var arr = {
                    "record":rec,
                    "className": rec[options.titlefield],
                    "group": "records",
                    "value": 0,
                    "facet": "none"
                }
                //arr.className == undefined ? arr.className = indata.projectComposition.project.title : false; // ADDED FOR GTR
                options.nodes.push(arr);
            };
            var links = [];
            $('.graphview_facetsizer').remove();
            $('.graphview_nodetype:checked', obj).each(function() {
                var key = $(this).attr('data-field');
                var obj = options.response.facets[key];
                var facetcount = ' <input id="' + key.replace(/\./g,'_') + '_graphview_facetsize" class="graphview_facetsizer" style="width:30px;padding:0;margin:0;font-size:10px;" type="text" value="' + obj.terms.length + '" />';
                $(this).parent().append(facetcount);
                for ( var item in obj.terms ) {
                    var trec = obj.terms;
                    var arr = {
                        "className": trec[item].term,
                        "group": key,
                        "value": trec[item].count,
                        "facet": key
                    }
                    options.nodes.push(arr);
                    
                    for ( var x = 0; x < options.response.hits.hits.length; x++ ) {
                        var record = options.nodes[x].record;
                        var route = key; //.replace('.exact','');
                        var source = options.nodes.length-1;
                        var target = x;
                        var value = 1;
                        if ( findthis(route.split('.'), record, trec[item].term) ) {
                            links.push({"source":source,"target":target,"value":value});
                        }
                    };
                };            
            });
            $('.graphview_facetsizer').bind('change',options.executequery);
            options.links = links;

            // build a dict that tells us which things are linked
            options.linksindex = {'d1':{},'d2':{},'d3':{}};
            options.links.forEach(function(d) {
                options.linksindex.d1[d.source + "," + d.target] = 1;
                if ( options.focusdepth > 1 ) {
                    options.links.forEach(function(d2) {
                        if ( d2.target == d.target && d2.source != d.source ) {
                            options.linksindex.d2[d.source + "," + d2.source] = 1;
                        }
                        if ( d2.source == d.source && d2.target != d.target ) {
                            options.linksindex.d2[d.target + "," + d2.target] = 1;
                        }
                        if ( options.focusdepth > 2 ) {
                            options.links.forEach(function(d3) {
                                if ( d3.target == d2.target && d3.source != d2.source ) {
                                    options.linksindex.d3[d.source + "," + d3.source] = 1;
                                }
                                if ( d3.source == d2.source && d3.target != d2.target ) {
                                    options.linksindex.d3[d.target + "," + d3.target] = 1;
                                }
                            
                            });
                        }
                    });
                }
            });

        }




        // ===============================================
        // ===============================================
        //
        // default results display
        //
        // ===============================================
        // ===============================================
        
        defaults.showresults = function(data) {
            // put the response data in the response option
            data ? options.response = data : false;
            // do some cleaning
            $('.graphview_panel', obj).html('');
            $('.graphview_panel', obj).css({"overflow":"visible"});
            $('.graphview_total', obj).html(options.response.hits.total);
            
            // when graphable backend is available, get the nodes and links from it
            if ( options.graphable.enabled ) {
                options.nodes = options.response.nodes;
                options.links = options.response.links;
                // options.linksindex = options.response.linksindex; TODO: make this work on the backend and pass depth params
            } else { 
                // otherwise generate them
                setnodesandlinks();
            }
            force();
            typeof options.afterresults == 'function' ? options.afterresults.call(this) : false;
            $('.graphview_loading', obj).hide();
        };
        


        // ===============================================
        // ===============================================
        //
        // default query functions
        //
        // defaults.query() builds and returns a query object 
        // from current page state
        //
        // defaults.executequery() sends the query to the 
        // target and calls showresults when a suitable 
        // response is retrieved
        //
        // ===============================================
        // ===============================================

        defaults.query = function() {
            // fuzzify the freetext search query terms if required
            var fuzzify = function(querystr) {
                var rqs = querystr;
                if ( options.query_string_fuzzify !== undefined ) {
                    if ( options.query_string_fuzzify == "*" || options.query_string_fuzzify == "~" ) {
                        if ( querystr.indexOf('*') == -1 && querystr.indexOf('~') == -1 && querystr.indexOf(':') == -1 ) {
                            var optparts = querystr.split(' ');
                            pq = "";
                            for ( var oi = 0; oi < optparts.length; oi++ ) {
                                var oip = optparts[oi];
                                if ( oip.length > 0 ) {
                                    oip = oip + options.query_string_fuzzify;
                                    options.query_string_fuzzify == "*" ? oip = "*" + oip : false;
                                    pq += oip + " ";
                                }
                            };
                            rqs = pq;
                        };

                    };
                };
                return rqs;
            };

            // TODO: find things in the obj with attr data-something
            // this should tell if it is a query_string, a facet value, a setting of some sort
            // set them all into the options.currentstate
            // they will be used to build the elasticsearch query
            options.defaultquery.size = parseInt($('.graphview_to', obj).val()) - parseInt($('.graphview_from', obj).val());
            options.defaultquery.from = $('.graphview_from', obj).val();
            // copy the default query
            var qry = $.extend(true, {}, options.defaultquery);
            qry["facets"] = {};
            // add any selections to the query
            var vals = $('.query_string', obj).select2("val");
            if ( vals.length != 0 ) {
                for ( var i in vals ) {
                    var kv = vals[i].split('__________');
                    if ( kv.length == 1 ) {
                        qry.query.bool.must.push({"query_string":{"query":fuzzify(kv[0]), "default_operator": options.default_operator}});
                    } else {
                        var qobj = {"term":{}};
                        qobj.term[kv[0]] = kv[1];
                        qry.query.bool.must.push(qobj);
                    }
                }
            } else {
                qry.query.bool.must.push({"match_all":{}});
            }
            // check for any ranged values to add to the bool
            if ( $('.lowvalue', obj).val() || $('.highvalue', obj).val() ) {
                var ranged = {
                    'range': {
                        'year': {
                        }
                    }
                };
                $('.lowvalue',obj).val().length ? ranged.range.year.from = endater( $('.lowvalue', obj).val() ) : false;
                $('.highvalue',obj).val().length ? ranged.range.year.to = endater( $('.highvalue', obj).val() ) : false;
                qry.query.bool.must.push(ranged);
            };
            
            // request facets for the selected nodetypes
            $('.graphview_nodetype:checked', obj).each(function() {
                var bb = $(this).attr('data-field');
                if ( bb.length != 0 ) {
                    var size = options.nodesize;
                    if ( $('#' + bb.replace(/\./g,'_') + '_graphview_facetsize', obj).val() ) {
                        size = $('#' + bb.replace(/\./g,'_') + '_graphview_facetsize', obj).val();
                    };
                    var f = {
                        "terms": {
                            "field": bb,
                            "order": "count",
                            "size": size
                        }
                    }
                    qry.facets[bb] = f;
                };
            });
            // add graphing parameters if the backend supports graphing
            options.graphable.enabled ? qry.graph = options.graphable : false;
            return qry;
        };

        defaults.executequery = function(event) {
            // do nothing if triggered by mouseover when nothing is being dragged
            if ( !(event !== undefined && event.type == "mouseover" && !options.dragging) ) {
                // show the loading image
                $('.graphview_loading', obj).show();
                // get the current dataset of the select box
                var selectdata = $('.query_string',obj).select2("data");
                // check if a new search term is being dragged onto the search area
                if ( options.dragging ) {
                    if ( options.dragging.group == "records" ) {
                        var did = options.dragging.className
                    } else {
                        var did = options.dragging.group + "__________" + options.dragging.className
                    }
                    selectdata.push({
                        "id":did, 
                        "text": options.dragging.className
                    });
                    $('.query_string', obj).select2("data",selectdata);
                    options.dragging = false;
                }            
                // remove numbers from choices and set their colors to match their types
                $('.select2-search-choice', obj).each(function(i) {
                    var kv = selectdata[i]['id'].split('__________');
                    if ( kv.length > 1 ) {
                        $(this).css({"color":options.fill(kv[0])});
                    }
                    var nonumber = $(this).children('div').text().replace(/ \([0-9]*\)/,'');
                    $(this).children('div').text(nonumber);
                });
                // put the current query state into the URL if set
                options.pushstate ? window.history.pushState("", "search", '?source=' + JSON.stringify(options.query())): false;
                // set the ajax options then execute
                var ajaxopts = {
                    type: options.ajaxtype,
                    url: options.target,
                    contentType: "application/json; charset=utf-8",
                    dataType: options.datatype,
                    success: options.showresults
                };
                if ( options.ajaxtype != 'POST' ) {
                    ajaxopts.url += '?source=' + JSON.stringify(options.query());
                } else {
                    // TODO: add the query as data to the ajax opts
                }
                $.ajax(ajaxopts);
            };
        };
        




        // ===============================================
        // ===============================================
        // ranged date functions
        // ===============================================
        // ===============================================

        var endater = function(d) {
            var reg = /(\d{2})-(\d{2})-(\d{4})/;
            var dateArray = reg.exec(d); 
            var dateObject = new Date(
                (+dateArray[3]),
                (+dateArray[2])-1,
                (+dateArray[1]),
                (+00),
                (+00),
                (+00)
            );
            return dateObject;
        };

        var ranged = function() {

            var dater = function(d) {
                var day = d.getDate();
                var month = d.getMonth() + 1;
                var year = d.getFullYear();
                var date = day + "-" + month + "-" + year;
                date = date.toString();
                var parts = date.split('-');
                parts[0].length == 1 ? parts[0] = '0' + parts[0] : "";
                parts[1].length == 1 ? parts[1] = '0' + parts[1] : "";
                date = parts[0] + '-' + parts[1] + '-' + parts[2];
                return date;
            };

            if ( $('.dateranged', obj).length == 0 ) { 
                $('.graphview', obj).append('<div class="dateranged" style="position:absolute;bottom:-5px;left:5%;z-index:1000;width:90%;"> \
                    <div style="width:10%;float:left;"> \
                        <input type="text" class="lowvalue" style="width:100%;" placeholder="from date" /> \
                    </div> \
                    <div style="width:70%;float:left;margin:0 20px 0 35px;"><div class="ranged" style="margin-top:8px;"></div></div> \
                    <div style="width:10%;float:left;"><input type="text" class="highvalue" style="width:100%;" placeholder="to date" /></div> \
                    </div>');

                var ranged_values = [];
                var entries = options.response.facets.ranged.entries;
                for ( var i=0, len=entries.length; i < len; i++ ) {
                    ranged_values.push(new Date(entries[i].time));
                };

                var opts = {
                    inline: true,
                    dateFormat: 'dd-mm-yy',
                    defaultDate: dater(ranged_values[0]),
                    minDate: dater(ranged_values[0]),
                    maxDate: dater(new Date()),
                    changeYear: true
                };

                $('.lowvalue', obj).datepicker(opts);
                $('.highvalue', obj).datepicker(opts);
                $('.lowvalue', obj).bind('change',options.executequery);
                $('.highvalue', obj).bind('change',options.executequery);
                $('.resolution', obj).val("year");
                $('.ranged', obj).slider({
                    range: true,
                    min: 0,
                    max: ranged_values.length-1,
                    values: [0, ranged_values.length-1],
                    slide: function( event, ui ) {
                        $('.lowvalue', obj).val( dater(ranged_values[ ui.values[0] ]) );
                        $('.highvalue', obj).val( dater(ranged_values[ ui.values[1] ]) ).trigger('change');
                    }
                });

            }
        }



        // ===============================================
        // ===============================================
        //
        // the graphview default UI
        //
        // defaults.uitemplate() and defaults.uibindings()
        //
        // ===============================================
        // ===============================================

        /*
         * TODO: For putting option changers on pages, give them an attribute called
         * data-option, with a value of the name of the option e.g. options.defaultquery.size
         * it will then automatically update when a query is performed
         */

        defaults.uitemplate = function() {
            var ui = '<div class="graphview" style="width:100%;height:100%;position:relative;">';
            
            ui += '<div class="graphview_searcharea" style="-webkit-border-radius:4px;-moz-border-radius:4px;border-radius:4px;position:absolute;top:5px;left:5px;z-index:1000;">';
            ui += '<select class="graphview_suggest" style="display:inline;width:180px;height:29px;margin-right:-2px;background:#eee;border-radius:5px 0px 0px 5px;">';
            ui += '<option style="color:' + options.fill("records") + ';" data-value="records">search everything</option>';
            for ( var key in options.defaultquery.facets ) {
                var obj = options.defaultquery.facets[key];
                if ( key != "range" && obj.term.suggest ) { // TODO: change this in case it is not a term facet?
                    ui += '<option data-value="' + obj.term.field + '" style="color:' + options.fill(obj.term.field) + ';">suggest ' + key + '</option>';
                    ui += ', ';
                }
            }
            ui += '</select>';
            ui += '<input type="text" class="query_string" style="width:400px;" data-option="query.bool.must.query_string.query" placeholder="mix and match some search terms" />';
            ui += ' <img class="graphview_loading" style="width:30px;margin-top:-10px;" src="loading.gif" />';
            ui += '</div>'; // closes searcharea

            ui += '<div class="graphview_optionsarea" style="position:absolute;top:40px;left:5px;z-index:1000;">';
            ui += '<input class="graphview_from" type="text" value="';
            ui += options.defaultquery.from;
            ui += '" style="width:40px;margin:-5px 0 0 0;padding:1px 1px 0 0;font-size:14px;color:#666;text-align:center;" />';
            ui += ' to ';
            ui += '<input class="graphview_to" type="text" value="';
            ui += options.defaultquery.size;
            ui += '" style="width:40px;margin:-5px 0 0 0;padding:1px 1px 0 0;font-size:14px;color:#666;text-align:center;" /> of \
                <span class="graphview_total" style="font-size:16px;font-weight:bold;color:#999;"></span>';
            ui += '</div>'; // closes optionsarea
            
            ui += '<div class="graphview_nodesarea" style="position:absolute;top:62px;left:5px;z-index:1000;">';
            for ( var key in options.defaultquery.facets ) {
                if ( key != "range" && options.defaultquery.facets[key].term.node ) { // TODO: change this in case the facet is not a term type?
                    var node = options.defaultquery.facets[key].term;
                    ui += '<div style="margin-right:2px;color:' + options.fill(node.field) + ';"><input type="checkbox" class="graphview_nodetype" data-field="' + node.field + '" /> ' + key + '</div>';
                }
            };
            ui += '</div>'; // closes nodesarea

            ui += '<div class="graphview_panel" style="position:absolute;top:0;left:0;"></div>';

            ui += '</div>'; // closes graphview

            return ui;
        }

        defaults.uibindings = function() {
            // attach select2 functionality to the query string input
            $('.query_string', obj).select2({
                "formatNoMatches": function() { return "type text and hit enter to search, choose and mix and match suggestion types, drag objects here to add them";},
                "tags": function(q) {
                    var field = options.suggest;
                    var qry = {
                        "query": {
                            "match_all": {}
                        },
                        "size": 0
                    };
                    if ( field !== undefined ) {
                        qry.facets = {
                            "tags":{
                                "terms": {
                                    "field": field,
                                    "order": "count",
                                    "size": options.suggestsize
                                }
                            }
                        };
                        if ( options.graphable.enabled ) {
                            qry.graph = options.graphable;
                            qry.graph.dropfacets = false;
                        };
                        qry.facets.tags.facet_filter = {"query": options.query().query };
                        var dropdownfilter = true;
                        if ( q.term.length ) {
                            if ( q.term.length == 1 ) {
                                var ts = {
                                    "bool":{
                                        "should":[
                                            {"prefix":{}},
                                            {"prefix":{}}
                                        ]
                                    }
                                };
                                ts.bool.should[0].prefix[field] = q.term.toLowerCase();
                                ts.bool.should[1].prefix[field] = q.term.toUpperCase();
                                qry.facets.tags.facet_filter.query.bool.must.push(ts);
                                qry.facets.tags.terms.order = "term";
                            } else {
                                if ( q.term.indexOf('*') != -1 || q.term.indexOf('~') != -1 || q.term.indexOf(':') != -1 ) {
                                    var qs = q.term;
                                    dropdownfilter = false;
                                } else if ( q.term.indexOf(' ') == -1 ) {
                                    var qs = '*' + q.term + '*';
                                } else {
                                    var qs = q.term.replace(/ /g,' AND ') + '*';
                                }
                                var ts = {
                                    "query_string":{
                                        "query": qs,
                                        "default_field": field.replace('.exact','')//,
                                        //"analyzer":"simple"
                                    }
                                };
                                qry.facets.tags.facet_filter.query.bool.must.push(ts);
                            }
                        };
                        if ( qry.facets.tags.facet_filter.query.bool.must.length == 0 ) {
                            delete qry.facets.tags.facet_filter;
                        };
                    };
                                            
                    $.ajax({
                        type: "POST",
                        url: options.target + '?source=' + JSON.stringify(qry),
                        contentType: "application/json; charset=utf-8",
                        dataType: options.datatype,
                        q: q,
                        field: field,
                        dropdownfilter: dropdownfilter,
                        success: function(data) {
                            var qa = this.q;
                            var t = qa.term, filtered = {results: []};
                            var tags = [];
                            if ( field !== undefined ) {
                                var terms = data.facets.tags.terms;
                                for ( var item in terms ) {
                                    tags.push({'id':this.field + '__________' + terms[item].term,'text':terms[item].term + ' (' + terms[item].count + ')'});
                                };
                            };
                            $(tags).each(function () {
                                var isObject = this.text !== undefined,
                                    text = isObject ? this.text : this;
                                if ( this.dropdownfilter ) {
                                    if (t === "" || qa.matcher(t, text)) {
                                        filtered.results.push(isObject ? this : {id: this, text: this});
                                    }
                                } else {
                                    filtered.results.push(isObject ? this : {id: this, text: this});
                                };
                            });
                            qa.callback(filtered);
                        }
                    });
                },
                "tokenSeparators":[","],
                "width":"element",
            });
            
            // add some customisation to select2 css
            $('.select2-choices', obj).css({
                "-webkit-border-radius":"3px",
                "-moz-border-radius":"3px",
                "border-radius":"3px",
                "border":"1px solid #ccc"
            });            

            // put some bindings to execute queries and so on onto the template
            $('.graphview_nodetype', obj).bind('change',options.executequery);
            $('.query_string', obj).bind('change',options.executequery);
            $('.query_string', obj).bind('mouseover',options.executequery);
            $('.graphview_to', obj).bind('change',options.executequery);
            $('.graphview_from', obj).bind('change', function(event) {
                $(this).val() > options.response.hits.total ? $(this).val(options.response.hits.total - 1) : false;
                options.defaultquery.from = $(this).val();
                var to = parseInt(options.defaultquery.from) + parseInt(options.defaultquery.size);
                to > options.response.hits.total ? to = options.response.hits.total : false;
                $('.graphview_to', obj).val(to).trigger('change');            
            });
            $('.graphview_suggest', obj).bind('change', function(event) {
                options.suggest = $('option:selected',this).attr('data-value');
            });

        }



        // ===============================================
        // ===============================================
        //
        // now set the options from the defaults and those provided
        // and create the plugin on the target element
        // and bind everything up for starting
        //
        // ===============================================
        // ===============================================
        $.fn.graphview.options = $.extend(defaults, options);
        var options = $.fn.graphview.options;
        options.defaultquery.size == undefined ? options.defaultquery.size = 10 : false;
        options.defaultquery.from == undefined ? options.defaultquery.from = 0 : false;

        var obj = undefined;
        return this.each(function() {
            obj = $(this);
            obj.append(options.uitemplate());
            options.uibindings();            
            options.searchonload ? options.executequery() : false;

        });

    };
    
    // define options here then they are written to above, then they become available externally
    $.fn.graphview.options = {};
    
})(jQuery);
