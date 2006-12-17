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
"""Synchronize with Foreign Translation Domains

$Id: synchronize.py 39064 2005-10-11 18:40:10Z philikon $
"""
__docformat__ = 'restructuredtext'

import httplib
import urllib
import xmlrpclib
from base64 import encodestring

from zope.security.proxy import removeSecurityProxy

from zope.app.i18n.browser import BaseView
from zope.app.i18n import ZopeMessageFactory as _

DEFAULT = 'http://localhost:8080/++etc++site/default/zope'

class Synchronize(BaseView):

    messageStatus = [_('Up to Date'), _('New Remote'), _('Out of Date'),
                     _('Newer Local'), _('Does not exist')]

    def __init__(self, context, request):
        super(Synchronize, self).__init__(context, request)

        self.sync_url = self.request.cookies.get(
            'sync_url', DEFAULT)
        self.sync_url = urllib.unquote(self.sync_url)
        self.sync_username = self.request.cookies.get('sync_username', 'admin')
        self.sync_password = self.request.cookies.get('sync_password', 'admin')
        self.sync_languages = filter(None, self.request.cookies.get(
            'sync_languages', '').split(','))


    def _connect(self):
        '''Connect to the remote server via XML-RPC HTTP; return status'''
        # make sure the URL contains the http:// prefix
        if not self.sync_url.startswith('http://'):
            url = 'http://' + self.sync_url
        else:
            url = self.sync_url

        # Now try to connect
        self._connection = xmlrpclib.Server(
            url, transport = BasicAuthTransport(self.sync_username,
                                                self.sync_password))

        # check whether the connection was made and the Master Babel Tower
        # exists
        try:
            self._connection.getAllLanguages()
            return 1
        except:
            self._connection = None
            return 0


    def _disconnect(self):
        '''Disconnect from the sever; return ``None``'''
        if hasattr(self, '_connection') and self._connection is not None:
            self._connection = None


    def _isConnected(self):
        '''Check whether we are currently connected to the server; return
        boolean'''
        if not hasattr(self, '_connection'):
            self._connection = None

        if not self._connection is None and self._connection.getAllLanguages():
            return 1
        else:
            return 0


    def canConnect(self):
        '''Checks whether we can connect using this server and user data;
        return boolean'''
        if self._isConnected():
            return 1
        else:
            try:
                return self._connect()
            except:
                return 0


    def getAllLanguages(self):
        connected = self._isConnected()
        if not connected: connected = self._connect()

        if connected:
            return self._connection.getAllLanguages()
        else:
            return []



    def queryMessages(self):
        connected = self._isConnected()
        if not connected: connected = self._connect()

        if connected:
            fmsgs = self._connection.getMessagesFor(self.sync_languages)
        else:
            fmsgs = []

        return self.context.getMessagesMapping(self.sync_languages,
                                               fmsgs)

    def queryMessageItems(self):
        items = self.queryMessages().items()
        items = removeSecurityProxy(items)
        items.sort(lambda x, y: cmp(x[0][0] + x[0][1], y[0][0]+y[0][1]))
        return items

    def getStatus(self, fmsg, lmsg, verbose=1):
        state = 0
        if fmsg is None:
            state = 4
        elif lmsg is None:
            state = 1
        elif fmsg['mod_time'] > lmsg['mod_time']:
            state = 2
        elif fmsg['mod_time'] < lmsg['mod_time']:
            state = 3
        elif fmsg['mod_time'] == lmsg['mod_time']:
            state = 0

        if verbose:
            return self.messageStatus[state]
        return state


    def saveSettings(self):
        self.sync_languages = self.request.form.get('sync_languages', [])
        self.request.response.setCookie('sync_languages',
                                             ','.join(self.sync_languages))
        self.request.response.setCookie('sync_url',
                            urllib.quote(self.request['sync_url']).strip())
        self.request.response.setCookie('sync_username',
                                             self.request['sync_username'])
        self.request.response.setCookie('sync_password',
                                             self.request['sync_password'])

        return self.request.response.redirect(self.request.URL[-1]+
                                                   '/@@synchronizeForm.html')


    def synchronize(self):
        mapping = self.queryMessages()
        self.context.synchronize(mapping)
        return self.request.response.redirect(self.request.URL[-1]+
                                                   '/@@synchronizeForm.html')


    def synchronizeMessages(self):
        idents = []
        for id in self.request.form['message_ids']:
            msgid = self.request.form['update-msgid-'+id]
            language = self.request.form['update-language-'+id]
            idents.append((msgid, language))

        mapping = self.queryMessages()
        new_mapping = {}
        for item in mapping.items():
            if item[0] in idents:
                new_mapping[item[0]] = item[1]

        self.context.synchronize(new_mapping)
        return self.request.response.redirect(self.request.URL[-1]+
                                                   '/@@synchronizeForm.html')



class BasicAuthTransport(xmlrpclib.Transport):
    def __init__(self, username=None, password=None, verbose=0):
        self.username=username
        self.password=password
        self.verbose=verbose

    def request(self, host, handler, request_body, verbose=0):
        # issue XML-RPC request

        self.verbose = verbose

        h = httplib.HTTP(host)
        h.putrequest("POST", handler)

        # required by HTTP/1.1
        h.putheader("Host", host)

        # required by XML-RPC
        h.putheader("User-Agent", self.user_agent)
        h.putheader("Content-Type", "text/xml")
        h.putheader("Content-Length", str(len(request_body)))

        # basic auth
        if self.username is not None and self.password is not None:
            h.putheader("AUTHORIZATION", "Basic %s" %
                        encodestring("%s:%s" % (self.username, self.password)
                                     ).replace("\012", ""))
        h.endheaders()

        if request_body:
            h.send(request_body)

        errcode, errmsg, headers = h.getreply()

        if errcode != 200:
            raise xmlrpclib.ProtocolError(host + handler,
                                          errcode, errmsg, headers)

        return self.parse_response(h.getfile())
