##############################################################################
#
# Copyright (c) 2002 Zope Corporation and Contributors.
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
"""Code to initialize the application server

$Id: debug.py 67630 2006-04-27 00:54:03Z jim $
"""
__docformat__ = 'restructuredtext'

import base64, time
from StringIO import StringIO
from zope.publisher.publish import publish as _publish, debug_call
from zope.publisher.browser import TestRequest, setDefaultSkin
from zope.app.publication.browser import BrowserPublication
from zope.app.appsetup import config, database

class Debugger(object):

    def __init__(self, db=None, config_file=None):
        if db is None and config_file is None:
            db = 'Data.fs'
            config_file = 'site.zcml'

        if config_file is not None:
            config(config_file)
        self.db = database(db)

    def fromDatabase(cls, db):
        inst = cls.__new__(cls)
        inst.db = db
        return inst
    fromDatabase = classmethod(fromDatabase)

    def root(self):
        """Get the top-level application object

        The object returned is connected to an open database connection.
        """

        from zope.app.publication.zopepublication import ZopePublication
        return self.db.open().root()[ZopePublication.root_name]

    def _request(self,
                 path='/', stdin='', basic=None,
                 environment = None, form=None,
                 request=None, publication=BrowserPublication):
        """Create a request
        """

        env = {}

        if type(stdin) is str:
            stdin = StringIO(stdin)

        p=path.split('?')
        if len(p)==1:
            env['PATH_INFO'] = p[0]
        elif len(p)==2:
            env['PATH_INFO'], env['QUERY_STRING'] = p
        else:
            raise ValueError("Too many ?s in path", path)

        if environment is not None:
            env.update(environment)

        if basic:
            env['HTTP_AUTHORIZATION']="Basic %s" % base64.encodestring(basic)


        pub = publication(self.db)

        if request is not None:
            request = request(stdin, env)
        else:
            request = TestRequest(stdin, env)
            setDefaultSkin(request)
        request.setPublication(pub)
        if form:
            # This requires that request class has an attribute 'form'
            # (BrowserRequest has, TestRequest hasn't)
            request.form.update(form)

        return request

    def publish(self, path='/', stdin='', *args, **kw):
        t, c = time.time(), time.clock()

        request = self._request(path, stdin, *args, **kw)
        getStatus = getattr(request.response, 'getStatus', lambda: None)
        _publish(request)

        headers = request.response.getHeaders()
        headers.sort()
        print 'Status %s\r\n%s\r\n\r\n%s' % (
            request.response.getStatusString(),
            '\r\n'.join([("%s: %s" % h) for h in headers]),
            request.response.consumeBody(),
            )
        return time.time()-t, time.clock()-c, getStatus()

    def run(self, *args, **kw):
        t, c = time.time(), time.clock()
        request = self._request(*args, **kw)
        getStatus = getattr(request.response, 'getStatus', lambda: None)
        _publish(request, handle_errors=False)
        return time.time()-t, time.clock()-c, getStatus()

    def debug(self, *args, **kw):

        import pdb

        class Pdb(pdb.Pdb):
            def do_pub(self,arg):
                if hasattr(self,'done_pub'):
                    print 'pub already done.'
                else:
                    self.do_s('')
                    self.do_s('')
                    self.do_c('')
                    self.done_pub=1
            def do_ob(self,arg):
                if hasattr(self,'done_ob'):
                    print 'ob already done.'
                else:
                    self.do_pub('')
                    self.do_c('')
                    self.done_ob=1

        db=Pdb()

        request = self._request(*args, **kw)
        fbreak(db, _publish)
        fbreak(db, debug_call)

        print '* Type c<cr> to jump to published object call.'
        db.runcall(_publish, request)


def fbreak(db, meth):
    try:
        meth = meth.im_func
    except AttributeError:
        pass
    code = meth.func_code
    lineno = getlineno(code)
    filename = code.co_filename
    db.set_break(filename,lineno)



try:
    from codehack import getlineno
except:
    def getlineno(code):
        return code.co_firstlineno
