##############################################################################
#
# Copyright (c) 2005 Zope Corporation and Contributors.
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
"""Retrieve Static APIDOC

$Id$
"""
__docformat__ = "reStructuredText"

import base64
import os
import sys
import time
import optparse
import urllib2
import warnings
import HTMLParser

import zope.testbrowser
import mechanize

from zope.app.testing import functional

from zope.app.apidoc import classregistry

VERBOSITY_MAP = {1: 'ERROR', 2: 'WARNING', 3: 'INFO'}

# A mapping of HTML elements that can contain links to the attribute that
# actually contains the link
urltags = {
    "a": "href",
    "area": "href",
    "frame": "src",
    "iframe": "src",
    "link": "href",
    "img": "src",
    "script": "src",
}

def getMaxWidth():
    try:
        import curses
    except ImportError:
        pass
    else:
        try:
            curses.setupterm()
            cols = curses.tigetnum('cols')
            if cols > 0:
                return cols
        except curses.error:
            pass
    return 80

def cleanURL(url):
    """Clean a URL from parameters."""
    if '?' in url:
        url = url.split('?')[0]
    if '#' in url:
        url = url.split('#')[0]
    return url

def completeURL(url):
    """Add file to URL, if not provided."""
    if url.endswith('/'):
        url += 'index.html'
    if '.' not in url.split('/')[-1]:
        url += '/index.html'
    filename = url.split('/')[-1]
    if filename.startswith('@@'):
        url = url.replace(filename, filename[2:])
    return url


class Link(object):
    """A link in the page."""

    def __init__(self, mechLink, rootURL, referenceURL='None'):
        self.rootURL = rootURL
        self.referenceURL = referenceURL
        self.originalURL = mechLink.url
        self.callableURL = mechLink.absolute_url
        self.url = completeURL(cleanURL(mechLink.url))
        self.absoluteURL = completeURL(cleanURL(mechLink.absolute_url))

    def isLocalURL(self):
        """Determine whether the passed in URL is local and accessible."""
        # Javascript function call
        if self.url.startswith('javascript:'):
            return False
        # Mail Link
        if self.url.startswith('mailto:'):
            return False
        # External Link
        if self.url.startswith('http://') and \
               not self.url.startswith(self.rootURL):
            return False
        return True

    def isApidocLink(self):
        # Make sure that only apidoc links are loaded
        if self.absoluteURL.startswith(self.rootURL+'++apidoc++/'):
            return True
        if self.absoluteURL.startswith(self.rootURL+'@@/'):
            return True
        return False


class OnlineBrowser(mechanize.Browser, object):

    def setUserAndPassword(self, user, pw):
        """Specify the username and password to use for the retrieval."""
        hash = base64.encodestring(user+':'+pw).strip()
        self.addheaders.append(('Authorization', 'Basic '+hash))

    @property
    def contents(self):
        """Get the content of the returned data"""
        response = self.response()
        old_location = response.tell()
        response.seek(0)
        contents = response.read()
        response.seek(old_location)
        return contents


class PublisherBrowser(zope.testbrowser.testing.PublisherMechanizeBrowser,
                       object):

    def __init__(self, *args, **kw):
        functional.Functional.setUp()
        super(PublisherBrowser, self).__init__(*args, **kw)

    def setUserAndPassword(self, user, pw):
        """Specify the username and password to use for the retrieval."""
        self.addheaders.append(('Authorization', 'Basic %s:%s' %(user, pw)))

    @property
    def contents(self):
        """Get the content of the returned data"""
        response = self.response()
        old_location = response.tell()
        response.seek(0)
        # Remove HTTP Headers
        for line in iter(lambda: response.readline().strip(), ''):
            pass
        contents = response.read()
        response.seek(old_location)
        return contents


class StaticAPIDocGenerator(object):
    """Static API doc Maker"""

    def __init__(self, options):
        self.options = options
        self.linkQueue = []
        for url in self.options.additional_urls + [self.options.startpage]:
            link = Link(mechanize.Link(self.options.url, url, '', '', ()),
                        self.options.url)
            self.linkQueue.append(link)
        self.rootDir = os.path.join(os.path.dirname(__file__),
                                    self.options.target_dir)
        self.maxWidth = getMaxWidth()-13
        self.needNewLine = False

    def start(self):
        """Start the retrieval of the apidoc."""
        t0 = time.time()

        self.visited = []
        self.counter = 0
        self.linkErrors = 0
        self.htmlErrors = 0

        # Turn off deprecation warnings
        warnings.filterwarnings("ignore", category=DeprecationWarning)

        if not os.path.exists(self.rootDir):
            os.mkdir(self.rootDir)

        if self.options.use_publisher:
            self.browser = PublisherBrowser()

        if self.options.use_webserver:
            self.browser = OnlineBrowser()

        self.browser.setUserAndPassword(self.options.username,
                                        self.options.password)
        self.browser._links_factory.urltags = urltags

        if self.options.debug:
            self.browser.addheaders.append(('X-zope-handle-errors', False))

        classregistry.IGNORE_MODULES = self.options.ignore_modules

        if self.options.import_unknown_modules:
            classregistry.__import_unknown_modules__ = True

        # Work through all links until there are no more to work on.
        self.sendMessage('Starting retrieval.')
        while self.linkQueue:
            link = self.linkQueue.pop()
            # Sometimes things are placed many times into the queue, for example
            # if the same link appears twice in a page. In those cases, we can
            # check at this point whether the URL has been already handled.
            if link.absoluteURL not in self.visited:
                self.showProgress(link)
                self.processLink(link)

        t1 = time.time()

        self.sendMessage("Run time: %.3f sec" % (t1-t0))
        self.sendMessage("Links: %i" %self.counter)
        self.sendMessage("Link Retrieval Errors: %i" %self.linkErrors)
        self.sendMessage("HTML ParsingErrors: %i" %self.htmlErrors)

    def showProgress(self, link):
        self.counter += 1
        if self.options.progress:
            url = link.absoluteURL[-(self.maxWidth):]
            sys.stdout.write('\r' + ' '*(self.maxWidth+13))
            sys.stdout.write('\rLink %5d: %s' % (self.counter, url))
            sys.stdout.flush()
            self.needNewLine = True

    def sendMessage(self, msg, verbosity=4):
        if self.options.verbosity >= verbosity:
            if self.needNewLine:
                sys.stdout.write('\n')
            sys.stdout.write(VERBOSITY_MAP.get(verbosity, 'INFO')+': ')
            sys.stdout.write(msg)
            sys.stdout.write('\n')
            sys.stdout.flush()
            self.needNewLine = False

    def processLink(self, link):
        """Process a link."""
        url = link.absoluteURL

        # Whatever will happen, we have looked at the URL
        self.visited.append(url)

        # Retrieve the content
        try:
            self.browser.open(link.callableURL)
        except urllib2.HTTPError, error:
            # Something went wrong with retrieving the page.
            self.linkErrors += 1
            self.sendMessage(
                '%s (%i): %s' % (error.msg, error.code, link.callableURL), 2)
            self.sendMessage('+-> Reference: ' + link.referenceURL, 2)
            # Now set the error page as the response
            from ClientCookie._Util import response_seek_wrapper
            self.browser._response = response_seek_wrapper(error)
        except (urllib2.URLError, ValueError):
            # We had a bad URL running the publisher browser
            self.linkErrors += 1
            self.sendMessage('Bad URL: ' + link.callableURL, 2)
            self.sendMessage('+-> Reference: ' + link.referenceURL, 2)
            return
        except Exception, error:
            # This should never happen outside the debug mode. We really want
            # to catch all exceptions, so that we can investigate them.
            if self.options.debug:
                import pdb; pdb.set_trace()
            return

        # Get the response content
        contents = self.browser.contents

        # Make sure the directory exists and get a file path.
        relativeURL = url.replace(self.options.url, '')
        dir = self.rootDir
        segments = relativeURL.split('/')
        filename = segments.pop()

        for segment in segments:
            dir = os.path.join(dir, segment)
            if not os.path.exists(dir):
                os.mkdir(dir)

        filepath = os.path.join(dir, filename)

        # Now retrieve all links
        if self.browser.viewing_html():

            try:
                links = self.browser.links()
            except HTMLParser.HTMLParseError, error:
                self.htmlErrors += 1
                self.sendMessage('Failed to parse HTML: ' + url, 1)
                self.sendMessage('+-> %s: line %i, column %s' % (
                    error.msg, error.lineno, error.offset), 1)
                links = []

            links = [Link(mech_link, self.options.url, url)
                     for mech_link in links]

            for link in links:
                # Make sure we do not handle unwanted links.
                if not (link.isLocalURL() and link.isApidocLink()):
                    continue

                # Add link to the queue
                if link.absoluteURL not in self.visited:
                    self.linkQueue.insert(0, link)

                # Rewrite URLs
                parts = ['..']*len(segments)
                parts.append(link.absoluteURL.replace(self.options.url, ''))
                contents = contents.replace(link.originalURL, '/'.join(parts))

        # Write the data into the file
        try:
            file = open(filepath, 'w')
            file.write(contents)
            file.close()
        except IOError:
            # The file already exists, so it is a duplicate and a bad one,
            # since the URL misses `index.hml`. ReST can produce strange URLs
            # that produce this problem, and we have little control over it.
            pass

        # Cleanup; this is very important, otherwise we are opening too many
        # files.
        self.browser.close()


###############################################################################
# Command-line UI

parser = optparse.OptionParser("%prog [options] TARGET_DIR")

######################################################################
# Retrieval

retrieval = optparse.OptionGroup(
    parser, "Retrieval", "Options that deal with setting up the generator")

retrieval.add_option(
    '--publisher', '-p', action="store_true", dest='use_publisher',
    help="""\
Use the publisher directly to retrieve the data. The program will bring up
Zope 3 for you.
""")

retrieval.add_option(
    '--webserver', '-w', action="store_true", dest='use_webserver',
    help="""\
Use and external Web server that is connected to Zope 3.
""")

retrieval.add_option(
    '--url', '-u', action="store", dest='url',
    help="""\
The URL that will be used to retrieve the HTML pages. This option is
meaningless, if you are using the publisher as backend. Also, the value of
this option should *not* include the `++apidoc++` namespace.
""")

retrieval.add_option(
    '--startpage', '-s', action="store", dest='startpage',
    help="""\
The startpage specifies the path (after the URL) that is used as the starting
point to retrieve the contents. The default is `++apidoc++/static.html`. This
option can be very useful for debugging, since it allows you to select
specific pages.
""")

retrieval.add_option(
    '--username', '--user', action="store", dest='username',
    help="""\
Username to access the Web site.
""")

retrieval.add_option(
    '--password', '--pwd', action="store", dest='password',
    help="""\
Password to access the Web site.
""")

retrieval.add_option(
    '--add', '-a', action="append", dest='additional_urls',
    help="""\
Add an additional URL to the list of URLs to retrieve. Specifying those is
sometimes necessary, if the links are hidden in cryptic JAvascript code.
""")

retrieval.add_option(
    '--ignore', '-i', action="append", dest='ignore_modules',
    help="""\
Add modules that should be ignored during retrieval. That allows you to limit
the scope of the generated API documentation.
""")

retrieval.add_option(
    '--load-all', '-l', action="store_true", dest='import_unknown_modules',
    help="""\
Retrieve all referenced modules, even if they have not been imported during
the startup process.
""")

parser.add_option_group(retrieval)

######################################################################
# Reporting

reporting = optparse.OptionGroup(
    parser, "Reporting", "Options that configure the user output information.")

reporting.add_option(
    '--verbosity', '-v', type="int", dest='verbosity',
    help="""\
Specifies the reporting detail level.
""")

reporting.add_option(
    '--progress', '-b', action="store_true", dest='progress',
    help="""\
Output progress status
""")

reporting.add_option(
    '--debug', '-d', action="store_true", dest='debug',
    help="""\
Run in debug mode. This will allow you to use the debugger, if the publisher
experienced an error.
""")

parser.add_option_group(reporting)

######################################################################
# Command-line processing

# Default setup
default_setup_args = [
    '--verbosity', 5,
    '--publisher',
    '--url', 'http://localhost:8080/',
    '--startpage', '++apidoc++/static.html',
    '--username', 'mgr',
    '--password', 'mgrpw',
    '--progress',
    '--add', '@@/varrow.png',
    '--add', '@@/harrow.png',
    '--add', '@@/tree_images/minus.png',
    '--add', '@@/tree_images/plus.png',
    '--add', '@@/tree_images/minus_vline.png',
    '--add', '@@/tree_images/plus_vline.png',
    '--ignore', 'twisted',
    '--ignore', 'zope.app.twisted.ftp.test',
    '--load-all'
    ]

def merge_options(options, defaults):
    odict = options.__dict__
    for name, value in defaults.__dict__.items():
        if (value is not None) and (odict[name] is None):
            odict[name] = value

def get_options(args=None, defaults=None):

    default_setup, _ = parser.parse_args(default_setup_args)
    assert not _
    if defaults:
        defaults, _ = parser.parse_args(defaults)
        assert not _
        merge_options(defaults, default_setup)
    else:
        defaults = default_setup

    if args is None:
        args = sys.argv
    original_testrunner_args = args
    args = args[1:]
    options, positional = parser.parse_args(args)
    merge_options(options, defaults)
    options.original_testrunner_args = original_testrunner_args

    if not positional:
        parser.error("No target directory specified.")
    options.target_dir = positional.pop()

    return options

# Command-line UI
###############################################################################


def main():
    options = get_options()
    maker = StaticAPIDocGenerator(options)
    maker.start()
    sys.exit(0)

if __name__ == '__main__':
    main()
