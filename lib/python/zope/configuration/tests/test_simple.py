##############################################################################
#
# Copyright (c) 2003 Zope Corporation and Contributors.
# All Rights Reserved.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE.
#
##############################################################################
r"""How to write a simple directive

This module documents how to write a simple directive.

A simple directive is a directive that doesn't contain other
directives. It can be implemented via a fairly simple function.
To implement a simple directive, you need to do 3 things:

- You need to create a schema to describe the directive parameters,

- You need to write a directive handler, and

- You need to register the directive.

In this module, we'll implement a contrived example that records
information about files in a file registry. The file registry is just
the list, ``file_registry``. Our registry will contain tuples
with:

  - file path

  - file title

  - description

  - Information about where the file was defined

Our schema is defined in IRegisterFile (see below). Our schema lists
the path and title.  We'll get the description and other information
for free, as we'll see later.  The title is not required, and may be
ommmitted.

The job of a configuration handler is to compute one or more
configuration actions.  Configuration actions are defered function
calls. The handler doesn't perform the actions. It just computes
actions, which may be performed later if they are not overridden by
other directives.

Out handler is given in the function, ``registerFile``. It takes a context,
a path and a title. All directive handlers take the directive context
as the first argument.  A directive context, at a minimim, implements,
``zope.configuration.IConfigurationContext``.  (Specialized contexts
can implement more specific interfaces. We'll say more about that when
we talk about grouping directives.)  The title argument
must have a default value, because we indicated that the title was not
required in the schema. (Alternatively, we could have made the title
required, but provided a default value in the schema.

In the first line of function `registerFile`, we get the context information
object. This object contains information about the configuration
directive, such as the file and location within the file of the
directive.

The context information object also has a text attribute that contains
the textual data contained by the configuration directive. (This is
the concatenation of all of the xml text nodes directly contained by
the directive.)  We use this for our description in the second line
of the handler.

The last thing the handler does is to compute an action by calling the
action method of the context.  It passes the action method 3 keyword
arguments:

- discriminator

  The discriminator is used to identify the action to be performed so
  that duplicate actions can be detected.  Two actions are duplicated,
  and this conflict, if they have the same discriminator values and
  the values are not ``None``.  Conflicting actions can be resolved if
  one of the conflicting actions is from a configuration file that
  directly or indirectly includes the files containing the other
  conflicting actions.

  In function ``registerFile``, we a tuple with the string
  ``'RegisterFile'`` and the path to be registered.

- callable

  The callable is the object to be called to perform the action.

- args

  The args argument contains positinal arguments to be passed to the
  callable. In function ``registerFile``, we pass a tuple containing a
  ``FileInfo`` object.

  (Note that there's nothing special about the FileInfo class. It has
   nothing to do with creating simple directives. It's just used in
   this example to organize the application data.)


The final step in implementing the simple directive is to register
it. We do that with the zcml ``meta:directive`` directive.  This is
given in the file simple.zcml.  Here we specify the name, namespace,
schema, and handler for the directive.  We also provide a
documentation for the directive as text between the start and end
tags.

The file simple.zcml also includes some directives that use the new
directive to register some files.

Now let's try it all out:

>>> from zope.configuration import tests
>>> context = xmlconfig.file("simple.zcml", tests)

Now we should see some file information in the  registry:

>>> from zope.configuration.tests.test_xmlconfig import clean_text_w_paths
>>> from zope.configuration.tests.test_xmlconfig import clean_path
>>> for i in file_registry:
...   print "path:", clean_path(i.path)
...   print "title:", i.title
...   print "description:", '\n'.join(
...               [l.rstrip()
...                for l in i.description.strip().split('\n')
...                if l.rstrip()])
...   print "info:"
...   print clean_text_w_paths(i.info)
path: tests/test_simple.py
title: How to create a simple directive
description: Describes how to implement a simple directive
info:
File "tests/simple.zcml", line 19.2-24.2
    <files:register
        path="test_simple.py"
        title="How to create a simple directive"
        >
      Describes how to implement a simple directive
    </files:register>
path: tests/simple.zcml
title: 
description: Shows the ZCML directives needed to register a simple directive.
    Also show some usage examples,
info:
File "tests/simple.zcml", line 26.2-30.2
    <files:register path="simple.zcml">
      Shows the ZCML directives needed to register a simple directive.
      Also show some usage examples,
    </files:register>
path: tests/__init__.py
title: Make this a package
description: 
info:
File "tests/simple.zcml", line 32.2-32.67
    <files:register path="__init__.py" title="Make this a package" />


We'll clean up after ourselves:

>>> del file_registry[:]

$Id: test_simple.py 27162 2004-08-17 10:41:25Z hdima $
"""

file_registry = []

                   
import unittest
from zope.testing.doctestunit import DocTestSuite
from zope import interface
from zope import schema
from zope.configuration import fields, xmlconfig

class IRegisterFile(interface.Interface):

    path = fields.Path(
        title=u"File path",
        description=u"This is the path name of the file to be registered."
        )

    title = schema.Text(
        title=u"Short summary of the file",
        description=u"This will be used in file listings",
        required = False
        )

class FileInfo(object):

    def __init__(self, path, title, description, info):
        (self.path, self.title, self.description, self.info
         ) = path, title, description, info

def registerFile(context, path, title=u""):
    info = context.info
    description = info.text.strip()
    context.action(discriminator=('RegisterFile', path),
                   callable=file_registry.append,
                   args=(FileInfo(path, title, description, info),)
                   )

def test_suite():
    return unittest.TestSuite((
        DocTestSuite(),
        ))

if __name__ == '__main__': unittest.main()
