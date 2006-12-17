=======================================
Using additional DTML tags in SQLScript
=======================================

Inserting optional tests with 'sqlgroup'
----------------------------------------

It is sometimes useful to make inputs to an SQL statement optinal.
Doing so can be difficult, because not only must the test be inserted
conditionally, but SQL boolean operators may or may not need to be
inserted depending on whether other, possibly optional, comparisons
have been done.  The 'sqlgroup' tag automates the conditional
insertion of boolean operators.

The 'sqlgroup' tag is a block tag that has no attributes. It can have
any number of 'and' and 'or' continuation tags.

Suppose we want to find all people with a given first or nick name and
optionally constrain the search by city and minimum and maximum age.
Suppose we want all inputs to be optional.  We can use DTML source
like the following::

  <dtml-sqlgroup>
    <dtml-sqlgroup>
      <dtml-sqltest name column=nick_name type=nb multiple optional>
    <dtml-or>
      <dtml-sqltest name column=first_name type=nb multiple optional>
    </dtml-sqlgroup>
  <dtml-and>
    <dtml-sqltest home_town type=nb optional>
  <dtml-and>
    <dtml-if minimum_age>
       age >= <dtml-sqlvar minimum_age type=int>
    </dtml-if>
  <dtml-and>
    <dtml-if maximum_age>
       age <= <dtml-sqlvar maximum_age type=int>
    </dtml-if>
  </dtml-sqlgroup>

This example illustrates how groups can be nested to control boolean
evaluation order.  It also illustrates that the grouping facility can
also be used with other DTML tags like 'if' tags.

The 'sqlgroup' tag checks to see if text to be inserted contains other
than whitespace characters.  If it does, then it is inserted with the
appropriate boolean operator, as indicated by use of an 'and' or 'or'
tag, otherwise, no text is inserted.

Inserting optional tests with 'sqlgroup'
----------------------------------------

It is sometimes useful to make inputs to an SQL statement optinal.
Doing so can be difficult, because not only must the test be inserted
conditionally, but SQL boolean operators may or may not need to be
inserted depending on whether other, possibly optional, comparisons
have been done.  The 'sqlgroup' tag automates the conditional
insertion of boolean operators.

The 'sqlgroup' tag is a block tag. It can have any number of 'and' and
'or' continuation tags.

The 'sqlgroup' tag has an optional attribure, 'required' to specify
groups that must include at least one test.  This is useful when you
want to make sure that a query is qualified, but want to be very
flexible about how it is qualified.

Suppose we want to find people with a given first or nick name, city
or minimum and maximum age.  Suppose we want all inputs to be
optional, but want to require *some* input.  We can use DTML source
like the following::

  <dtml-sqlgroup required>
    <dtml-sqlgroup>
      <dtml-sqltest name column=nick_name type=nb multiple optional>
    <dtml-or>
      <dtml-sqltest name column=first_name type=nb multiple optional>
    </dtml-sqlgroup>
  <dtml-and>
    <dtml-sqltest home_town type=nb optional>
  <dtml-and>
    <dtml-if minimum_age>
       age >= <dtml-sqlvar minimum_age type=int>
    </dtml-if>
  <dtml-and>
    <dtml-if maximum_age>
       age <= <dtml-sqlvar maximum_age type=int>
    </dtml-if>
  </dtml-sqlgroup>

This example illustrates how groups can be nested to control boolean
evaluation order.  It also illustrates that the grouping facility can
also be used with other DTML tags like 'if' tags.

The 'sqlgroup' tag checks to see if text to be inserted contains other
than whitespace characters.  If it does, then it is inserted with the
appropriate boolean operator, as indicated by use of an 'and' or 'or'
tag, otherwise, no text is inserted.

Inserting values with the 'sqlvar' tag
--------------------------------------

The 'sqlvar' tag is used to type-safely insert values into SQL text.
The 'sqlvar' tag is similar to the 'var' tag, except that it replaces
text formatting parameters with SQL type information.

The sqlvar tag has the following attributes:

`name`
  The name of the variable to insert. As with other DTML tags, the
  'name=' prefix may be, and usually is, ommitted.

`type`
  The data type of the value to be inserted.  This attribute is
  required and may be one of 'string', 'int', 'float', or 'nb'.  The
  'nb' data type indicates a string that must have a length that is
  greater than 0.

`optional`
  A flag indicating that a value is optional.  If a value is optional
  and is not provided (or is blank when a non-blank value is
  expected), then the string 'null' is inserted.

For example, given the tag::

  <dtml-sqlvar x type=nb optional>

if the value of 'x' is::

  Let\'s do it

then the text inserted is:

  'Let''s do it'

however, if x is ommitted or an empty string, then the value inserted
is 'null'.
