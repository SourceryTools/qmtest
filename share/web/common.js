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

// Remove the select item from a set control.
//
// 'select' -- The select input displaying the elements in the set.
//
// 'contents' -- The hidden input that contains the encoded contents of
// the set. 

function remove_from_set(select, contents)
{
  // Is anything selected?
  if(select.selectedIndex != -1)
    // Yes.  Drop it from the options list.
    select.options[select.selectedIndex] = null;
  // Re-encode the set contents.
  contents.value = encode_select_options(select);
  return false;
}


// Add an element to a set control.
//
// 'select' -- The select input displaying the elements in the set.
//
// 'contents' -- The hidden input that contains the encoded contents of
// the set. 
//
// 'text' -- The user-visible text representing the element to add to
// the set. 
//
// 'value' -- The encoded value representing the element to add to the
// set. 
//
// The new element is not added if there is already another element in
// the set with the same encoded value.

function add_to_set(select, contents, text, value)
{
  var options = select.options;
  // Look for another option that has the same value.
  for(var i = 0; i < options.length; ++i)
    if(options[i].value == value)
      // Found a match; don't continue.
      return false;
  // Append a new option, if the value is not empty.
  if(value != "")
    options[options.length] = new Option(text, value);
  // Re-encode the set contents.
  contents.value = encode_select_options(select);
  return false;
}


// Move the selected element in a set control.
//
// 'select' -- The select input displaying the elements in the set.
//
// 'contents' -- The hidden input that contains the encoded contents of
// the set. 
//
// 'offset' -- The number of positions by which to move the selected
// element.  Negative values move the element towards the beginning of
// the set. 

function move_in_set(select, contents, offset)
{
  swap_option(select, offset);
  contents.value = encode_select_options(select);
}


// Encode the values of the options in a set control.
//
// 'select' -- The select input displaying the elements in the set.
//
// returns -- A string containing the value of the options of 'select',
// separated by commas.

function encode_select_options(select)
{
  // Construct the encoded value in this variable.
  var result = "";
  // Loop over options in the select list.
  for(var i = 0; i < select.options.length; ++i) {
    // Elements after the first are preceded by commas.
    if(i > 0)
      result += ",";
    // Append the next value.
    result += select.options[i].value;
  }
  return result;
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
  // If the state name isn't valid, complain and bail.
  if(!label_is_valid(name)) {
    popup_box("Error",
              "A property name can consist only of lower-case letters, " +
              "digits, and underscores, and cannot be empty.");
    return;
  }

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
      contents.value = encode_select_options(select);
      // Select the modified entry in the select input.
      options.selectedIndex = i;
      return;
    }
  }

  // Fell through; we didn't find a property matching 'name'.  So,
  // add a new property.
  options[options.length] = new Option(option_text, option_value);
  // Reencode the properties.
  contents.value = encode_select_options(select);
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
    // Re-encode the properties.
    contents.value = encode_select_options(select);
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


// Display a popup message box.
//
// 'title' -- The box title.
//
// 'message' -- The message to display in the box.
//
// The box includes a single "Close" button.

function popup_box(title, message)
{
  var popup = window.open("", "popup", "width=480,height=200");
  popup.document.open("text/html");
  popup.document.write("<html><head><title>" + title + "</title><body>\n"
                       + "<table border='0' width='100%' height='100%'>"
                       + "<tr><td align='center'><h3>" + title 
                       + "</h3></td></tr>"
                       + "<tr height='100%'><td align='center'>");
  popup.document.write(message);
  popup.document.write("</td></tr><tr><td align='right'><form>"
                       + "<input type='button' value=' Close ' "
                       + "onclick='window.close();' /></form>"
                       + "</tr></td></table></body></html>\n");
  popup.document.close();
}


// Return true if 'label' is a valid label.

function label_is_valid(label)
{
  return label.match(/^[a-z0-9][a-z0-9_]*$/) != null;
}


// Select an item in a select input by option value.
//
// 'select' -- The select input.
//
// 'value' -- The value of the option to be selected.
//
// Selects the first option whose value is 'value'.  If there is none,
// the selection is not changed.

function select_item(select, value) 
{
  var i;
  for(i = 0; i < select.options.length; ++i)
    if(select.options[i].value == value) {
      select.selectedIndex = i;
      return;
    }
}


// Return the value of the option selected in a select input.
//
// 'select' -- The select input.
//
// Returns 'null' if no item is selected.

function get_selected_value(select)
{
  if(select.selectedIndex == -1)
    return null;
  else
    return select.options[select.selectedIndex].value;
}


////////////////////////////////////////////////////////////////////////
// Local Variables:
// mode: java
// indent-tabs-mode: nil
// fill-column: 72
// End:
