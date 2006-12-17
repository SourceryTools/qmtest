##############################################################################
#
# Copyright (c) 2001, 2002 Zope Corporation and Contributors.
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
"""Error Reporting Utility

This is a port of the Zope 2 error reporting object

$Id: error.py 41724 2006-02-21 13:27:44Z hdima $
"""
__docformat__ = 'restructuredtext'

import time
import logging
import codecs

from persistent import Persistent
from random import random
from threading import Lock

from zope.exceptions.exceptionformatter import format_exception
from zope.interface import implements

from zope.app.container.contained import Contained
from zope.app.error.interfaces import IErrorReportingUtility
from zope.app.error.interfaces import ILocalErrorReportingUtility


#Restrict the rate at which errors are sent to the Event Log
_rate_restrict_pool = {}

# The number of seconds that must elapse on average between sending two
# exceptions of the same name into the the Event Log. one per minute.
_rate_restrict_period = 60

# The number of exceptions to allow in a burst before the above limit
# kicks in. We allow five exceptions, before limiting them to one per
# minute.
_rate_restrict_burst = 5

# _temp_logs holds the logs.
_temp_logs = {}  # { oid -> [ traceback string ] }

cleanup_lock = Lock()

logger = logging.getLogger('SiteError')

def printedreplace(error):
    symbols = (ur"\x%02x" % ord(s)
        for s in error.object[error.start:error.end])
    return u"".join(symbols), error.end

codecs.register_error("zope.app.error.printedreplace", printedreplace)

def getPrintable(value):
    if not isinstance(value, unicode):
        if not isinstance(value, str):
            # A call to str(obj) could raise anything at all.
            # We'll ignore these errors, and print something
            # useful instead, but also log the error.
            try:
                value = str(value)
            except:
                logger.exception(
                    "Error in ErrorReportingUtility while getting a str"
                    " representation of an object")
                return u"<unprintable %s object>" % type(value).__name__
        value = unicode(value, errors="zope.app.error.printedreplace")
    return value

def getFormattedException(info, as_html=False):
    lines = []
    for line in format_exception(as_html=as_html, *info):
        line = getPrintable(line)
        if not line.endswith("\n"):
            if not as_html:
                line += "\n"
            else:
                line += "<br />\n"
        lines.append(line)
    return u"".join(lines)

class ErrorReportingUtility(Persistent, Contained):
    """Error Reporting Utility"""
    implements(IErrorReportingUtility, ILocalErrorReportingUtility)

    keep_entries = 20
    copy_to_zlog = 0
    _ignored_exceptions = ('Unauthorized',)


    def _getLog(self):
        """Returns the log for this object.
        Careful, the log is shared between threads.
        """
        log = _temp_logs.get(self._p_oid, None)
        if log is None:
            log = []
            _temp_logs[self._p_oid] = log
        return log

    def _getUsername(self, request):
        username = None

        principal = getattr(request, "principal", None)
        if principal is None:
            return username

        # UnauthenticatedPrincipal does not have getLogin()
        getLogin = getattr(principal, "getLogin", None)
        if getLogin is None:
            login = "unauthenticated"
        else:
            try:
                login = getLogin()
            except:
                logger.exception("Error in ErrorReportingUtility while"
                    " getting login of the principal")
                login = u"<error getting login>"

        parts = []
        for part in [
                login,
                getattr(principal, "id",
                    u"<error getting 'principal.id'>"),
                getattr(principal, "title",
                    u"<error getting 'principal.title'>"),
                getattr(principal, "description",
                    u"<error getting 'principal.description'>")
                ]:
            part = getPrintable(part)
            parts.append(part)
        username = u", ".join(parts)
        return username

    def _getRequestAsHTML(self, request):
        lines = []
        for key, value in request.items():
            lines.append(u"%s: %s<br />\n" % (
                getPrintable(key), getPrintable(value)))
        return u"".join(lines)

    # Exceptions that happen all the time, so we dont need
    # to log them. Eventually this should be configured
    # through-the-web.
    def raising(self, info, request=None):
        """Log an exception.
        Called by ZopePublication.handleException method.
        """
        now = time.time()
        try:
            strtype = unicode(getattr(info[0], '__name__', info[0]))
            if strtype in self._ignored_exceptions:
                return

            tb_text = None
            tb_html = None
            if not isinstance(info[2], basestring):
                tb_text = getFormattedException(info)
                tb_html = getFormattedException(info, True)
            else:
                tb_text = getPrintable(info[2])

            url = None
            username = None
            req_html = None
            if request:
                # TODO: Temporary fix, which Steve should undo. URL is
                #      just too HTTPRequest-specific.
                if hasattr(request, 'URL'):
                    url = request.URL
                username = self._getUsername(request)
                req_html = self._getRequestAsHTML(request)

            strv = getPrintable(info[1])

            log = self._getLog()
            entry_id = str(now) + str(random()) # Low chance of collision

            log.append({
                'type': strtype,
                'value': strv,
                'time': time.ctime(now),
                'id': entry_id,
                'tb_text': tb_text,
                'tb_html': tb_html,
                'username': username,
                'url': url,
                'req_html': req_html,
                })
            cleanup_lock.acquire()
            try:
                if len(log) >= self.keep_entries:
                    del log[:-self.keep_entries]
            finally:
                cleanup_lock.release()

            if self.copy_to_zlog:
                self._do_copy_to_zlog(now, strtype, str(url), info)
        finally:
            info = None

    def _do_copy_to_zlog(self, now, strtype, url, info):
        # info is unused; logging.exception() will call sys.exc_info()
        # work around this with an evil hack
        when = _rate_restrict_pool.get(strtype,0)
        if now > when:
            next_when = max(when,
                            now - _rate_restrict_burst * _rate_restrict_period)
            next_when += _rate_restrict_period
            _rate_restrict_pool[strtype] = next_when
            try:
                raise info[0], info[1], info[2]
            except:
                logger.exception(str(url))

    def getProperties(self):
        return {
            'keep_entries': self.keep_entries,
            'copy_to_zlog': self.copy_to_zlog,
            'ignored_exceptions': self._ignored_exceptions,
            }

    def setProperties(self, keep_entries, copy_to_zlog=0,
                      ignored_exceptions=()):
        """Sets the properties of this site error log.
        """
        self.keep_entries = int(keep_entries)
        self.copy_to_zlog = bool(copy_to_zlog)
        self._ignored_exceptions = tuple(
                [unicode(e) for e in ignored_exceptions if e]
                )

    def getLogEntries(self):
        """Returns the entries in the log, most recent first.

        Makes a copy to prevent changes.
        """
        res = [entry.copy() for entry in self._getLog()]
        res.reverse()
        return res

    def getLogEntryById(self, id):
        """Returns the specified log entry.
        Makes a copy to prevent changes.  Returns None if not found.
        """
        for entry in self._getLog():
            if entry['id'] == id:
                return entry.copy()
        return None

class RootErrorReportingUtility(ErrorReportingUtility):
    rootId = 'root'

    def _getLog(self):
        """Returns the log for this object.

        Careful, the log is shared between threads.
        """
        log = _temp_logs.get(self.rootId, None)
        if log is None:
            log = []
            _temp_logs[self.rootId] = log
        return log


globalErrorReportingUtility = RootErrorReportingUtility()

def _cleanup_temp_log():
    _temp_logs.clear()

_clear = _cleanup_temp_log

# Register our cleanup with Testing.CleanUp to make writing unit tests simpler.
from zope.testing.cleanup import addCleanUp
addCleanUp(_clear)
del addCleanUp
