########################################################################
#
# File:   sql_idb.py
# Author: Alex Samuel
# Date:   2000-12-21
#
# Contents:
#   Generic SQL implementation of the IDB.
#
# Copyright (c) 2000, 2001 by CodeSourcery, LLC.  All rights reserved. 
#
# For license terms see the file COPYING.
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

    -- Attachment fields are represented by four columns, each VARCHAR,
       containing the attachment location, MIME type, description, and
       original file name, respectively.

    -- A set field is represented by an auxiliary table.  The table
       contains three columns: an issue id, a revision number, and a
       field value.  For a particular issue revision, each element of
       the set field is represented by a row in the auxiliary table.
       The row includes the issue's iid and revision number, and the
       column(s) containing the actual element value.
            
   Except for attachment fields, the column name is the same as the
   field name.  For an attachment field named "foo", the column names
   are "_atl_foo", "_att_foo", "_atd_foo", and "_atn_foo", respectively.
"""

########################################################################
# imports
########################################################################

from   issue import *
import issue_class
import issue_database
import parser
import qm.fields
import rexec
import string
import symbol
import token

########################################################################
# classes
########################################################################

class SqlIdb(issue_database._IssueDatabase):
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

    # Many of the operations in this implementation use issues
    # represented by tuples of field values rather than 'Issue'
    # instances.  These tuples are what is returned by the RDBMS from
    # selects on the issue tables.  Since we'll often filter out many
    # of these rows immediately after selecting, when possible we
    # filter the rows directly rather than converting them all to
    # 'Issue' instances.
    #
    # To facilitate this, the issue id is always the first column in
    # an issue table, and therefore each row contains the issue id in
    # the first position.  Similarly, the revision number is always
    # second. 
    

    def __init__(self, path, create_idb):
        # Perform base class initialization.
        issue_database._Issue_Database.__init__(self, path, create_idb)


    def Close(self):
        # Perform base class operation.
        issue_database._Issue_Database.Close(self)


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
            if isinstance(field, qm.fields.SetField):
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
        
        # Make sure the issue is OK.
        issue.AssertValid()
        # Check IID uniqueness.
        try:
            revision = self.GetIssue(issue.GetId())
            # Oops, we foudn this issue.
            raise ValueError, "iid already in use"
        except KeyError:
            # Couldn't find the issue.  That's good.
            pass
        # Set the revision number to zero.
        issue.SetField("revision", 0)
        # Set the timestamp to now.
        issue.StampTime()
        # Make sure the issue's class is in this IDB.
        issue_class = issue.GetClass()
        if not self.__HasIssueClass(issue_class):
            raise ValueError, "new issue in a class not in this IDB"
        # Insert the first revision.
        return self.__InsertIssue(issue_class, issue)


    def AddRevision(self, issue):
        """Add a revision of an existing issue to the database.

        returns -- A true value if the addition succeeded.

        'issue' -- A new revision of an existing issue.  The revision
        number is ignored and replaced with the next consecutive one
        for the issue."""

        issue_class = issue.GetClass()
        # Make sure the issue is OK.
        issue.AssertValid()
        # Find the current revision, and assign the next revision
        # number to 'issue'.
        current = self.GetIssue(issue.GetId(), issue_class=issue_class)
        next_revision_number = current.GetRevision() + 1
        issue.SetField("revision", next_revision_number)
        # Set the timestamp to now.
        issue.StampTime()
        # Insert the revision.
        return self.__InsertIssue(issue_class, issue, current)


    def GetIssueClasses(self):
        """Return a sequence of issue classes in this IDB."""

        return self.issue_classes.values()


    def GetIssues(self, issue_class=None):
        """Return a list of all the issues.

        'issue_class' -- If an issue class name or 'IssueClass'
        instance is provided, all issues in this class will be
        returned.  If 'issue_class' is 'None', returns all issues in
        all classes.

        returns -- Returns a list of the current revisions of all
        issues in the database."""

        import types
        # If 'issue_class' is the name of an issue class, look up the
        # class itself.
        if isinstance(issue_class, types.StringType):
            issue_class = self.GetIssueClass(issue_class)
        # Make a list of one or many classes we'll scan over.
        if issue_class is None:
            # No classes specified, so use all of them.
            classes_to_search = self.issue_classes.values()
        else:
            classes_to_search = [issue_class]

        # FIXME: This is grotesquely inefficient.  Some caching of
        # most recent revisions or something like that is definitely
        # called for, if this function is going to stay around.
        # Probably, we shouldn't even support this operation.

        # We'll construct this list of all issues we find.
        issues = []
        # Loop over issue classes we care about.
        for icl in classes_to_search:
            # Get all revisions.
            rows = self.__SelectRows(icl, None)
            # Keep current revisions only.
            rows = self.__FilterCurrentRows(rows)
                
            # The values of the map are the most recent revisions of
            # all our issues.
            for row in rows:
                # Build an 'Issue' object.
                issue = self.__BuildIssueFromRow(icl, row)
                # Invoke get triggers on it.
                try:
                    self._InvokeGetTriggers(issue)
                except idb.TriggerRejectError:
                    pass
                else:
                    # Keep issues that pass the triggers.
                    issues.append(issue)

        return issues


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
        elif isinstance(issue_class, qm.track.issue_class.IssueClass):
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
                      % (revision, iid)

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
        try:
            self._InvokeGetTriggers(issue)
        except idb.TriggerReject:
            # The trigger rejected the retrieval, so behave as if the
            # issue was nout found.
            raise KeyError, "no revision with IID '%s' found" % iid

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
        elif isinstance(issue_class, qm.track.issue_class.IssueClass):
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
            try:
                self._InvokeGetTriggers(issue)
            except idb.TriggerRejectError:
                pass
            else:
                # Keep the issue only if the trigger passed it.
                issues.append(issue)

        return issues


    def GetCurrentRevisionNumber(self, iid):
        """Return the current revision number for issue 'iid'."""

        return self.GetIssue(iid).GetRevision()


    def Query(self, query_str, issue_class_name):
        """Query the database.

        This method is overridden from the idb base class. Instead of
        iterating over all of the issues and evaluating the query string
        on each issue, we parse the query string, convert it to an SQL
        type query, and submit the query via sql. This is more efficient.

        query_str -- The string with the python expression to be evaluated
        on each issue to determine if the issue matches.
        
        issue_class_name -- The name of the class of which you wish to
        query issues.  Only issues of that class will be queried.  

        returns -- This function returns a list of issues that match a
        query."""

        no_sql = self.__CheckTautology(query_str)

        if no_sql:
            query_command = "1 = 1"
        else:
            query_command = self.__ConvertToSQL(query_str)

        rows = [ ]
        icl = self.GetIssueClass(issue_class_name)
        try:
            results = self.__SelectRows(icl, query_command)
        except:
            raise qm.UserError, "Invalid SQL query '%s'." \
                  % query_command
        # For each result, build the issue to be in the list.
        results = []
        for row in rows:
            # Construct the issue.
            issue = self.__BuildIssueFromRow(icl, row)
            # Append the new issue to the list of results.
            results.append(issue)

        # Return the list of matches
        return results

        
    # Helper functions.

    def __ColumnSpecForField(self, issue_class, field):
        """Return a column specification for storing 'field'.

        'field' -- The field for which the column spec is returned.
        May not be a set field.

        returns -- A string representing the SQL specification of the
        column (or columns) used to represent 'field'."""

        name = field.GetName()
        # Select column type based on the field type.
        if isinstance(field, qm.fields.IntegerField):
            return "%s INTEGER" % name

        elif isinstance(field, qm.fields.TextField):
            return "%s VARCHAR" % name

        elif isinstance(field, qm.fields.SetField):
            raise RuntimeError, 'field may not be a set field'

        elif isinstance(field, qm.fields.AttachmentField):
            # For an attachment field, 'col_name' is a triplet of
            # three names of columns that are used to implement
            # the field.   All three should be VARCHARs.
            return "_atl_%s VARCHAR, _att_%s VARCHAR, " \
                   "_atd_%s VARCHAR, _atn_%s VARCHAR" \
                   % (4 * (name, ))

        else:
            raise RuntimeError, "unrecognized field type"
        

    def __MakeTableForSetField(self, issue_class, field):
        """Create an auxiliary table for set field 'field'."""

        assert isinstance(field, qm.fields.SetField)

        # Build the name of the table.
        table_name = self.__GetTableNameForSetField(issue_class, field)
        # Extract the field type of the elements of the set.
        contained = field.GetContainedField()
        # Set fields may not be nested.
        if __debug__ and isinstance(contained, qm.fields.SetField):
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
        self._InvokePreupdateTriggers(issue, previous_issue)

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
            if isinstance(field, qm.fields.SetField):
                self.__AddSetFieldContents(cursor, field, issue)
        # Delete the cursor to commit the results.
        del cursor

        # Invoke postupdate triggers.
        self._InvokePostupdateTriggers(issue, previous_issue)

        return 1


    def __SelectRows(self, issue_class, where_clause):
        """Issue an SQL SELECT statement and return the resulting rows.

        'issue_class' -- The issue class to query.

        'where_clause' -- The WHERE clause of the SELECT statement.
        If 'None', no WHERE clause is used.

        'revision' -- The revision number to request for each issue.
        If negative, the highest revision number is returned.  If
        'None', all revisions are returned.

        returns -- A sequence of tuples representing table rows that
        satisfy 'where_clause'."""

        # Construct an SQL SELECT statement.
        table_name = self.__GetTableName(issue_class)
        col_names = self.__GetColumnNames(issue_class)
        sql_statement = "SELECT %s FROM %s" % (col_names, table_name)
        # Add the WHERE clause, if specified.
        if where_clause is not None:
            sql_statement = sql_statement + " WHERE %s" % where_clause

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
        if isinstance(field, qm.fields.AttachmentField):
            # Attachment fields are implemented by three columns.
            # Return a triplet of the column names.  Use reserved
            # labels to avoid conflicts with user field names.
            return "_atl_%s, _att_%s, _atd_%s, _atn_%s" % (4 * (name, ))
        elif isinstance(field, qm.fields.SetField):
            return None
        else:
            return name


    def __GetTableNameForSetField(self, issue_class, field):
        """Return the name of the auxiliary table for set 'field'."""

        assert isinstance(field, qm.fields.SetField)
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


    def __FilterCurrentRows(self, rows):
        """Filter 'rows', keeping only the latest revision of each issue.

        'row' -- A sequence of tuples representing issues."""

        # We'll construct a map from iid to the row corresponding
        # to the most recent revision of this issue we've seen so far.
        map_iid_to_row = {}
        # Select all rows in this issue class.
        for row in rows:
            # Fish out the iid.
            iid = row[0]
            # Keep this row, if it's the first row we've seen for
            # this issue class, or if it has the larger revision
            # number than the previous most-recent.
            if not map_iid_to_row.has_key(iid) \
               or map_iid_to_row[iid][1] < row[1]:
                map_iid_to_row[iid] = row

        return map_iid_to_row.values()


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
            if isinstance(field, qm.fields.SetField):
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

        if isinstance(field, qm.fields.IntegerField):
            # Convert the integer to a string.
            return str(value)
        elif isinstance(field, qm.fields.TextField):
            # Express the text as an SQL string literal.
            value = escape_for_sql(value)
            return make_sql_string_literal(value)
        elif isinstance(field, qm.fields.SetField):
            # Set fields are implemented with auxiliary tables.
            # They require no columns in the main table.
            return None
        elif isinstance(field, qm.fields.AttachmentField):
            # An attachment is represented by three columns.
            if value == None:
                # For no attachment, use four empty strings.
                return "'', '', '', ''"
            else:
                cols = (
                    value.location,
                    value.mime_type,
                    value.description,
                    value.file_name,
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
        
        if isinstance(field, qm.fields.IntegerField):
            value = int(row[0])
            new_row = row[1:]

        elif isinstance(field, qm.fields.TextField):
            value = str(row[0])
            value = unescape_for_sql(value)
            new_row = row[1:]

        elif isinstance(field, qm.fields.SetField):
            raise ValueError, 'field may not be a set field'

        elif isinstance(field, qm.fields.AttachmentField):
            # The next four columns contain information about the
            # attachment. 
            location, value, mime_type, file_name = row[:4]
            # Advance past all four columns.
            new_row = row[4:]
            if location == "":
                # A null location field indicates no attachment.
                value = None
            else:
                value = qm.track.Attachment(mime_type=mime_type,
                                            description=description,
                                            file_name=file_name,
                                            location=location)
        else:
            raise RuntimeError, "unrecognized field type"

        return new_row, value


    def __GetSetFieldContents(self, issue_class, field, iid, revision):
        """Return the contents of 'field' for the specified issue.

        'issue_class' -- The class containing the issue.

        'field' -- The set field of which the contents are returned."""

        assert isinstance(field, qm.fields.SetField)

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

        assert isinstance(field, qm.fields.SetField)

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


    def __ConvertToSQL(self, string_expr):
        """Create an SQL expression query from the python expression.

        'string_expr' -- The python string to evaluate for the query.

        returns -- A WHERE clause of an SQL query string that may be used
        to query an SQL database."""

        try:
            # Get the AST
            ast = parser.ast2tuple(parser.expr(string_expr))
        except:
            raise qm.UserError, \
                  "Unable to parse Python query expression '%s'." \
                  % string_expr
        try:
            # Pass it on to the helper to create the actual SQL string.
            sql_str = self.__AstToSQL(ast)
        except:
            raise ValueError, \
                  "Invalid Python query expression: '%s'" \
                  % string_expr
        return sql_str


    def __AstToSQL(self, ast):
        """Returns the SQL expression for the given python AST.

        'ast' -- The ast as returned by the ast2tuple from the parser.

        returns -- A string that represents the SQL query.

        Subclasses should override this method for the types of trees they
        wish to handle differently. The grammar for these expressions
        is listed below.

        expression:    or_test

        or_test:       and_test 
                       | or_test "or" and_test
        
        and_test:      not_test 
                       | and_test "and" not_test

        not_test:      comparison 
                       | "not" not_test

        comparison:    or_expr (comp_operator or_expr)*

        comp_operator: "<" 
                       | ">"
                       | "==" 
                       | ">=" 
                       | "<=" 
                       | "<>"
                       | "!="

        or_expr:       xor_expr 
                       | or_expr "|" xor_expr

        xor_expr:      and_expr 
                       | xor_expr "^" and_expr

        and_expr:      shift_expr 
                       | and_expr "&" shift_expr

        shift_expr:    a_expr 
                       | shift_expr ("<<" | ">>") a_expr

        a_expr:        m_expr 
                       | a_expr "+" m_expr 
                       | a_expr "-" m_expr

        m_expr:        u_expr 
                       | m_expr "*" u_expr 
                       | m_expr "/" u_expr
                       | m_expr "%" u_expr

        u_expr:        power 
                       | "-" u_expr 
                       | "+" u_expr 
                       | "~" u_expr

        power:         primary ["**" u_expr]

        primary:       atom

        atom:          identifier
                       | literal
                       | enclosure

        literal:       stringliteral
                       | integer    
                       | floatnumber

        enclosure:     parenth_form

        parenth_form:  "(" [expression_list] ")"

        expression_list: expression ("," expression)* [","]"""
        
        # Initialize the sql string.
        sql_str = ""
        
        # Get the top level token from the ast to decide how to process
        # this ast.
        tok = ast[0]

        # Non-terminal 'expression'.
        if tok == symbol.eval_input:
            if len(ast) != 4:
                raise "Unrecognized expression"
            sql_str = self.__AstToSQL(ast[1])
        # Of of these non-terminals behave the same so
        # we put them together. We rely on the fact that the python parser
        # will correctly build up the tree for us. Therefore, we don't
        # really need to check that there are the correct number of
        # subtrees or anything like that, except for in special cases that
        # we wish to handle differently.
        elif tok == symbol.testlist \
             or tok == symbol.test \
             or tok == symbol.and_test \
             or tok == symbol.not_test \
             or tok == symbol.comparison \
             or tok == symbol.comp_op \
             or tok == symbol.expr \
             or tok == symbol.xor_expr \
             or tok == symbol.and_expr \
             or tok == symbol.shift_expr \
             or tok == symbol.arith_expr \
             or tok == symbol.term \
             or tok == symbol.power:
            sql_str = self.__AstToSQLHelper(ast, " ")
        # We leave these two out because we want the spacing to be right
        # next to each other, instead of spaced one apart like all the
        # rest. This is for +4, -4, etc. Same goes for atoms.
        elif tok == symbol.factor \
             or tok == symbol.atom:
            sql_str = self.__AstToSQLHelper(ast, "")
        # For the NAME token, most of them remain the same, but the
        # boolean operators must be capitalized.
        elif tok == token.NAME:
            if ast[1] == 'or':
                sql_str = "OR"
            elif ast[1] == 'and':
                sql_str = "AND"
            elif ast[1] == 'not':
                sql_str = "NOT"
            elif ast[1] == 'in':
                raise "Expression not in python subset."
            else:
                sql_str = ast[1]
        # Most of the operators in python are the same in SQL so just
        # use their python representation.
        elif tok == token.STRING \
             or tok == token.LPAR \
             or tok == token.RPAR \
             or tok == token.LSQB \
             or tok == token.RSQB \
             or tok == token.LESS \
             or tok == token.GREATER \
             or tok == token.NOTEQUAL \
             or tok == token.NUMBER \
             or tok == token.LEFTSHIFT \
             or tok == token.RIGHTSHIFT \
             or tok == token.PLUS \
             or tok == token.MINUS \
             or tok == token.STAR \
             or tok == token.SLASH \
             or tok == token.PERCENT \
             or tok == token.TILDE \
             or tok == token.VBAR \
             or tok == token.AMPER \
             or tok == token.COMMA:
            sql_str = ast[1]
        # The (power) '**' operator in python is '^' in SQL.
        elif tok == token.DOUBLESTAR:
            sql_str = "^"
        # The (xor) '^' operator in python is '#' in SQL.
        elif tok == token.CIRCUMFLEX:
            sql_str = "#"
        # The (comparison) '==' operator in python is '=' in SQL.
        elif tok == token.EQEQUAL:
            sql_str = "="
        else:
            raise "Expression not in python subset."

        # Finally return the string we have built up.
        return sql_str

        
    def __AstToSQLHelper(self, ast, seperator):
        """Calls AstToSQL recursively and builds up string.

        'ast' -- The ast as passed to __AstToSQL.

        'separator' -- The seperator that you wish to sepearte tokens
        at this highest level.
        
        returns -- An SQL string that __AstToSQL will return."""

        if len(ast) >= 2:
            sql_str = self.__AstToSQL(ast[1])
            if len(ast) > 2:
                num_taken = 2
                while num_taken < len(ast):
                    sql_str = "%s%s%s" % (sql_str, seperator,
                                          self.__AstToSQL(ast[num_taken]))
                    num_taken = num_taken + 1
        else:
            raise "Unrecognized expression"
        return sql_str


    def __CheckTautology(self, query_str):
        """Check to see if the given string is a tautology in python.

        This checks to see if the pythong string evaluates to true
        before even setting up the environment. This is because you can
        give python '1' and that will evaulate to true but in SQL, that
        will not be a boolean expression therefore it is not a valid
        search criteria. Eventually, we'll need to be more general
        and notice when they are using the value of an int to represent
        a boolean, but for now, we'll just take the whole expression.

        'query_str' -- The python expression to be checked for true.

        returns -- 1 if the expression is always true, 0 otherwise."""
        query_env = rexec.RExec()
        try:
            if query_env.r_eval(query_str):
                return 1
            else:
                return 0
        # If an exception occurs, that means there's probably a variable
        # in there somewhere so we know its not a tautology.
        except:
            return 0
            

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


def escape_for_sql(s):
    """Modify 's' so it's safe to use as an SQL string."""
    
    # Some databases choke on newlines.  Linefeeds seem to be safe
    # though. 
    s = string.replace(s, "\n", "\r")
    return s


def unescape_for_sql(s):
    """Reverse the effects of 'escape_for_sql'."""

    s = string.replace(s, "\r", "\n")
    return s


########################################################################
# Local Variables:
# mode: python
# indent-tabs-mode: nil
# fill-column: 72
# End:
