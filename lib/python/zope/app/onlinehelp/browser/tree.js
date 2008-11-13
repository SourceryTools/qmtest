//----------------------------------------------------------------------------
// unordered list based tree
//----------------------------------------------------------------------------

var nodeCollapseClass = "collapse";
var nodeExpandClass = "expand";
var nodeItemClass = "item";
var nodeLinkClass = "link";
var activeNodeId = "activeTreeNode";

//----------------------------------------------------------------------------
// public API
//----------------------------------------------------------------------------
function buildTrees() {
    if (!document.createElement) {
        return;
    }
    uls = document.getElementsByTagName("ul");
    for (var i=0; i<uls.length; i++) {
        var ul = uls[i];
        if (ul.nodeName == "UL" && ul.className == "tree") {
            _renderTreeList(ul);
            _toggleTreeList(ul, nodeExpandClass, activeNodeId);
        }
    }
}

function expandTree(id) {
    var ul = document.getElementById(id);
    if (ul == null) {
        return false;
    }
    _toggleTreeList(ul, nodeExpandClass);
}

function collapseTree(id) {
    var ul = document.getElementById(id);
    if (ul == null) {
        return false;
    }
    _toggleTreeList(ul, nodeCollapseClass);
}

function expandItem(treeId, itemId) {
    var ul = document.getElementById(treeId);
    if (ul == null) {
        return false;
    }
    var togList = _toggleTreeList(ul, nodeExpandClass, itemId);
    if (togList) {
        var o = document.getElementById(itemId);
        if (o.scrollIntoView) {
            o.scrollIntoView(false);
        }
    }
}

function expandActiveItem(treeId) {
    expandItem(treeId, activeNodeId);
}

//----------------------------------------------------------------------------
// private methods
//----------------------------------------------------------------------------
function _toggleTreeList(ul, clsName, itemId) {
    if (!ul.childNodes || ul.childNodes.length==0) {
        return false;
    }
    for (var i=0; i<ul.childNodes.length; i++) {
        var item = ul.childNodes[i];
        if (itemId != null && item.id == itemId) { return true; }
        if (item.nodeName == "LI") {
            var subLists = false;
            for (var si=0; si<item.childNodes.length; si++) {
                var subitem = item.childNodes[si];
                if (subitem.nodeName == "UL") {
                    subLists = true;
                    var togList = _toggleTreeList(subitem, clsName, itemId);
                    if (itemId != null && togList) {
                        item.className = clsName;
                        return true;
                    }
                }
            }
            if (subLists && itemId == null) {
                item.className = clsName;
            }
        }
    }
}

function _renderTreeList(ul) {
    if (!ul.childNodes || ul.childNodes.length == 0) {
        return;
    }
    for (var i=0; i<ul.childNodes.length; i++) {
        var item = ul.childNodes[i];
        if (item.nodeName == "LI") {
            var subLists = false;
            for (var si=0; si<item.childNodes.length; si++) {
                var subitem = item.childNodes[si];
                if (subitem.nodeName == "UL") {
                    subLists = true;
                    _renderTreeList(subitem);
                }
            }
            var span = document.createElement("SPAN");
            var nbsp = '\u00A0'; // &nbsp;
            span.className = nodeLinkClass;
            if (subLists) {
                if (item.className == null || item.className == "") {
                    item.className = nodeCollapseClass;
                }
                if (item.firstChild.nodeName == "#text") {
                    nbsp = nbsp + item.firstChild.nodeValue;
                    item.removeChild(item.firstChild);
                }
                span.onclick = function () {
                    if (this.parentNode.className == nodeExpandClass) {
                        this.parentNode.className = nodeCollapseClass
                    }else {
                        this.parentNode.className = nodeExpandClass
                    }
                    return false;
                }
            }
            else {
                item.className = nodeItemClass;
                span.onclick = function () {
                    return false;
                }
            }
            child = document.createTextNode(nbsp)
            span.appendChild(child);
            item.insertBefore(span, item.firstChild);
        }
    }
}


