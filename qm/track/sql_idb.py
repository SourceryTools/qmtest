########################################################################
#
# File:   sql_idb.py
# Author: Alex Samuel
# Date:   2000-12-21
#
# Contents:
#   Generic SQL implementation of the IDB.
#
# Copyright (c) 2000 by CodeSourcery, LLC.  All rights reserved. 
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

"""
SQL-based implementation of the issue database.

 * Each issue class is represented by a table.  The table name is the
   same as the issue class name.

 * Fields in an issue class are represented by (usually a single)
   column.

    -- Integer fields are represented by INTEGER columns.

    -- Text fields are represented by VARCHAR columns.

    -- Attachment fields are represented by three columns, each
       VARCHAR, containing the attachment location, MIME type, and
       description respectively.  

    -- A set field is represented by an auxiliary table.  The table
       contains three columns: an issue id, a revision number, and a
       field value.  For a particular issue revision, each element of
       the set field is represented by a row in the auxiliary table.
       The row includes the issue's iid and revision number, and the
       column(s) containing the actual element value.
            
   Except for attachment fields, the column name is the same as the
   field name.  For an attachment field named "foo", the column names
   are "_atl_foo", "_att_foo", and "_atd_foo", respectively.
"""

########################################################################
# imports
########################################################################

from   issue import *
from   issue_class import *
import qm.track
import string

########################################################################
# classes
########################################################################

class SqlIdb(qm.track.IdbBase):
    """Generic SQL IDB implementation.

    An instance of this class represents a connections to an IDB.  Any
    one-time database creation and setup are performed elsewhere.

    This class is intended as a base class for IDB implementations
    that use an SQL-based RDBMS for issue storage.  Methods of this
    class assume that the underlying DB adheres to the Python Database
    API.

    The following members are assumed.  They must be initialized by
    concrete subclasses of this class.
    
       'issue_classes' -- A mapping from string issue class names to
       'IssueClass' instances.
    
    """
    

    def __init__(self):
        # Perform base class initialization.
        qm.track.IdbBase.__init__(self)


    def GetIssueClass(self, name):
        """Return the issue class named by 'name'."""

        return self.issue_classes[name]


    def AddIssueClass(self, issue_class):
        """Add 'issue_class' to the IDB.

        raises -- 'RuntimeError' if there is already a class in the
        IDB with the same name as the name of 'issue_class'."""

        # Make sure the issue class name is unique.
        name = issue_class.GetName()
        if self.issue_classes.has_key(name):
            raise RuntimeError, "duplicate issue class name %s" % name

        # The issue class is used as the table name.
        table_name = self.__GetTableName(issue_class)

        # Create the specification of the column types.
        fields = self.__GetFieldsOfIssueClass(issue_class)
        field_specs = []
        for field in fields:
            if isinstance(field, IssueFieldSet):
                self.__MakeTableForSetField(issue_class, field)
            else:
                spec = self.__ColumnSpecForField(issue_class, field)
                field_specs.append(spec)

        # Construct an SQL statement to create the table.
        sql_statement = "CREATE TABLE %s (%s)" \
                        % (table_name, string.join(field_specs, ", "))
        # Create the table.
        self.GetCursor().execute(sql_statement)
        # Record the issue class.
        self.issue_classes[name] = issue_class


    def AddIssue(self, issue):
        """Add a new issue record to the database.

        'issue' -- The new issue.  The revision number is ignored and
        set to zero.

        returns -- A true value if the addition succeeded.

        precondition -- The issue class of 'issue' must occur in this
        IDB, and fields of 'issue' must match the class's."""

        issue_class = issue.GetClass()
        # Set the revision number to zero.
        issue.SetField("revision", 0)
        # Make sure the issue's class is in this IDB.
        if not self.__HasIssueClass(issue_class):
            raise ValueError, "new issue in a class not in this IDB"
        # FIXME: Check iid uniqueness.
        # Insert the first revision.
        return self.__InsertIssue(issue_class, issue)


    def AddRevision(self, issue):
        """Add a revision of an existing issue to the database.

        returns -- A true value if the addition succeeded.

        'issue' -- A new revision of an existing issue.  The revision
        number is ignored and replaced with the next consecutive one
        for the issue."""

        issue_class = issue.GetClass()
        # Find the current revision, and assign the next revision
        # number to 'issue'.
        current = self.GetIssue(issue.GetId(), issue_class=issue_class)
        next_revision_number = current.GetRevision() + 1
        issue.SetField("revision", next_revision_number)
        # Insert the revision.
        return self.__InsertIssue(issue_class, issue, current)


    def GetIssueClasses(self):
        """Return a sequence of issue classes in this IDB."""

        return self.issue_classes.values()


    def GetIssue(self, iid, revision=None, issue_class=None):
        """Return the current revision of issue 'iid'.

        'revision' -- The revision number to retrieve.  If 'None', the
        current revision is returned.

        'issue_class' -- If 'None', all issue classes are searched for
        'iid'.  If an issue class name or 'IssueClass' instance are
        given, only that issue class is used.

        returns -- An 'Issue' instance.

        raises -- 'KeyError' if an issue with 'iid' cannot be found."""

        if issue_class == None:
            # Search all issue classes.
            classes_to_search = self.issue_classes.values()
        elif isinstance(issue_class, IssueClass):
            # Make sure the IssueClass instance belongs to this IDB.
            if not self.__HasIssueClass(issue_class):
                raise ValueError, "invalid issue class %s" % issue_class_name
            classes_to_search = [issue_class]
        else:
            # Assume it's an issue class name, and look it up.
            classes_to_search = [self.GetIssueClass(issue_class)]

        # Write the WHERE clause for the SELECT statement.
        where_clause = "iid = %s" % make_sql_string_literal(iid)
        # If a specific revision number was provided, add that to the
        # WHERE clause.
        if revision != None:
            where_clause = where_clause + " AND revision = %d" % revision

        # Query each class for a matching SELECT.
        results = []
        for icl in classes_to_search:
            results = self.__SelectRows(icl, where_clause)
            # Found it?  Stop searching.
            if len(results) > 0:
                # We'll need to know later the issue class in which
                # the revision was found.
                found_in_issue_class = icl
                break

        if len(results) == 0:
            # The issue was not found.
            if revision == None:
                raise KeyError, "no issue with IID '%s' found" % iid
            else:
                raise KeyError, "no revision %d of issue IID '%s' found" \
                      % (iid, revision)

        if revision == None:
            # The current revision was requested; find it.  All
            # revisions of the issue are (hopefully) in this result.
            result = results[0]
            for row in results[1:]:
                # The revision number is the second element of each
                # row.  Keep the row with the highest value.
                if row[1] > result[1]:
                    result = row
        else:
            # There should only be one matching revision.
            assert len(results) == 1
            result = results[0]

        # Found it; construct the issue.
        issue = self.__BuildIssueFromRow(found_in_issue_class, result)
        # Invoke get triggers.
        trigger_result, outcomes = self._IdbBase__InvokeGetTriggers(issue)
        # Check the trigger result.
        if not trigger_result:
            # The trigger vetoed the retrieval, so behave as if the
            # issue was nout found.
            raise KeyError, "no revision with IID '%s' found" % iid
        # FIXME: Do something with outcomes.
        # All done.
        return issue


    def GetAllRevisions(self, iid, issue_class=None):
        """Return a sequence of all revisions of an issue.

        'iid' -- The issue of which to retrieve all revisions.

        'issue_class' -- The issue class to search for this issue.  If
        'None', all issue classes are checked.

        returns -- A sequence of 'IssueRecord' objects, all
        corresponding to 'iid', indexed by revision number."""

        if issue_class == None:
            # Search all issue classes.
            classes_to_search = self.issue_classes.values()
        elif isinstance(issue_class, IssueClass):
            # Make sure the IssueClass instance belongs to this IDB.
            if not self.__HasIssueClass(issue_class):
                raise ValueError, "invalid issue class %s" % issue_class_name
            classes_to_search = [issue_class]
        else:
            # Assume it's an issue class name, and look it up.
            classes_to_search = [self.GetIssueClass(issue_class)]

        # Write the WHERE clause for the SELECT statement.
        where_clause = "iid = %s" % make_sql_string_literal(iid)
        
        rows = None
        for icl in classes_to_search:
            rows = self.__SelectRows(icl, where_clause)
            # Found it?  Stop searching.
            if len(rows) > 0:
                # We'll need to know later the issue class in which
                # the revision was found.
                found_in_issue_class = icl
                # Hopefully, all revisions of the issue are in the
                # same issue class, so stop searching.
                break

        if rows == None:
            # The issue was not found.
            raise KeyError, "no issue with IID '%s' found" % iid

        # Found it; convert rows into issues.
        issues = []
        for row in rows:
            issue = self.__BuildIssueFromRow(found_in_issue_class, row)
            # Invoke get triggers.
            trigger_result, outcomes = self._IdbBase__InvokeGetTriggers(issue)
            # Keep the issue only if the trigger passed it.
            if trigger_result:
                issues.append(issue)
            # FIXME: Do something with outcomes.
        return issues


    def GetCurrentRevisionNumber(self, iid):
        """Return the current revision number for issue 'iid'."""

        return self.GetIssue(iid).GetRevision()


    def Query(self, query_record, current_revision_only=1):
        """Return a sequence of issues matching 'query_record'.

        'query_record' -- An instance of IssueRecord specifying the query.

        'current_revision_only -- If true, don't match revisions other
        than the current revision of each issue."""

        raise NotImplementedError


    # Helper functions.

    def __ColumnSpecForField(self, issue_class, field):
        """Return a column specification for storing 'field'.

        'field' -- The field for which the column spec is returned.
        May not be a set field.

        returns -- A string representing the SQL specification of the
        column (or columns) used to represent 'field'."""

        name = field.GetName()
        # Select column type based on the field type.
        if isinstance(field, IssueFieldInteger):
            return "%s INTEGER" % name

        elif isinstance(field, IssueFieldText):
            return "%s VARCHAR" % name

        elif isinstance(field, IssueFieldSet):
            raise RuntimeError, 'field may not be a set field'

        elif isinstance(field, IssueFieldAttachment):
            # For an attachment field, 'col_name' is a triplet of
            # three names of columns that are used to implement
            # the field.   All three should be VARCHARs.
            return "_atl_%s VARCHAR, _att_%s VARCHAR, _atd_%s VARCHAR" \
                   % (3 * (name, ))

        else:
            raise RuntimeError, "unrecognized field type"
        

    def __MakeTableForSetField(self, issue_class, field):
        """Create an auxiliary table for set field 'field'."""

        assert isinstance(field, IssueFieldSet)

        # Build the name of the table.
        table_name = self.__GetTableNameForSetField(issue_class, field)
        # Extract the field type of the elements of the set.
        contained = field.GetContainedField()
        # Set fields may not be nested.
        if __debug__ and isinstance(contained, IssueFieldSet):
            raise RuntimeError, \
                  "a set field may not contain a set field"
        # Build the column specification of the value column.
        value_column = self.__ColumnSpecForField(issue_class, contained)
        # Construct the SQL statement to create the table.
        sql_statement = "CREATE TABLE %s " \
                        "(iid VARCHAR, revision INTEGER, %s)" \
                        % (table_name, value_column)
        # Do it.
        self.GetCursor().execute(sql_statement)
        

    def __InsertIssue(self, issue_class, issue, previous_issue=None):
        """Insert 'issue' into 'issue_class'.

        Invokes preupdate and postupdate triggers.

        'issue_class' -- The class into which to insert the issue.

        'issue' -- The 'Issue' instance to insert.

        'previous_issue' -- If this is not the first revision of a new
        issue, the previous current revision of the same issue.

        returns -- A true value if the insert succeeded, or a false
        value if it was vetoed by a trigger."""

        # Invoke preupdate triggers.
        result, outcomes = \
                self._IdbBase__InvokePreupdateTriggers(issue, previous_issue)
        # FIXME: Do something with outcomes.
        # Did a trigger veto the update?
        if not result:
            # Yes; bail.
            return 0

        # The name of the table containing this class.
        table_name = self.__GetTableName(issue_class)
        # The names of columns in the table.
        col_names = self.__GetColumnNames(issue_class)
        # Build an array of values that will be inserted into each
        # column.
        col_values = self.__BuildSqlForFields(issue)
        # Construct an SQL statement to insert the record.
        sql_statement = "INSERT INTO %s (%s) VALUES (%s)" \
                        % (table_name, col_names, col_values)
        # Insert the row.
        cursor = self.GetCursor()
        cursor.execute(sql_statement)
        # Save the cursor and use it below, so that everything gets
        # committed together.

        # For each set in the issue, insert rows into auxiliary tables
        # corresponding to list elements. 
        for field in self.__GetFieldsOfIssueClass(issue_class):
            if isinstance(field, IssueFieldSet):
                self.__AddSetFieldContents(cursor, field, issue)
        # Delete the cursor to commit the results.
        del cursor

        # Invoke postupdate triggers.
        outcomes = self._IdbBase__InvokePostupdateTriggers(issue,
                                                           previous_issue)
        # FIXME: Do something with outcomes.
        return 1


    def __SelectRows(self, issue_class, where_clause):
        """Issue an SQL SELECT statement and return the resulting rows.

        'issue_class' -- The issue class to query.

        'where_clause' -- The WHERE clause of the SELECT statement.

        'revision' -- The revision number to request for each issue.
        If negative, the highest revision number is returned.  If
        'None', all revisions are returned.

        returns -- A sequence of tuples representing table rows that
        satisfy 'where_clause'."""

        # Construct an SQL SELECT statement.
        table_name = self.__GetTableName(issue_class)
        col_names = self.__GetColumnNames(issue_class)
        sql_statement = "SELECT %s FROM %s WHERE %s" \
                        % (col_names, table_name, where_clause)
        # Run the query.
        cursor = self.GetCursor()
        cursor.execute(sql_statement)
        return cursor.fetchall()


    def __HasIssueClass(self, issue_class):
        """Return true if 'issue' is an issue class in this IDB."""

        name = issue_class.GetName()
        return self.issue_classes.has_key(name) \
               and self.issue_classes[name] == issue_class


    def __GetTableName(self, issue_class):
        """Return the name of the main table for 'issue_class'."""

        return issue_class.GetName()


    def __GetColumnName(self, field):
        """Return the name of the column containing 'field'."""

        name = field.GetName()
        if isinstance(field, IssueFieldAttachment):
            # Attachment fields are implemented by three columns.
            # Return a triplet of the column names.  Use reserved
            # labels to avoid conflicts with user field names.
            return "_atl_%s, _att_%s, _atd_%s" % (3 * (name, ))
        elif isinstance(field, IssueFieldSet):
            return None
        else:
            return name


    def __GetTableNameForSetField(self, issue_class, field):
        """Return the name of the auxiliary table for set 'field'."""

        assert isinstance(field, IssueFieldSet)
        return "_set_%s_%s" % (issue_class.GetName(), field.GetName())
        

    def __GetFieldsOfIssueClass(self, issue_class):
        """Return a list of fields in this issue.

        Unlike 'issue_class.GetFields(), this returns a known and
        stable order for fields in the issue class.  The issue id and
        revision are always the first two fields, in that order."""

        # Put the iid and revision up front.
        fields = [
            issue_class.GetField("iid"),
            issue_class.GetField("revision")
            ]
        # Everything else follows.  Don't care about their order.
        for field in issue_class.GetFields():
            name = field.GetName()
            if name != "iid" and name != "revision":
                fields.append(field)
        return fields


    def __GetColumnNames(self, issue_class):
        """Return the column names for fields of 'issue_class'.

        The iid and revision columns are gauranteed to the first two,
        in that order.  For fields that are represented by more than
        one column, all columns are included, sequentially.

        returns -- A sequence of column names, in the order that
        fields appear in 'issue_class'."""

        # Start with the iid and revision.
        col_names = []
        # Iterate over fields.
        for field in self.__GetFieldsOfIssueClass(issue_class):
            # The name of the column.
            col_name = self.__GetColumnName(field)
            if col_name != None:
                col_names.append(col_name)
        # Join the column names into a list.
        result = string.join(col_names, ", ")
        return result


    def __BuildIssueFromRow(self, issue_class, row):
        """Build an 'Issue' instance from a table row.

        Also queries auxiliary tables to set the contents of set
        fields. 

        'issue_class' -- The issue class of which this row represents
        an issue.

        'row' -- A tuple representing this row.  The tuple contains
        column values corresponding columns as returned by
        '__GetColumnNames'."""

        # The iid and revision number are the first and second
        # elements in the row, respectively.
        iid = row[0]
        revision = row[1]
        # Construct a mapping from field names to field values
        # extracted from this row.  As we go, pop colums off the front
        # of the row tuple.
        field_values = {}
        for field in self.__GetFieldsOfIssueClass(issue_class):
            name = field.GetName()
            if isinstance(field, IssueFieldSet):
                value = self.__GetSetFieldContents(issue_class, field,
                                                 iid, revision)
            else:
                row, value = self.__GetFieldFromRow(row, issue_class, field)
            # Insert the field value.
            field_values[name] = value
        # There should be nothing left in the row.
        assert len(row) == 0
        
        # Build the 'Issue'.
        new_issue = apply(Issue, (issue_class, ), field_values)
        return new_issue


    def __BuildSqlForFields(self, issue):
        """Construct SQL for column values for fields of 'issue'.

        The order of the fields is as returned by 'GetColumnNames()'.

        returns -- A string representing values of fields of
        'issue'."""

        issue_class = issue.GetClass()
        # Put the issue id and revision up front.
        col_values = []
        for field in self.__GetFieldsOfIssueClass(issue_class):
            # Get the field value.
            value = issue.GetField(field.GetName())
            # Represent it in SQL.
            sql_value = self.__BuildSqlForFieldValue(field, value)
            if sql_value != None:
                col_values.append(sql_value)
        # Join all the values into a list.
        return string.join(col_values, ", ")


    def __BuildSqlForFieldValue(self, field, value):
        """Return SQL representing the vale of 'field' in 'issue'.

        returns -- A string containing the SQL representation, or
        'None' if none is required."""

        if isinstance(field, IssueFieldInteger):
            # Convert the integer to a string.
            return str(value)
        elif isinstance(field, IssueFieldText):
            # Express the text as an SQL string literal.
            return make_sql_string_literal(value)
        elif isinstance(field, IssueFieldSet):
            # Set fields are implemented with auxiliary tables.
            # They require no columns in the main table.
            return None
        elif isinstance(field, IssueFieldAttachment):
            # An attachment is represented by three columns.
            if value == None:
                # For no attachment, use three empty strings.
                return "'', '', ''"
            else:
                cols = (
                    value.GetLocation(),
                    value.GetMimeType(),
                    value.GetDescription()
                    )
                cols = map(make_sql_string_literal, cols)
                return string.join(cols, ", ")
        else:
            raise RuntimeError, "unrecognized field type"


    def __GetFieldFromRow(self, row, issue_class, field):
        """Extract value of 'field' from the front of 'row'.

        The right way to use this function is:

          row, value = self.__GetFieldFromRow(row, ...

        'row' -- A tuple of elements returned from an SQL query.  The
        frontmost elements of the tuple are used to extract the field
        value.

        'field' -- The field whose value is extracted.  It may not be
        a set field; se '__GetSetFieldContents()' instead for these.

        returns -- A pair ('new_row', 'value'), where 'new_row' is
        'row' with elements removed from the front that were used to
        find the field value, and 'value' is the field value."""
        
        if isinstance(field, IssueFieldInteger):
            value = int(row[0])
            new_row = row[1:]

        elif isinstance(field, IssueFieldText):
            value = str(row[0])
            new_row = row[1:]

        elif isinstance(field, IssueFieldSet):
            raise ValueError, 'field may not be a set field'

        elif isinstance(field, IssueFieldAttachment):
            # The next three columns contain information about the
            # attachment. 
            location, value, mime_type = row[:3]
            # Advance past all three columns.
            new_row = row[3:]
            if location == "":
                # A null location field indicates no attachment.
                value = None
            else:
                value = Attachment(location, value, mime_type)

        else:
            raise RuntimeError, "unrecognized field type"

        return new_row, value


    def __GetSetFieldContents(self, issue_class, field, iid, revision):
        """Return the contents of 'field' for the specified issue.

        'issue_class' -- The class containing the issue.

        'field' -- The set field of which the contents are returned."""

        assert isinstance(field, IssueFieldSet)

        # The name of the auxiliary table containing set contents.
        table_name = self.__GetTableNameForSetField(issue_class, field)
        # The name of the column containing actual element values.
        contained = field.GetContainedField()
        col_name = self.__GetColumnName(contained)
        # Build an SQL statement to select elements.
        sql_statement = "SELECT %s FROM %s " \
                        "WHERE iid = %s AND revision = %d" \
                        % (col_name, table_name,
                           make_sql_string_literal(iid), revision)
        # Execute the query.
        cursor = self.GetCursor()
        cursor.execute(sql_statement)
        rows = cursor.fetchall()
        del cursor
        # Extract set elements from the rows.
        set = []
        for row in rows:
            # Extract the element value.
            row, value = self.__GetFieldFromRow(row, issue_class, contained)
            set.append(value)
            # There should be nothing left in the row.
            assert len(row) == 0
        # All done.
        return set


    def __AddSetFieldContents(self, cursor, field, issue):
        """Record elements of set 'field' of 'issue'.

        Adds elements to the auxiliary table for 'field' corresponding
        to elements of 'field's value in 'issue'.

        'cursor' -- The cursor to use to execute the INSERT
        statements."""

        assert isinstance(field, IssueFieldSet)

        iid = issue.GetId()
        revision = issue.GetRevision()
        # Get the elements in the set.
        set = issue.GetField(field.GetName())
        # Find the name of the auxiliary table for this field.
        table_name = self.__GetTableNameForSetField(issue.GetClass(), field)
        # The name of the column containing actual element values.
        contained = field.GetContainedField()
        col_name = self.__GetColumnName(contained)
        for element in set:
            # Build an SQL statement to select elements.
            value = self.__BuildSqlForFieldValue(contained, element)
            sql_statement = "INSERT INTO %s (iid, revision, %s) " \
                            "VALUES (%s, %d, %s)" \
                            % (table_name, col_name,
                               make_sql_string_literal(iid), revision,
                               value)
            # Execute the query.
            cursor.execute(sql_statement)



########################################################################
# functions
########################################################################

def make_sql_string_literal(s):
    """Return string 's' as an SQL string literal."""

    # Represent 'None' by an empty string.  Some SQL implementations
    # don't support null values.
    if s == None:
        s = ""
    # Single quotes are represented by two consecutive single quote
    # characters.
    s = string.replace(str(s), "'", "''")
    # Construct the literal.
    return "'" + s + "'"


########################################################################
# Local Variables:
# mode: python
# indent-tabs-mode: nil
# End:
