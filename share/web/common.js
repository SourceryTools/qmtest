////////////////////////////////////////////////////////////////////////
//
// File:   common.js
// Author: Alex Samuel
// Date:   2001-06-09
//
// Contents:
//   Common JavaScript functions for web pages.
//
// Copyright (c) 2001 by CodeSourcery, LLC.  All rights reserved. 
//
// Permission is hereby granted, free of charge, to any person
// obtaining a copy of this software and associated documentation files
// (the "Software"), to deal in the Software without restriction,
// including without limitation the rights to use, copy, modify, merge,
// publish, distribute, sublicense, and/or sell copies of the Software,
// and to permit persons to whom the Software is furnished to do so,
// subject to the following conditions:
//
// The above copyright notice and this permission notice shall be
// included in all copies or substantial portions of the Software.
//
// THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
// EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
// MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
// NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS
// BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN
// ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN
// CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
// SOFTWARE.
//
////////////////////////////////////////////////////////////////////////

function remove_from_set(select, contents)
{
  if(select.selectedIndex != -1)
    select.options[select.selectedIndex] = null;
  update_from_select_list(select, contents);
  return false;
}

function add_to_set(select, contents, text, value)
{
  var options = select.options;
  for(var i = 0; i < options.length; ++i)
    if(options[i].value == value)
      return false;
  if(value != "")
    options[options.length] = new Option(text, value);
  update_from_select_list(select, contents);
  return false;
}

function update_from_select_list(select, contents)
{
  var result = "";
  for(var i = 0; i < select.options.length; ++i) {
    if(i > 0)
      result += ",";
    result += select.options[i].value;
  }
  contents.value = result;
}

function update_from_select(select, control)
{
  if(select.selectedIndex != -1)
    control.value = select.options[select.selectedIndex].value;
}

var help_window = null;
function show_help(help_page)
{
  if(help_window != null && !help_window.closed)
    help_window.close();
  help_window = window.open("", "help",
			    "resizeable,toolbar,scrollbars");
  help_window.document.open("text/html", "replace");
  help_window.document.write(help_page);
  help_window.document.close();
}

var debug_window = null;
function debug(msg)
{
  if(debug_window == null || debug_window.closed) {
    debug_window = window.open("", "debug", "resizable");
    debug_window.document.open("text/plain", "replace");
  }
  debug_window.document.writeln(msg);
}

function move_option(src, dst)
{
  if(src.selectedIndex == -1)
    return;
  var option = src[src.selectedIndex];
  dst[dst.length] = new Option(option.text, option.value);
  src[src.selectedIndex] = null;
}

function swap_option(select, offset)
{
  var index = select.selectedIndex;
  if(index == -1)
    return;
  var new_index = index + offset;
  if(new_index < 0 || new_index >= select.length)
    return;

  var text = select[index].text;
  var value = select[index].value;
  select[index].text = select[new_index].text;
  select[index].value = select[new_index].value;
  select[new_index].text = text;
  select[new_index].value = value;

  select.selectedIndex = new_index;
}

function popup_manual()
{
  window.open("/manual/index.html", "manual",
	      "resizeable,toolbar,scrollbars");
}
