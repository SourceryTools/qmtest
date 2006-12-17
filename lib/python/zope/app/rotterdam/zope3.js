//----------------------------------------------------------------------------
// Copyright (c) 2005 Zope Corporation and Contributors.
// All Rights Reserved.
//
// This software is subject to the provisions of the Zope Public License,
// Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
// THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
// WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
// WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
// FOR A PARTICULAR PURPOSE.
//----------------------------------------------------------------------------

//----------------------------------------------------------------------------
// popup window with settings 
//----------------------------------------------------------------------------
function popup(page, name, settings) {
  win = window.open(page, name, settings);
  win.focus();
}

//----------------------------------------------------------------------------
// guess browser version, feel free to enhance it if needed.
//----------------------------------------------------------------------------
var ie = document.all != null;
var moz = !ie && document.getElementById != null && document.layers == null;

//----------------------------------------------------------------------------
// change the status (color) of the matrix table used in grant.html
//----------------------------------------------------------------------------
function changeMatrix(e) {
  var ele = e? e: window.event;
  var id = ele.getAttribute('id');
  var name = ele.getAttribute('name');
  if (moz) {
    var label = ele.parentNode;
    var center = label.parentNode;
    var td = center.parentNode;
  }
  else {
    var label = ele.parentElement;
    var center = label.parentElement;
    var td = center.parentElement;
  }
  resetMatrixCSS(name);
  if (td.className != "default") {
    td.className = "changed";
  }
}

function resetMatrixCSS(name) {
  var inputFields = document.getElementsByTagName('input');
  for (var i = 0; i < inputFields.length; i++) {
    var field = inputFields[i];
    if (field.getAttribute('name') == name) {
      if (moz) {
        td = field.parentNode.parentNode.parentNode;
      }
      else {
        td = field.parentElement.parentElement.parentElement;
      }
      if (td.className != "default") {
        td.className = "";
      }
    }
  }
}
