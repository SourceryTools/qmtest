A quick introduction to generations
===================================

Generations are a way of updating objects in the database when the application
schema changes.  An application schema is essentially the structure of data,
the structure of classes in the case of ZODB or the table descriptions in the
case of a relational database.

When you change your application's data structures, for example,
you change the semantic meaning of an existing field in a class, you will
have a problem with databases that were created before your change.  For a
more thorough discussion and possible solutions, see
http://dev.zope.org/Zope3/DatabaseGenerations

We will be using the component architecture, and we will need a database and a
connection:

    >>> import cgi
    >>> from pprint import pprint
    >>> from zope.interface import implements
    >>> from zope.app.testing import ztapi

    >>> from ZODB.tests.util import DB
    >>> db = DB()
    >>> conn = db.open()
    >>> root = conn.root()

Imagine that our application is an oracle: you can teach it to react to
phrases.  Let's keep it simple and store the data in a dict:

    >>> root['answers'] = {'Hello': 'Hi & how do you do?',
    ...                    'Meaning of life?': '42',
    ...                    'four < ?': 'four < five'}
    >>> import transaction
    >>> transaction.commit()


Initial setup
-------------

Here's some generations-specific code.  We will create and register a
SchemaManager.  SchemaManagers are responsible for the actual updates of the
database.  This one will be just a dummy.  The point here is to make the
generations module aware that our application supports generations.

The default implementation of SchemaManager is not suitable for this test
because it uses Python modules to manage generations.  For now, it
will be just fine, since we don't want it to do anything just yet.

    >>> from zope.app.generations.interfaces import ISchemaManager
    >>> from zope.app.generations.generations import SchemaManager
    >>> dummy_manager = SchemaManager(minimum_generation=0, generation=0)
    >>> ztapi.provideUtility(ISchemaManager, dummy_manager, name='some.app')

'some.app' is a unique identifier.  You should use a URI or the dotted name
of your package.

When you start Zope and a database is opened, an
IDatabaseOpenedWithRootEvent is sent.  Zope registers
evolveMinimumSubscriber by default as a handler for this event.  Let's
simulate this:

    >>> class DatabaseOpenedEventStub(object):
    ...     def __init__(self, database):
    ...         self.database = database
    >>> event = DatabaseOpenedEventStub(db)

    >>> from zope.app.generations.generations import evolveMinimumSubscriber
    >>> evolveMinimumSubscriber(event)

The consequence of this action is that now the database contains the fact
that our current schema number is 0.  When we update the schema, Zope3 will
have an idea of what the starting point was.  Here, see?

    >>> from zope.app.generations.generations import generations_key
    >>> root[generations_key]['some.app']
    0

In real life you should never have to bother with this key directly,
but you should be aware that it exists.


Upgrade scenario
----------------

Back to the story.  Some time passes and one of our clients gets hacked because
we forgot to escape HTML special characters!  The horror!  We must fix this
problem ASAP without losing any data.  We decide to use generations to impress
our peers.

Let's update the schema manager (drop the old one and install a new custom
one):

    >>> ztapi.unprovideUtility(ISchemaManager, name='some.app')

    >>> class MySchemaManager(object):
    ...     implements(ISchemaManager)
    ...
    ...     minimum_generation = 1
    ...     generation = 2
    ...
    ...     def evolve(self, context, generation):
    ...         root = context.connection.root()
    ...         answers = root['answers']
    ...         if generation == 1:
    ...             for question, answer in answers.items():
    ...                 answers[question] = cgi.escape(answer)
    ...         elif generation == 2:
    ...             for question, answer in answers.items():
    ...                 del answers[question]
    ...                 answers[cgi.escape(question)] = answer
    ...         else:
    ...             raise ValueError("Bummer")
    ...         root['answers'] = answers # ping persistence
    ...         transaction.commit()

    >>> manager = MySchemaManager()
    >>> ztapi.provideUtility(ISchemaManager, manager, name='some.app')

We have set `minimum_generation` to 1.  That means that our application
will refuse to run with a database older than generation 1.  The `generation`
attribute is set to 2, which means that the latest generation that this
SchemaManager knows about is 2.

evolve() is the workhorse here.  Its job is to get the database from
`generation`-1 to `generation`.  It gets a context which has the attribute
'connection', which is a connection to the ZODB.  You can use that to change
objects like in this example.

In this particular implementation generation 1 escapes the answers (say,
critical, because they can be entered by anyone!), generation 2 escapes the
questions (say, less important, because these can be entered by authorized
personell only).

In fact, you don't really need a custom implementation of ISchemaManager.  One
is available, we have used it for a dummy previously. It uses Python modules
for organization of evolver functions.  See its docstring for more information.

In real life you will have much more complex object structures than the one
here.  To make your life easier, there are two very useful functions available
in zope.app.generations.utility: findObjectsMatching() and
findObjectsProviding().  They will dig through containers recursively to help
you seek out old objects that you wish to update, by interface or by some other
criteria.  They are easy to understand, check their docstrings.


Generations in action
---------------------

So, our furious client downloads our latest code and restarts Zope.  The event
is automatically sent again:

    >>> event = DatabaseOpenedEventStub(db)
    >>> evolveMinimumSubscriber(event)

Shazam!  The client is happy again!

    >>> pprint(root['answers'])
    {'Hello': 'Hi &amp; how do you do?',
     'Meaning of life?': '42',
     'four < ?': 'four &lt; five'}

Because evolveMinimumSubscriber is very lazy, it only updates the database just
enough so that your application can use it (to the `minimum_generation`, that
is).  Indeed, the marker indicates that the database generation has been bumped
to 1:

    >>> root[generations_key]['some.app']
    1

We see that generations are working, so we decide to take the next step
and evolve to generation 2.  Let's see how this can be done manually:

    >>> from zope.app.generations.generations import evolve
    >>> evolve(db)

    >>> pprint(root['answers'])
    {'Hello': 'Hi &amp; how do you do?',
     'Meaning of life?': '42',
     'four &lt; ?': 'four &lt; five'}
    >>> root[generations_key]['some.app']
    2

Default behaviour of `evolve` upgrades to the latest generation provided by
the SchemaManager. You can use the `how` argument to evolve() when you want
just to check if you need to update or if you want to be lazy like the
subscriber which we have called previously.

Installation
------------

In the the example above, we manually initialized the answers.  We
shouldn't have to do that manually.  The application should be able to
do that automatically.

IInstallableSchemaManager extends ISchemaManager, providing an install
method for performing an intial installation of an application.  This
is a better alternative than registering database-opened subscribers.

Let's define a new schema manager that includes installation:


    >>> ztapi.unprovideUtility(ISchemaManager, name='some.app')

    >>> from zope.app.generations.interfaces import IInstallableSchemaManager
    >>> class MySchemaManager(object):
    ...     implements(IInstallableSchemaManager)
    ...
    ...     minimum_generation = 1
    ...     generation = 2
    ...
    ...     def install(self, context):
    ...         root = context.connection.root()
    ...         root['answers'] = {'Hello': 'Hi &amp; how do you do?',
    ...                            'Meaning of life?': '42',
    ...                            'four &lt; ?': 'four &lt; five'}
    ...         transaction.commit()
    ...
    ...     def evolve(self, context, generation):
    ...         root = context.connection.root()
    ...         answers = root['answers']
    ...         if generation == 1:
    ...             for question, answer in answers.items():
    ...                 answers[question] = cgi.escape(answer)
    ...         elif generation == 2:
    ...             for question, answer in answers.items():
    ...                 del answers[question]
    ...                 answers[cgi.escape(question)] = answer
    ...         else:
    ...             raise ValueError("Bummer")
    ...         root['answers'] = answers # ping persistence
    ...         transaction.commit()

    >>> manager = MySchemaManager()
    >>> ztapi.provideUtility(ISchemaManager, manager, name='some.app')

Now, lets open a new database:

    >>> db.close()
    >>> db = DB()
    >>> conn = db.open()
    >>> 'answers' in conn.root()
    False


    >>> event = DatabaseOpenedEventStub(db)
    >>> evolveMinimumSubscriber(event)

    >>> conn.sync()
    >>> root = conn.root()

    >>> pprint(root['answers'])
    {'Hello': 'Hi &amp; how do you do?',
     'Meaning of life?': '42',
     'four &lt; ?': 'four &lt; five'}
    >>> root[generations_key]['some.app']
    2
