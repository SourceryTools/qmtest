########################################################################
#
# File:   summary.py
# Author: Alex Samuel
# Date:   2001-02-08
#
# Contents:
#   Web form to summarize issues in a table.
#
# Copyright (c) 2001 by CodeSourcery, LLC.  All rights reserved. 
#
# Permission is hereby granted, free of charge, to any person
# obtaining a copy of this software and associated documentation files
# (the "Software"), to deal in the Software without restriction,
# including without limitation the rights to use, copy, modify, merge,
# publish, distribute, sublicense, and/or sell copies of the Software,
# and to permit persons to whom the Software is furnished to do so,
# subject to the following conditions:
#
# The above copyright notice and this permission notice shall be
# included in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
# MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
# NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS
# BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN
# ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN
# CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
#
########################################################################

"""Web form to print a table of issues.

The form is generated from the DTML template summary.dtml, using
code in this module.

The form recognizes the following query arguments:

'sort' -- The name of the field by which to sort the issues, prefixed
with a hyphen for reverse sort.

'query' -- If specified, show the issues matching this query.
Otherwise, show all issues.

'last_query' -- If this argument is included, use the query expression
from the last query run by this user.  The argument value is ignored.

'open_only' -- Either 0 or 1, indicating whether only open issues should
be shown.  If omitted, the value 0 is impled."""

########################################################################
# imports
########################################################################

import colorsys
import qm.track.issue
import qm.web
import string
import sys
import web

########################################################################
# classes
########################################################################

class SummaryPage(web.DtmlPage):
    """Page summarizing multiple issues in a table, as for query results.

    The following attributes are available as DTML variables.

      'issues' -- A sequence of issues to display in the table."""

    def __init__(self,
                 issues,
                 field_names,
                 sort_order,
                 open_only=0,
                 hue_field_name=None,
                 lightness_field_name=None,
                 saturation_field_name=None):
        """Create a new page.

        'issues' -- A sequence of issues to summarize.

        'field_names' -- A comma-separated list of field names to
        display.

        'sort_order' -- The name of the field by which to sort entries.
        If prefixed with a minus sign, sort in reverse order.

        'open_only' -- If true, show only issues in an open state."""

        # Initialize the base class.
        web.DtmlPage.__init__(self,
                              "summary.dtml",
                              field_names=field_names,
                              open_only=open_only,
                              hue_field_name=hue_field_name,
                              lightness_field_name=lightness_field_name,
                              saturation_field_name=saturation_field_name)

        # If requested, limit the issues to open issues only.
        if open_only:
            issues = filter(lambda i: i.IsOpen(), issues)

        # Partition issues by issue class.  'self.issue_map' is a map
        # from issue class onto a sequence of issues.
        self.issue_map = {}
        for issue in issues:
            issue_class = issue.GetClass()
            if self.issue_map.has_key(issue_class):
                self.issue_map[issue_class].append(issue)
            else:
                self.issue_map[issue_class] = [ issue ]

        # Build a map of all fields in all issue classes we're showing.
        # If a field is present in more than one issue class, choose one
        # instance arbitrarily.  We need this because the summary can
        # contain issues from several different issue classes, each of
        # which have their own fields, yet some aspects of this page
        # (such as display options) are common to all fields.
        self.field_dictionary = {}
        for issue_class in self.issue_map.keys():
            for field in issue_class.GetFields():
                self.field_dictionary[field.GetName()] = field

        if sort_order[0] == "-":
            # If the first character of the sort order is a hyphen, that
            # indicates a reverse sort.
            reverse = 1
            # The rest is the field name.
            sort_field_name = sort_order[1:]
        else:
            # Otherwise, just a field name is given.
            reverse = 0
            sort_field_name = sort_order

        # Sort the issues in each class.
        for issue_class, issue_list in self.issue_map.items():
            sort_field = issue_class.GetField(sort_field_name)
            sort_predicate = \
                qm.track.issue.IssueSortPredicate(sort_field, reverse)
            issue_list.sort(sort_predicate)

        # Extract a list of issue classes we need to show.
        self.issue_classes = self.issue_map.keys()
        # Put them into dictionary order by title.
        sort_predicate = lambda cl1, cl2: \
                         cmp(cl1.GetTitle(), cl2.GetTitle())
        self.issue_classes.sort(sort_predicate)


    def MakeDisplayOptionsButton(self):
        """Construct the button that pops up the display options page."""

        # Generate the HTML page for the popup window for selecting
        # display options.
        display_options_page = DisplayOptionsPage(
            self.field_dictionary,
            self.field_names,
            self.open_only,
            str(self.hue_field_name),
            str(self.lightness_field_name),
            str(self.saturation_field_name))
        display_options_page = display_options_page(self.request)
        # Construct the Display Options button, which pops up a window
        # showing this page.
        return qm.web.make_button_for_popup(
            "Change Display Options...",
            display_options_page,
            request=self.request,
            window_width=640,
            window_height=480)


    def MakeColorKeyButton(self):
        """Construct the button that pops up the color key window."""

        if self.hue_field_name is None \
           and self.saturation_field_name is None \
           and self.lightness_field_name is None:
            return ""

        page = ColorKeyPage(
            self.field_dictionary.get(self.hue_field_name, None),
            self.field_dictionary.get(self.lightness_field_name, None),
            self.field_dictionary.get(self.saturation_field_name, None)
            )
        return qm.web.make_button_for_popup(
            "Color Key",
            page(self.request),
            request=self.request,
            window_width=480,
            window_height=480)


    def GetBackgroundColor(self, issue):
        """Return the color, in HTML syntax, for the row showing 'issue'."""

        hue, lightness, saturation = _hls_transform(
            _color_value_for_enum_field(issue, self.hue_field_name),
            _color_value_for_enum_field(issue, self.lightness_field_name),
            _color_value_for_enum_field(issue, self.saturation_field_name)
            )

        # Convert to HTML RGB syntax.
        rgb = colorsys.hls_to_rgb(hue, lightness, saturation)
        return apply(qm.web.format_color, rgb)


    def FormatFieldValue(self, issue, field_name):
        """Generate a rendering of a field value.

        'issue' -- The issue from which to obtain the value.

        'field_name' -- The name of the field whose value to render.

        returns -- The field value, formatted for HTML."""

        issue_class = issue.GetClass()
        try:
            field = issue_class.GetField(field_name)
        except KeyError:
            # This issue does not have a field by this name.  Skip it.
            return "&nbsp;"
        else:
            value = issue.GetField(field_name)
            return field.FormatValueAsHtml(value, style="brief")


    def MakeResortUrl(self, field_name):
        """Generate a URL for the same page, but sorted by 'field_name'."""

        # Take all the previous field values.
        new_request = self.request.copy()
        # If the previous key had a sort field, and this is the same
        # field, prepend a dash, which indicates reverse sort.
        if self.request.has_key("sort") \
           and self.request["sort"] == field_name:
            field_name = "-" + field_name
        # Add a sort specificaiton.
        new_request["sort"] = field_name
        # Generate the new URL.
        return new_request.AsUrl()



class DisplayOptionsPage(web.DtmlPage):
    """Popup page for setting summary display options.

    The following attributes are availablet as DTML variables.

      'field_controls' -- The HTML controls for selecting the fields to
      display.

      'base_url' -- The base URL to redisplay the issue summary."""

    def __init__(self,
                 field_dictionary,
                 included_field_names,
                 open_only,
                 hue_field_name,
                 lightness_field_name,
                 saturation_field_name):
        """Create a new page info context.

        'field_dictionary' -- A map from field names to 'Field'
        instances for fields in issue classes of issues in the summary.

        'included_field_names' -- A sequence of names of all fields
        currently included in the issue summary display.

        'open_only' -- True if only open issues are currently
        displayed."""

        # Initialize the base class.
        web.DtmlPage.__init__(self,
                              "summary-display-options.dtml",
                              hue_field_name=hue_field_name,
                              lightness_field_name=lightness_field_name,
                              saturation_field_name=saturation_field_name)

        # Find all names of non-hidden fields that aren't in
        # 'included_field_names'.
        excluded_field_names = []
        for field_name, field in field_dictionary.items():
            if not field.IsProperty("hidden") \
               and field_name not in included_field_names:
                excluded_field_names.append(field_name)

        # This function returns the title of the field whose name is
        # 'field_name'.  If it isn't a field we know about here, just
        # return the field name.
        def get_title(field_name, fields=field_dictionary):
            if fields.has_key(field_name):
                return fields[field_name].GetTitle()
            else:
                return field_name

        # Construct the controls for selecting fields to display.
        self.fields_controls = qm.web.make_choose_control(
            "fields",
            "Show Fields",
            included_field_names,
            "Don't Show Fields",
            excluded_field_names,
            item_to_text=get_title,
            ordered=1)

        self.open_only = open_only

        # Construct a list of names of open states in the state model
        # for these issue classes.
        try:
            state_field = field_dictionary["state"]
        except KeyError:
            # No state field, probably because there are no issues in
            # the summary.
            self.open_state_names = []
        else:
            state_model = state_field.GetStateModel()
            self.open_state_names = state_model.GetOpenStateNames()

        # Construct a list of names of fields that can be used for
        # coloring summary rows.
        self.colorable_fields = []
        for field in field_dictionary.values():
            if isinstance(field, qm.fields.EnumerationField):
                self.colorable_fields.append(field)


    def MakeBaseUrl(self):
        """Build the base URL for redisplaying the issue summary.

        The form will add fields to this URL to reflect the display
        options selected in the form."""

        redisplay_request = self.request.copy()
        # Blank out the fields that the form will add.
        for field_name in ["fields", "open_only", "hue", "saturation",
                           "lightness"]:
            if redisplay_request.has_key(field_name):
                del redisplay_request[field_name]
        return redisplay_request.AsUrl()


    def MakeColorableFieldSelect(self, name, default_field_name):
        """Build a select input for selecting a field for coloring.

        'name' -- The field name.

        'default_field_name' -- The name of the field which should be
        the default value in the select control.

        returns -- A select input displaying the titles of fields
        available for use as a color channel, plus 'None' for no
        field."""
        
        # We'll use an object of this class in place of a field, to
        # allow the user to choose no field for the color channel.  It
        # appears as 'None' in the select.
        class NoneField:
            def GetName(self):
                return "None"
            def GetTitle(self):
                return "None"
        # An instance of it.
        none_field = NoneField()

        if default_field_name == "None":
            # Default value is no field, so indicate our 'None'
            # placeholder. 
            default = none_field
        else:
            # Find the field matching this name.
            try:
                default = filter(lambda f, d=default_field_name:
                                 f.GetName() == d,
                                 self.colorable_fields) \
                                 [0]
            except IndexError:
                default = none_field

        # Construct the select control.  The elements are the fields
        # themselves.  The user-visible text for each option in the
        # select control is the field title, and the corresponding value
        # is the field name.
        return qm.web.make_select(
            name,
            [none_field] + self.colorable_fields,
            default,
            item_to_text=lambda f: f.GetTitle(),
            item_to_value=lambda f: f.GetName())



class ColorKeyPage(web.DtmlPage):
    """Popup page displaying the color key for the issue summary page."""

    def __init__(self,
                 hue_field,
                 lightness_field,
                 saturation_field):
        """Create a new page.

        'hue_field', 'lightness_field', 'saturation_field' -- Fields
        from which HLS channel values are taken.  These are enumeration
        fields.  Values may also be 'None', indicating no variation in
        this channel."""

        # Initialize the base class.
        web.DtmlPage.__init__(self, "summary-color-key.dtml")
        # This little class represents one item in a color chart,
        # composed of an HTML-formatted color value, and its label.
        class Color:
            def __init__(self, label, hls_color):
                self.label = label
                rgb = apply(colorsys.hls_to_rgb, hls_color)
                self.color = apply(qm.web.format_color, rgb)


        # Construct the color chart for hues, if hues are varied
        # according to an issue field.
        if hue_field is None:
            self.hues = None
        else:
            self.hues = []
            enumerals = hue_field.GetEnumerals()
            for enumeral in enumerals:
                color = _hls_transform(
                    hue=_color_value_for_enum(enumeral, enumerals))
                self.hues.append(Color(enumeral, color))
            self.hue_field_title = hue_field.GetTitle()
                
        # Construct the color chart for lightness values, if lightness
        # is varied according to an issue field.
        if lightness_field is None:
            self.lightnesses = None
        else:
            self.lightnesses = []
            enumerals = lightness_field.GetEnumerals()
            for enumeral in enumerals:
                color = _hls_transform(
                    lightness=_color_value_for_enum(enumeral, enumerals))
                self.lightnesses.append(Color(enumeral, color))
            self.lightness_field_title = lightness_field.GetTitle()
                
        # Construct the color chart for saturation values, if saturation
        # is varied according to an issue field.
        if saturation_field is None:
            self.saturations = None
        else:
            self.saturations = []
            enumerals = saturation_field.GetEnumerals()
            for enumeral in enumerals:
                color = _hls_transform(
                    saturation=_color_value_for_enum(enumeral, enumerals))
                self.saturations.append(Color(enumeral, color))
            self.saturation_field_title = saturation_field.GetTitle()
                
                

########################################################################
# functions
########################################################################

def handle_summary(request):
    """Generate the summary page.

    'request' -- A 'WebRequest' object."""

    session = request.GetSession()
    user = session.GetUser()
    idb = session.idb
    issue_store = idb.GetIssueStore()

    if request.has_key("last_query"):
        # Retrieve the last query performed by the user.
        query = user.GetConfigurationProperty("summary_last_query", "1")
    elif request.has_key("query"):
        # Use the query specified in the request.
        query = request["query"]
    else:
        query = "1"

    try:
        issues = []
        # Query all issue classes successively.
        for issue_class in idb.GetIssueClasses():
            issues = issues + issue_store.Query(query, issue_class.GetName())
    except qm.track.issue.ExpressionNameError, exception:
        msg = qm.error("query name error", name=str(exception), query=query)
        return qm.web.generate_error_page(request, msg)
    except qm.track.issue.ExpressionSyntaxError:
        msg = qm.error("query syntax error", query=query)
        return qm.web.generate_error_page(request, msg)

    # Store the query so the user can repeat it easily.
    user.SetConfigurationProperty("summary_last_query", query)

    # The request may specify the fields to display in the summary.  Are
    # they specified?
    if request.has_key("fields"):
        # Yes; use them.
        field_names = request["fields"]
        # Save them as the default for next time in the user record.
        user.SetConfigurationProperty("summary_fields", field_names)
    else:
        # No.  Retrieve the fields to show from the user record, or use
        # a default if they're not listed there.
        field_names = user.GetConfigurationProperty(
            "summary_fields", "iid,summary,state,categories")

    # The request may specify the sort order.  Is it specified?
    if request.has_key("sort"):
        # Yes; use it.
        sort_order = request["sort"]
        # Save it for next time.
        user.SetConfigurationProperty("summary_sort", sort_order)
    else:
        # No.  Retrieve the sort order from the user record, or use a
        # default if it's not listed there.
        sort_order = user.GetConfigurationProperty("summary_sort", "iid")

    # The request may specify that only open issues are to be
    # displayed.  Is the flag specified?
    if request.has_key("open_only"):
        # Yes; use it.
        open_only = int(request["open_only"])
        # Save it for next time.
        user.SetConfigurationProperty("summary_open_only", str(open_only))
    else:
        # No.  Retrieve the state from the user record, or use a default
        # if it's not listed there.
        open_only = int(
            user.GetConfigurationProperty("summary_open_only", 0))

    # Extract the name of the field from which the hue channel is
    # derived.  
    if request.has_key("hue"):
        hue_field = request["hue"]
        user.SetConfigurationProperty("summary_hue_field", hue_field)
    else:
        hue_field = user.GetConfigurationProperty("summary_hue_field", "None")
    # 'None' indicates no variation in background color hue.
    if hue_field == "None":
        hue_field = None

    # Extract the name of the field from which the lightness channel is
    # derived.  
    if request.has_key("lightness"):
        lightness_field = request["lightness"]
        user.SetConfigurationProperty("summary_lightness_field",
                                      lightness_field)
    else:
        lightness_field = user.GetConfigurationProperty(
            "summary_lightness_field", "None")
    # 'None' indicates no variation in background color lightness.
    if lightness_field == "None":
        lightness_field = None

    # Extract the name of the field from which the saturation channel is
    # derived.  
    if request.has_key("saturation"):
        saturation_field = request["saturation"]
        user.SetConfigurationProperty("summary_saturation_field",
                                      saturation_field)
    else:
        saturation_field = user.GetConfigurationProperty(
            "summary_saturation_field", "None")
    # 'None' indicates no variation in background color saturation.
    if saturation_field == "None":
        saturation_field = None

    # Split field names into a sequence.
    field_names = string.split(field_names, ",")
    # Make sure the IID field is in there somewhere.
    if not "iid" in field_names:
        field_names.insert(0, "iid")

    page = SummaryPage(issues, field_names, sort_order, open_only,
                       hue_field, lightness_field, saturation_field)
    return page(request)


def _color_value_for_enum_field(issue, field_name):
    """Extract a color channel value for the value of a field.

    'issue' -- The issue from which to extract a field value.

    'field_name' -- The name of the enumeration field to use.

    returns -- A single color channel value, between 0.0 and 1.0,
    representing the value of this field, or 'None' if 'field_name' is
    'None'."""

    if field_name is None:
        return None

    issue_class = issue.GetClass()
    field = issue_class.GetField(field_name)
    value = issue.GetField(field_name)

    # We determine the color channel value differently for different
    # types of fields.
    if isinstance(field, qm.fields.EnumerationField):
        return _color_value_for_enum(value, field.GetEnumerals())
    else:
        return 0.5


def _color_value_for_enum(value, enumerals):
    """Return the color channel value for an enumeral.

    'value' -- The enumeral value for which to generate the channel
    value.

    'enumerals' -- The full list of enumerals."""
    
    # Divide the range [0, 1] into even steps for the enumerals.
    if len(enumerals) < 2:
        return 0.5
    else:
        return enumerals.index(value) / (len(enumerals) - 1.0)


def _hls_transform(hue=None, lightness=None, saturation=None):
    """Transform HLS color values for an issue.

    The input channel values each range, in general, between 0 and 1.
    The output values are transformed from the input values to provide
    pleasing color output.

    'hue', 'lightness', 'saturation' -- HLS channel values.  A default
    value is used for each that is 'None'.

    returns -- A transformed '(hue, lightness, saturation)' triplet."""

    if hue is None:
        hue = 0.5
    # The values 0 and 1 correspond to the same hue, so shrink the range
    # somewhat.
    hue = 0.80 * hue

    if lightness is None:
        lightness = 0.2
    # Shift the lightness to keep the background colors light, and flip
    # sign so higher values correspond to darker colors.
    lightness = 0.85 - lightness * 0.25

    if saturation is None:
        saturation = 0.0
    # Shift the saturation range into lower values, to avoid garish
    # colors in the summary.
    saturation = 0.25 + saturation * 0.75

    return (hue, lightness, saturation)


########################################################################
# Local Variables:
# mode: python
# indent-tabs-mode: nil
# End:
