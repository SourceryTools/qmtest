"""Stateful programmatic WWW navigation, after Perl's WWW::Mechanize.

Copyright 2003-2006 John J. Lee <jjl@pobox.com>
Copyright 2003 Andy Lester (original Perl code)

This code is free software; you can redistribute it and/or modify it
under the terms of the BSD or ZPL 2.1 licenses (see the file COPYING.txt
included with the distribution).

"""

import urllib2, urlparse, sys, copy, re

from _useragent import UserAgent
from _html import DefaultFactory
from _util import response_seek_wrapper, closeable_response
import _request

__version__ = (0, 1, 2, "b", None)  # 0.1.2b

class BrowserStateError(Exception): pass
class LinkNotFoundError(Exception): pass
class FormNotFoundError(Exception): pass


class History:
    """

    Though this will become public, the implied interface is not yet stable.

    """
    def __init__(self):
        self._history = []  # LIFO
    def add(self, request, response):
        self._history.append((request, response))
    def back(self, n, _response):
        response = _response  # XXX move Browser._response into this class?
        while n > 0 or response is None:
            try:
                request, response = self._history.pop()
            except IndexError:
                raise BrowserStateError("already at start of history")
            n -= 1
        return request, response
    def clear(self):
        del self._history[:]
    def close(self):
        """
            If nothing has been added, .close should work.

                >>> history = History()
                >>> history.close()

            Under some circumstances response can be None, in that case
            this method should not raise an exception.

                >>> history.add(None, None)
                >>> history.close()
        """
        for request, response in self._history:
            if response is not None:
                response.close()
        del self._history[:]

# Horrible, but needed, at least until fork urllib2.  Even then, may want
# to preseve urllib2 compatibility.
def upgrade_response(response):
    # a urllib2 handler constructed the response, i.e. the response is an
    # urllib.addinfourl, instead of a _Util.closeable_response as returned
    # by e.g. mechanize.HTTPHandler
    try:
        code = response.code
    except AttributeError:
        code = None
    try:
        msg = response.msg
    except AttributeError:
        msg = None

    # may have already-.read() data from .seek() cache
    data = None
    get_data = getattr(response, "get_data", None)
    if get_data:
        data = get_data()

    response = closeable_response(
        response.fp, response.info(), response.geturl(), code, msg)
    response = response_seek_wrapper(response)
    if data:
        response.set_data(data)
    return response
class ResponseUpgradeProcessor(urllib2.BaseHandler):
    # upgrade responses to be .close()able without becoming unusable
    handler_order = 0  # before anything else
    def any_response(self, request, response):
        if not hasattr(response, 'closeable_response'):
            response = upgrade_response(response)
        return response


class Browser(UserAgent):
    """Browser-like class with support for history, forms and links.

    BrowserStateError is raised whenever the browser is in the wrong state to
    complete the requested operation - eg., when .back() is called when the
    browser history is empty, or when .follow_link() is called when the current
    response does not contain HTML data.

    Public attributes:

    request: current request (mechanize.Request or urllib2.Request)
    form: currently selected form (see .select_form())

    """

    handler_classes = UserAgent.handler_classes.copy()
    handler_classes["_response_upgrade"] = ResponseUpgradeProcessor
    default_others = copy.copy(UserAgent.default_others)
    default_others.append("_response_upgrade")

    def __init__(self,
                 factory=None,
                 history=None,
                 request_class=None,
                 ):
        """

        Only named arguments should be passed to this constructor.

        factory: object implementing the mechanize.Factory interface.
        history: object implementing the mechanize.History interface.  Note this
         interface is still experimental and may change in future.
        request_class: Request class to use.  Defaults to mechanize.Request
         by default for Pythons older than 2.4, urllib2.Request otherwise.

        The Factory and History objects passed in are 'owned' by the Browser,
        so they should not be shared across Browsers.  In particular,
        factory.set_response() should not be called except by the owning
        Browser itself.

        Note that the supplied factory's request_class is overridden by this
        constructor, to ensure only one Request class is used.

        """
        if history is None:
            history = History()
        self._history = history
        self.request = self._response = None
        self.form = None

        if request_class is None:
            if not hasattr(urllib2.Request, "add_unredirected_header"):
                request_class = _request.Request
            else:
                request_class = urllib2.Request  # Python >= 2.4

        if factory is None:
            factory = DefaultFactory()
        factory.set_request_class(request_class)
        self._factory = factory
        self.request_class = request_class

        UserAgent.__init__(self)  # do this last to avoid __getattr__ problems

    def close(self):
        if self._response is not None:
            self._response.close()    
        UserAgent.close(self)
        if self._history is not None:
            self._history.close()
            self._history = None
        self.request = self._response = None

    def open(self, url, data=None):
        if self._response is not None:
            self._response.close()
        return self._mech_open(url, data)

    def _mech_open(self, url, data=None, update_history=True):
        try:
            url.get_full_url
        except AttributeError:
            # string URL -- convert to absolute URL if required
            scheme, netloc = urlparse.urlparse(url)[:2]
            if not scheme:
                # relative URL
                assert not netloc, "malformed URL"
                if self._response is None:
                    raise BrowserStateError(
                        "can't fetch relative URL: not viewing any document")
                url = urlparse.urljoin(self._response.geturl(), url)

        if self.request is not None and update_history:
            self._history.add(self.request, self._response)
        self._response = None
        # we want self.request to be assigned even if UserAgent.open fails
        self.request = self._request(url, data)
        self._previous_scheme = self.request.get_type()

        success = True
        try:
            response = UserAgent.open(self, self.request, data)
        except urllib2.HTTPError, error:
            success = False
            response = error
##         except (IOError, socket.error, OSError), error:
##             # Yes, urllib2 really does raise all these :-((
##             # See test_urllib2.py for examples of socket.gaierror and OSError,
##             # plus note that FTPHandler raises IOError.
##             # XXX I don't seem to have an example of exactly socket.error being
##             #  raised, only socket.gaierror...
##             # I don't want to start fixing these here, though, since this is a
##             # subclass of OpenerDirector, and it would break old code.  Even in
##             # Python core, a fix would need some backwards-compat. hack to be
##             # acceptable.
##             raise
        self.set_response(response)
        if not success:
            raise error
        return copy.copy(self._response)

    def __str__(self):
        text = []
        text.append("<%s " % self.__class__.__name__)
        if self._response:
            text.append("visiting %s" % self._response.geturl())
        else:
            text.append("(not visiting a URL)")
        if self.form:
            text.append("\n selected form:\n %s\n" % str(self.form))
        text.append(">")
        return "".join(text)

    def response(self):
        """Return a copy of the current response.

        The returned object has the same interface as the object returned by
        .open() (or urllib2.urlopen()).

        """
        return copy.copy(self._response)

    def set_response(self, response):
        """Replace current response with (a copy of) response."""
        # sanity check, necessary but far from sufficient
        if not (hasattr(response, "info") and hasattr(response, "geturl") and
                hasattr(response, "read")):
            raise ValueError("not a response object")

        self.form = None

        if not hasattr(response, "seek"):
            response = response_seek_wrapper(response)
        if not hasattr(response, "closeable_response"):
            response = upgrade_response(response)
        else:
            response = copy.copy(response)

        self._response = response
        self._factory.set_response(self._response)

    def geturl(self):
        """Get URL of current document."""
        if self._response is None:
            raise BrowserStateError("not viewing any document")
        return self._response.geturl()

    def reload(self):
        """Reload current document, and return response object."""
        if self.request is None:
            raise BrowserStateError("no URL has yet been .open()ed")
        if self._response is not None:
            self._response.close()
        return self._mech_open(self.request, update_history=False)

    def back(self, n=1):
        """Go back n steps in history, and return response object.

        n: go back this number of steps (default 1 step)

        """
        if self._response is not None:
            self._response.close()
        self.request, response = self._history.back(n, self._response)
        self.set_response(response)
        return response

    def clear_history(self):
        self._history.clear()

    def links(self, **kwds):
        """Return iterable over links (mechanize.Link objects)."""
        if not self.viewing_html():
            raise BrowserStateError("not viewing HTML")
        links = self._factory.links()
        if kwds:
            return self._filter_links(links, **kwds)
        else:
            return links

    def forms(self):
        """Return iterable over forms.

        The returned form objects implement the ClientForm.HTMLForm interface.

        """
        if not self.viewing_html():
            raise BrowserStateError("not viewing HTML")
        return self._factory.forms()

    def viewing_html(self):
        """Return whether the current response contains HTML data."""
        if self._response is None:
            raise BrowserStateError("not viewing any document")
        return self._factory.is_html

    def encoding(self):
        """"""
        if self._response is None:
            raise BrowserStateError("not viewing any document")
        return self._factory.encoding

    def title(self):
        """Return title, or None if there is no title element in the document.

        Tags are stripped or textified as described in docs for
        PullParser.get_text() method of pullparser module.

        """
        if not self.viewing_html():
            raise BrowserStateError("not viewing HTML")
        return self._factory.title

    def select_form(self, name=None, predicate=None, nr=None):
        """Select an HTML form for input.

        This is a bit like giving a form the "input focus" in a browser.

        If a form is selected, the Browser object supports the HTMLForm
        interface, so you can call methods like .set_value(), .set(), and
        .click().

        At least one of the name, predicate and nr arguments must be supplied.
        If no matching form is found, mechanize.FormNotFoundError is raised.

        If name is specified, then the form must have the indicated name.

        If predicate is specified, then the form must match that function.  The
        predicate function is passed the HTMLForm as its single argument, and
        should return a boolean value indicating whether the form matched.

        nr, if supplied, is the sequence number of the form (where 0 is the
        first).  Note that control 0 is the first form matching all the other
        arguments (if supplied); it is not necessarily the first control in the
        form.

        """
        if not self.viewing_html():
            raise BrowserStateError("not viewing HTML")
        if (name is None) and (predicate is None) and (nr is None):
            raise ValueError(
                "at least one argument must be supplied to specify form")

        orig_nr = nr
        for form in self.forms():
            if name is not None and name != form.name:
                continue
            if predicate is not None and not predicate(form):
                continue
            if nr:
                nr -= 1
                continue
            self.form = form
            break  # success
        else:
            # failure
            description = []
            if name is not None: description.append("name '%s'" % name)
            if predicate is not None:
                description.append("predicate %s" % predicate)
            if orig_nr is not None: description.append("nr %d" % orig_nr)
            description = ", ".join(description)
            raise FormNotFoundError("no form matching "+description)

    def _add_referer_header(self, request, origin_request=True):
        if self.request is None:
            return request
        scheme = request.get_type()
        original_scheme = self.request.get_type()
        if scheme not in ["http", "https"]:
            return request
        if not origin_request and not self.request.has_header("Referer"):
            return request

        if (self._handle_referer and
            original_scheme in ["http", "https"] and
            not (original_scheme == "https" and scheme != "https")):
            # strip URL fragment (RFC 2616 14.36)
            parts = urlparse.urlparse(self.request.get_full_url())
            parts = parts[:-1]+("",)
            referer = urlparse.urlunparse(parts)
            request.add_unredirected_header("Referer", referer)
        return request

    def click(self, *args, **kwds):
        """See ClientForm.HTMLForm.click for documentation."""
        if not self.viewing_html():
            raise BrowserStateError("not viewing HTML")
        request = self.form.click(*args, **kwds)
        return self._add_referer_header(request)

    def submit(self, *args, **kwds):
        """Submit current form.

        Arguments are as for ClientForm.HTMLForm.click().

        Return value is same as for Browser.open().

        """
        return self.open(self.click(*args, **kwds))

    def click_link(self, link=None, **kwds):
        """Find a link and return a Request object for it.

        Arguments are as for .find_link(), except that a link may be supplied
        as the first argument.

        """
        if not self.viewing_html():
            raise BrowserStateError("not viewing HTML")
        if not link:
            link = self.find_link(**kwds)
        else:
            if kwds:
                raise ValueError(
                    "either pass a Link, or keyword arguments, not both")
        request = self.request_class(link.absolute_url)
        return self._add_referer_header(request)

    def follow_link(self, link=None, **kwds):
        """Find a link and .open() it.

        Arguments are as for .click_link().

        Return value is same as for Browser.open().

        """
        return self.open(self.click_link(link, **kwds))

    def find_link(self, **kwds):
        """Find a link in current page.

        Links are returned as mechanize.Link objects.

        # Return third link that .search()-matches the regexp "python"
        # (by ".search()-matches", I mean that the regular expression method
        # .search() is used, rather than .match()).
        find_link(text_regex=re.compile("python"), nr=2)

        # Return first http link in the current page that points to somewhere
        # on python.org whose link text (after tags have been removed) is
        # exactly "monty python".
        find_link(text="monty python",
                  url_regex=re.compile("http.*python.org"))

        # Return first link with exactly three HTML attributes.
        find_link(predicate=lambda link: len(link.attrs) == 3)

        Links include anchors (<a>), image maps (<area>), and frames (<frame>,
        <iframe>).

        All arguments must be passed by keyword, not position.  Zero or more
        arguments may be supplied.  In order to find a link, all arguments
        supplied must match.

        If a matching link is not found, mechanize.LinkNotFoundError is raised.

        text: link text between link tags: eg. <a href="blah">this bit</a> (as
         returned by pullparser.get_compressed_text(), ie. without tags but
         with opening tags "textified" as per the pullparser docs) must compare
         equal to this argument, if supplied
        text_regex: link text between tag (as defined above) must match the
         regular expression object or regular expression string passed as this
         argument, if supplied
        name, name_regex: as for text and text_regex, but matched against the
         name HTML attribute of the link tag
        url, url_regex: as for text and text_regex, but matched against the
         URL of the link tag (note this matches against Link.url, which is a
         relative or absolute URL according to how it was written in the HTML)
        tag: element name of opening tag, eg. "a"
        predicate: a function taking a Link object as its single argument,
         returning a boolean result, indicating whether the links
        nr: matches the nth link that matches all other criteria (default 0)

        """
        try:
            return self._filter_links(self._factory.links(), **kwds).next()
        except StopIteration:
            raise LinkNotFoundError()

    def __getattr__(self, name):
        # pass through ClientForm / DOMForm methods and attributes
        form = self.__dict__.get("form")
        if form is None:
            raise AttributeError(
                "%s instance has no attribute %s (perhaps you forgot to "
                ".select_form()?)" % (self.__class__, name))
        return getattr(form, name)

#---------------------------------------------------
# Private methods.

    def _filter_links(self, links,
                    text=None, text_regex=None,
                    name=None, name_regex=None,
                    url=None, url_regex=None,
                    tag=None,
                    predicate=None,
                    nr=0
                    ):
        if not self.viewing_html():
            raise BrowserStateError("not viewing HTML")

        found_links = []
        orig_nr = nr

        for link in links:
            if url is not None and url != link.url:
                continue
            if url_regex is not None and not re.search(url_regex, link.url):
                continue
            if (text is not None and
                (link.text is None or text != link.text)):
                continue
            if (text_regex is not None and
                (link.text is None or not re.search(text_regex, link.text))):
                continue
            if name is not None and name != dict(link.attrs).get("name"):
                continue
            if name_regex is not None:
                link_name = dict(link.attrs).get("name")
                if link_name is None or not re.search(name_regex, link_name):
                    continue
            if tag is not None and tag != link.tag:
                continue
            if predicate is not None and not predicate(link):
                continue
            if nr:
                nr -= 1
                continue
            yield link
            nr = orig_nr
