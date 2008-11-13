//constants
var ELEMENT_NODE = 1;
var TEXT_NODE = 3;
var COLLECTION = 'COLLECTION';
var ICON = 'ICON';
var EXPAND = 'EXPAND';
var XML_CHILDREN_VIEW = '@@children.xml';
var SINGLE_BRANCH_TREE_VIEW = '@@singleBranchTree.xml';
var CONTENT_VIEW = '@@SelectedManagementView.html';
var NUM_TEMPLATE = '$${num}';


var LG_DEBUG = 6;
var LG_TRACE_EVENTS = 5;
var LG_TRACE = 4;
var LG_INFO = 3;
var LG_NOLOG = 0;


// globals
var loadingMsg = 'Loading...';
var abortMsg = 'Unavailable';
var titleTemplate = 'Contains ' + NUM_TEMPLATE + ' item(s)';
var baseurl;
var navigationTree;
var docNavTree;
var loglevel = LG_NOLOG;



//class navigationTreeNode
function navigationTreeNode (domNode) {
    this.childNodes = new Array();
    this.isEmpty = 1;
    this.isCollapsed = 1;
    this.domNode = domNode;
    this.loadingNode = null;
    this.path = '';
    this.parentNode = null;
}

navigationTreeNode.prototype.appendChild = function(node) {
    this.childNodes.push(node);
    this.domNode.appendChild(node.domNode);
    node.parentNode = this;
}

navigationTreeNode.prototype.setPath = function(path) {
    this.path = path;
    this.domNode.setAttribute("path", path);
}

navigationTreeNode.prototype.setSelected = function() {
    this.domNode.getElementsByTagName('icon')[0].className='selected';
}

navigationTreeNode.prototype.collapse = function() {
    this.isCollapsed = 1;
    this.changeExpandIcon("pl.gif");
}

navigationTreeNode.prototype.expand = function() {
    this.isCollapsed = 0;
    this.changeExpandIcon("mi.gif");
}

navigationTreeNode.prototype.changeExpandIcon = function(icon) {
    var expand = this.domNode.getElementsByTagName('expand')[0];
    expand.style.backgroundImage = 'url("' + baseurl + '@@/' + icon + '")';
}

navigationTreeNode.prototype.getNodeByPath = function(path) {
    var numchildren = this.childNodes.length;
    if (path == this.path) return this;
    else {
        for (var i=0; i<numchildren; i++) {
            foundChild = this.childNodes[i].getNodeByPath(path);
            if (foundChild) return foundChild;
        }
    }
    return null;
}

navigationTreeNode.prototype.toggleExpansion = function() {
    with (this) {
        prettydump('toggleExpansion', LG_TRACE);
        // If this collection is empty, load it from server
        // todo xxx optimize for the case where collection has null length
        if (isEmpty) startLoadingChildren();
        else refreshExpansion();
    }
}

navigationTreeNode.prototype.startLoadingChildren = function() {
    with (this) {
        //already loading?
        if (loadingNode) return;
        loadingNode = createLoadingNode();
        domNode.appendChild(loadingNode);
        //var url = baseurl + path + XML_CHILDREN_VIEW;
        var url = path + XML_CHILDREN_VIEW;
        loadtreexml(url, this);
    }
}

navigationTreeNode.prototype.finishLoadingChildren = function() {
    with (this) {
        isEmpty = 0;
        refreshExpansion();
        domNode.removeChild(loadingNode);
        loadingNode = null;
    }
}

navigationTreeNode.prototype.abortLoadingChildren = function() {
    with (this) {
        domNode.removeChild(loadingNode);
        loadingNode = null;
    }
}

navigationTreeNode.prototype.refreshExpansion = function() {
    with (this) {
        if (isCollapsed) {
            expand();
            showChildren();
        }
        else {
            collapse();
            hideChildren();
        }
    }
}


navigationTreeNode.prototype.hideChildren = function() {
    with (this) {
        prettydump('hideChildren', LG_TRACE);
        var num = childNodes.length;
        for (var i=num-1; i>=0; i--) {
            childNodes[i].domNode.style.display = 'none';
        }
    }
}

navigationTreeNode.prototype.showChildren = function() {
    with (this) {
        prettydump('showChildren', LG_TRACE);
        var num = childNodes.length;
        for (var i=num-1; i>=0; i--) {
            childNodes[i].domNode.style.display = 'block';
        }
    }
}

// utilities
function prettydump(s, locallog) {
    // Put the string "s" in a box on the screen as an log message
    if (locallog > loglevel) return;

    var logger = document.getElementById('logger');
    var msg = document.createElement('code');
    var br1 = document.createElement('br');
    var br2 = document.createElement('br');
    var msg_text = document.createTextNode(s);
    msg.appendChild(msg_text);
    logger.insertBefore(br1, logger.firstChild);
    logger.insertBefore(br2, logger.firstChild);
    logger.insertBefore(msg, logger.firstChild);
}


function debug(s) {
    var oldlevel = loglevel;
    loglevel = LG_DEBUG;
    prettydump("Debug : " + s, LG_DEBUG);
    loglevel = oldlevel;
}

// DOM utilities
function getTreeEventTarget(e) {
    var elem;
    if (e.target) {
        // Mozilla uses this
        if (e.target.nodeType == TEXT_NODE) {
            elem=e.target.parentNode;
        }
        else elem=e.target;
    } else {
        // IE uses this
        elem=e.srcElement;
    }
    return elem;
}

function isCollection(elem) {
    return checkTagName(elem, COLLECTION);
}


function isIcon(elem) {
    return checkTagName(elem, ICON);
}

function isExpand(elem) {
    return checkTagName(elem, EXPAND);
}

function checkTagName(elem, tagName) {
    return elem.tagName.toUpperCase() == tagName;
}

function getCollectionChildNodes(xmlDomElem) {
    // get collection element nodes among childNodes of elem
    var result = new Array();

    var items = xmlDomElem.childNodes;
    var numitems = items.length;
    var currentItem;
    for (var i=0; i<numitems; i++) {
        currentItem = items[i];

        if (currentItem.nodeType == ELEMENT_NODE && isCollection(currentItem)) {
            result.push(currentItem);
        }
    }
    return result;
}

//events
function treeclicked(e) {
    prettydump('treeclicked', LG_TRACE_EVENTS);
    var elem = getTreeEventTarget(e);
    if (elem.id == 'navtree') return;

    // if node clicked is expand elem, toggle expansion
    if (isExpand(elem) && !elem.getAttribute('disabled')) {
        //get collection node
        elem = elem.parentNode;
        var navTreeNode = navigationTree.getNodeByPath(elem.getAttribute('path'));
        navTreeNode.toggleExpansion();
    }
}

// helpers
function getControlPrefix() {
    if (getControlPrefix.prefix)
        return getControlPrefix.prefix;

    var prefixes = ["MSXML2", "Microsoft", "MSXML", "MSXML3"];
    var o, o2;
    for (var i=0; i<prefixes.length; i++) {
        try {
            // try to create the objects
            o = new ActiveXObject(prefixes[i] + ".XmlHttp");
            o2 = new ActiveXObject(prefixes[i] + ".XmlDom");
            return getControlPrefix.prefix = prefixes[i];
        }
        catch (ex) {};
    }

    throw new Error("Could not find an installed XML parser");
}


// XmlHttp factory
function XmlHttp() {}


XmlHttp.create = function() {
    if (window.XMLHttpRequest) {
        var req = new XMLHttpRequest();

        // some older versions of Moz did not support the readyState property
        // and the onreadystate event so we patch it!
        if (req.readyState == null) {
            req.readyState = 1;
            req.addEventListener("load", function() {
                req.readyState = 4;
                if (typeof req.onreadystatechange == "function")
                req.onreadystatechange();}, false);
        }

        return req;
    }
    if (window.ActiveXObject) {
        s = getControlPrefix() + '.XmlHttp';
        return new ActiveXObject(getControlPrefix() + ".XmlHttp");
    }
    return;
};

function loadtreexml (url, node) {
    var xmlHttp = XmlHttp.create();
    if (!xmlHttp) return;
    prettydump('URL ' + url, LG_INFO);
    xmlHttp.open('GET', url, true);

    xmlHttp.onreadystatechange = function() {
        if (xmlHttp.readyState != 4) return;
        prettydump('Response XML ' + xmlHttp.responseText, LG_INFO);
        parseXML(xmlHttp.responseXML, node);
    };

    // call in new thread to allow ui to update
    window.setTimeout(function() { xmlHttp.send(null); }, 10);
}

function loadtree (rooturl, thisbaseurl) {
    baseurl = rooturl;  // Global baseurl
    docNavTree = document.getElementById('navtreecontents');

    var url = thisbaseurl + SINGLE_BRANCH_TREE_VIEW;
    loadtreexml(url, null);
}


function removeChildren(node) {
    var items = node.childNodes;
    var numitems = items.length;
    for (var i=0; i<numitems; i++) {
        node.removeChild(items[i]);
    }
}


function parseXML(responseXML, node) {
    if (responseXML) {
        var data = responseXML.documentElement;
        if (node == null) {
            //[top] node
            removeChildren(docNavTree);
            titleTemplate = data.getAttribute('title_tpl');
            loadingMsg = data.getAttribute('loading_msg');
            addNavigationTreeNodes(data, null, 1);
        //      docNavTree.appendChild(navigationTree.domNode);
        } else {
            //expanding nodes
            addNavigationTreeNodes(data, node, 0);
            node.finishLoadingChildren();
        }
    } else {
        // no XML response, reset the loadingNode
        if (node == null) {
            //unable to retrieve [top] node
            docNavTree.innerHTML = abortMsg;
        } else {
            //abort expanding nodes
            node.abortLoadingChildren()
        }
    }
}

function addNavigationTreeNodes(sourceNode, targetNavTreeNode, deep) {
    // create tree nodes from XML children nodes of sourceNode
    // and add them to targetNode
    // if deep, create all descendants of sourceNode
    var basePath = "";
    if (targetNavTreeNode) basePath = targetNavTreeNode.path;
    var items = getCollectionChildNodes(sourceNode);
    var numitems = items.length;
    for (var i=0; i<numitems; i++) {
        var navTreeChild = createNavigationTreeNode(items[i], basePath, deep);
        if (targetNavTreeNode) targetNavTreeNode.appendChild(navTreeChild);
    }
}


function createPresentationNodes(title, targetUrl, icon_url, length) {
    // create nodes hierarchy for one collection (without children)

    // create elem for plus/minus icon
    var expandElem = document.createElement('expand');
    // create elem for item icon
    var iconElem = document.createElement('icon');
    expandElem.appendChild(iconElem);
    // Mozilla tries to infer an URL if url is empty and reloads containing page
    if (icon_url != '')  {
        iconElem.style.backgroundImage = 'url("' + icon_url + '")';
    }
    // create link
    var linkElem = document.createElement('a');
    var titleTextNode = document.createTextNode(title);

    linkElem.appendChild(titleTextNode);
    var titleText = titleTemplate.split(NUM_TEMPLATE).join(length);
    linkElem.setAttribute('title', titleText);
    linkElem.setAttribute('href', targetUrl);

    iconElem.appendChild(linkElem);

    return expandElem;
}

function createLoadingNode() {
    var loadingElem = document.createElement('loading');
    var titleTextNode = document.createTextNode(loadingMsg);

    loadingElem.appendChild(titleTextNode);

    return loadingElem;
}

function createNavigationTreeNode(source, basePath, deep) {
    var newelem = document.createElement(source.tagName);

    var navTreeNode = new navigationTreeNode(newelem);
    var elemPath;
    var elemTitle;
    if (source.getAttribute('isroot') != null) {
        elemTitle = source.getAttribute('name');
        //elemPath = basePath;
        // set base url for virtual host support
        baseurl = source.getAttribute('baseURL');
        elemPath = source.getAttribute('baseURL');
        newelem.style.marginLeft = '0px';
        navigationTree = navTreeNode;
        docNavTree.appendChild(newelem);
    } else {
        elemTitle = source.getAttribute('name');
        elemPath = basePath + elemTitle + '/';
    }
    navTreeNode.setPath(elemPath);

    //could show number of child items
    var length = source.getAttribute('length');

    var icon_url = source.getAttribute('icon_url');

    var targetUrl = elemPath + CONTENT_VIEW;

    var expandElem = createPresentationNodes(elemTitle, targetUrl, icon_url, length);
    newelem.appendChild(expandElem);

    // If no child element, we can disable the tree expansion
    if (length == '0') expandElem.setAttribute('disabled','1');

    // If this is the selected node, we want to highlight it with CSS
    if (source.firstChild && source.firstChild.nodeValue == 'selected')
        navTreeNode.setSelected();

    if (deep) {
        var children = getCollectionChildNodes(source);
        var numchildren = children.length;
        for (var i=0; i<numchildren; i++) {
            var navTreeNodeChild = createNavigationTreeNode(children[i], navTreeNode.path, deep);
            navTreeNode.appendChild(navTreeNodeChild);
        }
        if (numchildren) {
            navTreeNode.isEmpty = 0;
            navTreeNode.expand();
        } else {
            navTreeNode.isEmpty = 1;
            // if no child, we do not display icon '+'
            if (length != '0') navTreeNode.collapse();
        }
    } else {
        navTreeNode.isEmpty = 1;
        // if no child, we do not display icon '+'
        if (length != '0') navTreeNode.collapse();
    }
    return navTreeNode;
}
