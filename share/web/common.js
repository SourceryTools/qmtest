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


// Add or change a property in a property control.
//
// 'select' -- The select input displaying the properties.
//
// 'contents' -- The hidden input that gets the encoded representation
// of the properties.
//
// 'name' -- The property name.
//
// 'value' -- The property value.
//
// If there already is a property named 'name', its value is replaced
// with 'value'.  Otherwise, a new property is added.
//
// See 'qm.web.make_properties_control'.

function property_add_or_change(select, contents, name, value)
{
  // No name?  Bail.
  if(name == "")
    return;

  var options = select.options;
  // Construct the property as it will appear in the select input.
  var option_text = name + " = " + value;
  // Construct the encoded representation of the property.
  value = escape(value);
  var option_value = name + "=" + value;

  // Look for a existing property named 'name'.  Scan over the contents
  // of the select input.
  for(var i = 0; i < options.length; ++i) {
    var option = options[i];
    // Split the property name out of its encoded value.
    var option_name = option.value.split("=")[0];
    // Does it match our name?
    if(option_name == name) {
      // Yes.  Replace the property value with ours.
      option.text = option_text;
      option.value = option_value;
      // Reencode the properties.
      update_from_select_list(select, contents);
      // Select the modified entry in the select input.
      options.selectedIndex = i;
      return;
    }
  }

  // Fell through; we didn't find a property matching 'name'.  So,
  // add a new property.
  options[options.length] = new Option(option_text, option_value);
  // Reencode the properties.
  update_from_select_list(select, contents);
  // Make the new property selected.
  options.selectedIndex = options.length - 1;
  return;
}


// Remove the selected property in a property control.
// 
// 'select' -- The select input displaying the properties.
//
// 'contents' -- The hidden input that gets the encoded representation
// of the properties.
//
// See 'qm.web.make_properties_control'.

function property_remove(select, contents)
{
  // Is a property selected?
  if(select.selectedIndex != -1) {
    // Yes; remove it.
    select.options[select.selectedIndex] = null;
    // Reencode the properties.
    update_from_select_list(select, contents);
  }
}


// Update the name and value inputs when a new property is selected.
//
// 'select' -- The select input displaying the properties.
//
// 'name_text' -- The text input that displays the property name.
//
// 'value_text' -- The text input that displays the property value.
//
// Sets the contents of 'name_text' and 'value_text' to the name and
// value, respectively, of the property selected in 'select'.
//
// See 'qm.web.make_properties_control'.

function property_update_selection(select, name_text, value_text)
{
  var index = select.selectedIndex;
  if(index == -1)
    // No property is selected.
    return;
  // Get the encoded property from the select input.
  var option_value = select[index].value;
  // Extract the property name and value.
  var separator = option_value.indexOf("=");
  var name = option_value.substring(0, separator);
  var value = option_value.substring(separator + 1, option_value.length);
  value = unescape(value);
  // Set the text inputs appropriately.
  name_text.value = name;
  value_text.value = value;
}

////////////////////////////////////////////////////////////////////////
// Local Variables:
// mode: java
// indent-tabs-mode: nil
// fill-column: 72
// End:
