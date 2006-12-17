=================
Content Providers
=================

This package provides a framework to develop componentized Web GUI
applications. Instead of describing the content of a page using a single
template or static system of templates and METAL macros, content provider
objects are dynamically looked up based on the setup/configuration of the
application.

  >>> from zope.contentprovider import interfaces


Motivation and Design Goals
---------------------------

Before diving into the features of this package let me take up a few bytes of
text to explain the use cases that drove us to develop this package (also
others) and how the API documented below fulfills/solves those use cases. When
we started developing Zope 3, it was from a desire to decentralize
functionality and thus the complexity of the Python code. And we were
successful! The component architecture is a marvelous piece of software that
hopefully will allow us to build scalable solutions for a very long
time. However, when it comes to user interface design, in this case
specifically HTML pages, we have failed to provide the features and patterns
of assembeling a page from configured components.

Looking up views for a particular content component and a request just simply
does not work by itself. The content inside the page is still monolithic. One
attempt to solve this problem are METAL macros, which allow you to insert
other TAL snippets into your main template. But macros have two shortcomings.
For one there is a "hard-coded" one-to-one mapping between a slot and the
macro that fills that slot, which makes it impossible to register several
macros for a given location. The second problem is that macros are not views
in their own right; thus they cannot provide functionality that is independent
of the main template's view.

A second approach to modular UI design are rendering pipes. Rendering pipes
have the great advantage that they can reach all regions of the page during
every step of the rendering process. For example, if we have a widget in the
middle of the page that requires some additional Javascript, then it is easy
for a rendering unit to insert the Javascript file link in the HTML header of
the page. This type of use case is very hard to solve using page
templates. However, pipes are not the answer to componentized user interface,
since they cannot simply deal with registering random content for a given page
region. In fact, I propose that pipelines are orthogonal to content providers,
the concept introducted below. A pipeline framework could easily use
functionality provided by this and other packages to provide component-driven
UI design.

So our goal is clear: Bring the pluggability of the component architecture
into page templates and user interface design. Zope is commonly known to
reinvent the wheel, develop its own terminology and misuse other's terms. For
example, the Plone community has a very different understanding of what a
"portlet" is compared to the commonly accepted meaning in the corporate world,
which derives its definition from JSR 168. Therefore an additional use case of
the design of this package was to stick with common terms and use them in
their original meaning -- well, given a little extra twist.

The most basic user interface component in the Web application Java world is
the "content provider" [1]_. A content provider is simply responsible for
providing HTML content for a page. This is equivalent to a view that does not
provide a full page, but just a snippet, much like widgets or macros. Once
there is a way to configure those content providers, we need a way to
inserting them into our page templates. In our implementation this is
accomplished using a new TALES namespace that allows to insert content
providers by name. But how, you might wonder, does this provide a
componentized user interface? On the Zope 3 level, each content provider is
registered as a presentation component discriminted by the context, request
and view it will appear in. Thus different content providers will be picked
for different configurations.

Okay, that's pretty much everything there is to say about content
providers. What, we are done? Hold on, what about defining regions of pages
and filling them configured UI snippets. The short answer is: See the
``zope.viewlet`` pacakge. But let me also give you the long answer. This and
the other pacakges were developed using real world use cases. While doing
this, we noticed that not every project would need, for example, all the
features of a portlet, but would still profit from lower-level features. Thus
we decided to declare clear boundaries of functionality and providing each
level in a different package. This particualr package is only meant to provide
the interface between the content provider world and page templates.

.. [1] Note that this is a bit different from the role named content provider,
       which refers to a service that provides content; the content provider
       we are talking about here are the software components the service would
       provide to an application.


Content Providers
-----------------

Content Provider is a term from the Java world that refers to components that
can provide HTML content. It means nothing more! How the content is found and
returned is totally up to the implementation. The Zope 3 touch to the concept
is that content providers are multi-adapters that are looked up by the
context, request (and thus the layer/skin), and view they are displayed in.

The second important concept of content providers are their two-phase
rendering design. In the first phase the state of the content provider is
prepared and, if applicable, any data, the provider is responsible for, is
updated.

So let's create a simple content provider:

  >>> import zope.interface
  >>> import zope.component
  >>> from zope.publisher.interfaces import browser

  >>> class MessageBox(object):
  ...     zope.interface.implements(interfaces.IContentProvider)
  ...     zope.component.adapts(zope.interface.Interface,
  ...                           browser.IDefaultBrowserLayer,
  ...                           zope.interface.Interface)
  ...     message = u'My Message'
  ...
  ...     def __init__(self, context, request, view):
  ...         self.__parent__ = view
  ...
  ...     def update(self):
  ...         pass
  ...
  ...     def render(self):
  ...         return u'<div class="box">%s</div>' %self.message

The ``update()`` method is executed during phase one. Since no state needs to
be calculated and no data is modified by this simple content provider, it is
an empty implementation. The ``render()`` method implements phase 2 of the
process. We can now instantiate the content provider (manually) and render it:

  >>> box = MessageBox(None, None, None)
  >>> box.render()
  u'<div class="box">My Message</div>'

Since our content provider did not require the context, request or view to
create its HTML content, we were able to pass trivial dummy values into the
constructor. Also note that the provider must have a parent (using the
``__parent__`` attribute) specified at all times. The parent must be the view
the provider appears in.

I agree, this functionally does not seem very useful now. The constructor and
the ``update()`` method seem useless and the returned content is totally
static. However, we implemented a contract for content providers that other
code can rely on. Content providers are (commonly) instantiated using the
context, request and view they appear in and are required to always generate
its HTML using those three components.


Two-Phased Content Providers
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Let's now have a look at a content provider that actively uses the two-phase
rendering process. The simpler scenario is the case where the content provider
updates a content component without affecting anything else. So let's create a
content component to be updated,

  >>> class Article(object):
  ...     title = u'initial'
  >>> article = Article()

and the content provider that is updating the title:

  >>> class ChangeTitle(object):
  ...     zope.interface.implements(interfaces.IContentProvider)
  ...     zope.component.adapts(zope.interface.Interface,
  ...                           browser.IDefaultBrowserLayer,
  ...                           zope.interface.Interface)
  ...     fieldName = 'ChangeTitle.title'
  ...
  ...     def __init__(self, context, request, view):
  ...         self.__parent__ = view
  ...         self.context, self.request = context, request
  ...
  ...     def update(self):
  ...         if self.fieldName in self.request:
  ...             self.context.title = self.request[self.fieldName]
  ...
  ...     def render(self):
  ...         return u'<input name="%s" value="%s" />' % (self.fieldName,
  ...                                                     self.context.title)

Using a request, let's now instantiate the content provider and go through the
two-phase rendering process:

  >>> from zope.publisher.browser import TestRequest
  >>> request = TestRequest()
  >>> changer = ChangeTitle(article, request, None)
  >>> changer.update()
  >>> changer.render()
  u'<input name="ChangeTitle.title" value="initial" />'

Let's now enter a new title and render the provider:

  >>> request = TestRequest(form={'ChangeTitle.title': u'new title'})
  >>> changer = ChangeTitle(article, request, None)
  >>> changer.update()
  >>> changer.render()
  u'<input name="ChangeTitle.title" value="new title" />'
  >>> article.title
  u'new title'

So this was easy. Let's now look at a case where one content provider's update
influences the content of another. Let's say we have a content provider that
displays the article's title:

  >>> class ViewTitle(object):
  ...     zope.interface.implements(interfaces.IContentProvider)
  ...     zope.component.adapts(zope.interface.Interface,
  ...                           browser.IDefaultBrowserLayer,
  ...                           zope.interface.Interface)
  ...
  ...     def __init__(self, context, request, view):
  ...         self.context, self.__parent__ = context, view
  ...
  ...     def update(self):
  ...         pass
  ...
  ...     def render(self):
  ...         return u'<h1>Title: %s</h1>' % self.context.title

Let's now say that the `ShowTitle` content provider is shown on a page
*before* the `ChangeTitle` content provider. If we do the full rendering
process for each provider in sequence, we get the wrong result:

  >>> request = TestRequest(form={'ChangeTitle.title': u'newer title'})

  >>> viewer = ViewTitle(article, request, None)
  >>> viewer.update()
  >>> viewer.render()
  u'<h1>Title: new title</h1>'

  >>> changer = ChangeTitle(article, request, None)
  >>> changer.update()
  >>> changer.render()
  u'<input name="ChangeTitle.title" value="newer title" />'

So the correct way of doing this is to first complete phase 1 (update) for all
providers, before executing phase 2 (render):

  >>> request = TestRequest(form={'ChangeTitle.title': u'newest title'})

  >>> viewer = ViewTitle(article, request, None)
  >>> changer = ChangeTitle(article, request, None)

  >>> viewer.update()
  >>> changer.update()

  >>> viewer.render()
  u'<h1>Title: newest title</h1>'

  >>> changer.render()
  u'<input name="ChangeTitle.title" value="newest title" />'


``UpdateNotCalled`` Errors
~~~~~~~~~~~~~~~~~~~~~~~~~~

Since calling ``update()`` before any other method that mutates the provider
or any other data is so important to the correct functioning of the API, the
developer has the choice to raise the ``UpdateNotCalled`` error, if any method
is called before ``update()`` (with exception of the constructor):

  >>> class InfoBox(object):
  ...     zope.interface.implements(interfaces.IContentProvider)
  ...     zope.component.adapts(zope.interface.Interface,
  ...                           browser.IDefaultBrowserLayer,
  ...                           zope.interface.Interface)
  ...
  ...     def __init__(self, context, request, view):
  ...         self.__parent__ = view
  ...         self.__updated = False
  ...
  ...     def update(self):
  ...         self.__updated = True
  ...
  ...     def render(self):
  ...         if not self.__updated:
  ...             raise interfaces.UpdateNotCalled
  ...         return u'<div>Some information</div>'

  >>> info = InfoBox(None, None, None)

  >>> info.render()
  Traceback (most recent call last):
  ...
  UpdateNotCalled: ``update()`` was not called yet.

  >>> info.update()

  >>> info.render()
  u'<div>Some information</div>'


The TALES ``provider`` Expression
---------------------------------

The ``provider`` expression will look up the name of the content provider,
call it and return the HTML content. The first step, however, will be to
register our content provider with the component architecture:

  >>> zope.component.provideAdapter(MessageBox, name='mypage.MessageBox')

The content provider must be registered by name, since the TALES expression
uses the name to look up the provider at run time.

Let's now create a view using a page template:

  >>> import os, tempfile
  >>> temp_dir = tempfile.mkdtemp()
  >>> templateFileName = os.path.join(temp_dir, 'template.pt')
  >>> open(templateFileName, 'w').write('''
  ... <html>
  ...   <body>
  ...     <h1>My Web Page</h1>
  ...     <div class="left-column">
  ...       <tal:block replace="structure provider:mypage.MessageBox" />
  ...     </div>
  ...     <div class="main">
  ...       Content here
  ...     </div>
  ...   </body>
  ... </html>
  ... ''')

As you can see, we exprect the ``provider`` expression to simply look up the
content provider and insert the HTML content at this place.

Next we register the template as a view (browser page) for all objects:

  >>> from zope.app.pagetemplate.simpleviewclass import SimpleViewClass
  >>> FrontPage = SimpleViewClass(templateFileName, name='main.html')

  >>> zope.component.provideAdapter(
  ...     FrontPage,
  ...     (zope.interface.Interface, browser.IDefaultBrowserLayer),
  ...     zope.interface.Interface,
  ...     name='main.html')

Let's create a content object that can be viewed:

  >>> class Content(object):
  ...     zope.interface.implements(zope.interface.Interface)

  >>> content = Content()

Finally we look up the view and render it:

  >>> from zope.publisher.browser import TestRequest
  >>> request = TestRequest()

  >>> view = zope.component.getMultiAdapter((content, request),
  ...                                       name='main.html')
  >>> print view().strip()
  <html>
    <body>
      <h1>My Web Page</h1>
      <div class="left-column">
        <div class="box">My Message</div>
      </div>
      <div class="main">
        Content here
      </div>
    </body>
  </html>


Failure to lookup a Content Provider
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

If the name is not found, an error is raised. To demonstrate this behavior
let's create another template:

  >>> errorFileName = os.path.join(temp_dir, 'error.pt')
  >>> open(errorFileName, 'w').write('''
  ... <html>
  ...   <body>
  ...     <tal:block replace="structure provider:mypage.UnknownName" />
  ...   </body>
  ... </html>
  ... ''')

  >>> ErrorPage = SimpleViewClass(errorFileName, name='error.html')
  >>> zope.component.provideAdapter(
  ...     ErrorPage,
  ...     (zope.interface.Interface, browser.IDefaultBrowserLayer),
  ...     zope.interface.Interface,
  ...     name='main.html')

  >>> errorview = zope.component.getMultiAdapter((content, request),
  ...                                            name='main.html')
  >>> print errorview()
  Traceback (most recent call last):
  ...
  ContentProviderLookupError: mypage.UnknownName


Additional Data from TAL
~~~~~~~~~~~~~~~~~~~~~~~~

The ``provider`` expression allows also for transferring data from the TAL
context into the content provider. This is accomplished by having the content
provider implement an interface that specifies the attributes and provides
``ITALNamespaceData``:

  >>> import zope.schema
  >>> class IMessageText(zope.interface.Interface):
  ...     message = zope.schema.Text(title=u'Text of the message box')

  >>> zope.interface.directlyProvides(IMessageText,
  ...                                 interfaces.ITALNamespaceData)

Now the message box can receive its text from the TAL environment:

  >>> class DynamicMessageBox(MessageBox):
  ...     zope.interface.implements(IMessageText)

  >>> zope.component.provideAdapter(
  ...     DynamicMessageBox, provides=interfaces.IContentProvider,
  ...     name='mypage.DynamicMessageBox')

We are now updating our original template to provide the message text:

  >>> open(templateFileName, 'w').write('''
  ... <html>
  ...   <body>
  ...     <h1>My Web Page</h1>
  ...     <div class="left-column">
  ...       <tal:block define="message string:Hello World!"
  ...                  replace="structure provider:mypage.DynamicMessageBox" />
  ...       <tal:block define="message string:Hello World again!"
  ...                  replace="structure provider:mypage.DynamicMessageBox" />
  ...     </div>
  ...     <div class="main">
  ...       Content here
  ...     </div>
  ...   </body>
  ... </html>
  ... ''')

Now we should get two message boxes with different text:

  >>> print view().strip()
  <html>
    <body>
      <h1>My Web Page</h1>
      <div class="left-column">
        <div class="box">Hello World!</div>
        <div class="box">Hello World again!</div>
      </div>
      <div class="main">
        Content here
      </div>
    </body>
  </html>

Finally, a content provider can also implement several ``ITALNamespaceData``:

  >>> class IMessageType(zope.interface.Interface):
  ...     type = zope.schema.TextLine(title=u'The type of the message box')

  >>> zope.interface.directlyProvides(IMessageType,
  ...                                 interfaces.ITALNamespaceData)

We'll change our message box content provider implementation a bit, so the new
information is used:

  >>> class BetterDynamicMessageBox(DynamicMessageBox):
  ...     zope.interface.implements(IMessageType)
  ...     type = None
  ...
  ...     def render(self):
  ...         return u'<div class="box,%s">%s</div>' %(self.type, self.message)

  >>> zope.component.provideAdapter(
  ...     BetterDynamicMessageBox, provides=interfaces.IContentProvider,
  ...     name='mypage.MessageBox')

Of course, we also have to make our tempalte a little bit more dynamic as
well:

  >>> open(templateFileName, 'w').write('''
  ... <html>
  ...   <body>
  ...     <h1>My Web Page</h1>
  ...     <div class="left-column">
  ...       <tal:block define="message string:Hello World!;
  ...                          type string:error"
  ...                  replace="structure provider:mypage.MessageBox" />
  ...       <tal:block define="message string:Hello World again!;
  ...                          type string:warning"
  ...                  replace="structure provider:mypage.MessageBox" />
  ...     </div>
  ...     <div class="main">
  ...       Content here
  ...     </div>
  ...   </body>
  ... </html>
  ... ''')

Now we should get two message boxes with different text and types:

  >>> print view().strip()
  <html>
    <body>
      <h1>My Web Page</h1>
      <div class="left-column">
        <div class="box,error">Hello World!</div>
        <div class="box,warning">Hello World again!</div>
      </div>
      <div class="main">
        Content here
      </div>
    </body>
  </html>


You might also want to look at the ``zope.viewlet`` package for a more
featureful API.


Cleanup
-------

  >>> import shutil
  >>> shutil.rmtree(temp_dir)

