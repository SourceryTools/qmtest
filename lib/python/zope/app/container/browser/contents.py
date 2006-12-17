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
"""View Class for the Container's Contents view.

$Id: contents.py 67630 2006-04-27 00:54:03Z jim $
"""
__docformat__ = 'restructuredtext'

import urllib

from zope.exceptions.interfaces import UserError
from zope.security.interfaces import Unauthorized
from zope.security import canWrite
from zope.size.interfaces import ISized
from zope.traversing.interfaces import TraversalError
from zope.publisher.browser import BrowserView
from zope.dublincore.interfaces import IZopeDublinCore
from zope.dublincore.interfaces import IDCDescriptiveProperties
from zope.copypastemove.interfaces import IPrincipalClipboard
from zope.copypastemove.interfaces import IObjectCopier, IObjectMover
from zope.copypastemove.interfaces import IContainerItemRenamer

from zope.app import zapi
from zope.app.pagetemplate.viewpagetemplatefile import ViewPageTemplateFile
from zope.app.i18n import ZopeMessageFactory as _
from zope.app.principalannotation.interfaces import IPrincipalAnnotationUtility

from zope.app.container.browser.adding import Adding
from zope.app.container.interfaces import IContainer, DuplicateIDError
from zope.app.container.interfaces import IContainerNamesContainer

class Contents(BrowserView):

    __used_for__ = IContainer

    error = ''
    message = ''
    normalButtons = False
    specialButtons = False
    supportsRename = False

    def listContentInfo(self):
        request = self.request

        if  "container_cancel_button" in request:
            if "type_name" in request:
                del request.form['type_name']
            if "rename_ids" in request and "new_value" in request:
                del request.form['rename_ids']
            if "retitle_id" in request and "new_value" in request:
                del request.form['retitle_id']

            return self._normalListContentsInfo()

        elif "container_rename_button" in request and not request.get("ids"):
            self.error = _("You didn't specify any ids to rename.")
        elif "container_add_button" in request:
            if "single_type_name" in request \
                   and "single_new_value" in request:
                request.form['type_name'] = request['single_type_name']
                request.form['new_value'] = request['single_new_value']
                self.addObject()
            elif 'single_type_name' in request \
                     and 'single_new_value' not in request:
                request.form['type_name'] = request['single_type_name']
                request.form['new_value'] = ""
                self.addObject()
        elif "type_name" in request and "new_value" in request:
            self.addObject()
        elif "rename_ids" in request and "new_value" in request:
            self.renameObjects()
        elif "retitle_id" in request and "new_value" in request:
            self.changeTitle()
        elif "container_cut_button" in request:
            self.cutObjects()
        elif "container_copy_button" in request:
            self.copyObjects()
        elif "container_paste_button" in request:
            self.pasteObjects()
        elif "container_delete_button" in request:
            self.removeObjects()
        else:
            return self._normalListContentsInfo()

        if self.error:
            return self._normalListContentsInfo()

        status = request.response.getStatus()
        if status not in (302, 303):
            # Only redirect if nothing else has
            request.response.redirect(request.URL)
        return ()

    def normalListContentInfo(self):
        return self._normalListContentsInfo()

    def _normalListContentsInfo(self):
        request = self.request

        self.specialButtons = (
                 'type_name' in request or
                 'rename_ids' in request or
                 ('container_rename_button' in request
                  and request.get("ids")) or
                 'retitle_id' in request
                 )
        self.normalButtons = not self.specialButtons

        info = map(self._extractContentInfo, self.context.items())

        self.supportsCut = info
        self.supportsCopy = info
        self.supportsDelete = info
        self.supportsPaste = self.pasteable()
        self.supportsRename = (
            self.supportsCut and
            not IContainerNamesContainer.providedBy(self.context)
            )

        return info


    def _extractContentInfo(self, item):
        request = self.request


        rename_ids = {}
        if "container_rename_button" in request:
            for rename_id in request.get('ids', ()):
                rename_ids[rename_id] = rename_id
        elif "rename_ids" in request:
            for rename_id in request.get('rename_ids', ()):
                rename_ids[rename_id] = rename_id


        retitle_id = request.get('retitle_id')

        id, obj = item
        info = {}
        info['id'] = info['cb_id'] = id
        info['object'] = obj

        info['url'] = urllib.quote(id.encode('utf-8'))
        info['rename'] = rename_ids.get(id)
        info['retitle'] = id == retitle_id


        zmi_icon = zapi.queryMultiAdapter((obj, self.request), name='zmi_icon')
        if zmi_icon is None:
            info['icon'] = None
        else:
            info['icon'] = zmi_icon()

        dc = IZopeDublinCore(obj, None)
        if dc is not None:
            info['retitleable'] = canWrite(dc, 'title')
            info['plaintitle'] = not info['retitleable']

            title = self.safe_getattr(dc, 'title', None)
            if title:
                info['title'] = title

            formatter = self.request.locale.dates.getFormatter(
                'dateTime', 'short')

            created = self.safe_getattr(dc, 'created', None)
            if created is not None:
                info['created'] = formatter.format(created)

            modified = self.safe_getattr(dc, 'modified', None)
            if modified is not None:
                info['modified'] = formatter.format(modified)
        else:
            info['retitleable'] = 0
            info['plaintitle'] = 1


        sized_adapter = ISized(obj, None)
        if sized_adapter is not None:
            info['size'] = sized_adapter
        return info

    def safe_getattr(self, obj, attr, default):
        """Attempts to read the attr, returning default if Unauthorized."""
        try:
            return getattr(obj, attr, default)
        except Unauthorized:
            return default

    def renameObjects(self):
        """Given a sequence of tuples of old, new ids we rename"""
        request = self.request
        ids = request.get("rename_ids")
        newids = request.get("new_value")

        renamer = IContainerItemRenamer(self.context)
        for oldid, newid in map(None, ids, newids):
            if newid != oldid:
                renamer.renameItem(oldid, newid)

    def changeTitle(self):
        """Given a sequence of tuples of old, new ids we rename"""
        request = self.request
        id = request.get("retitle_id")
        new = request.get("new_value")

        item = self.context[id]
        dc = IDCDescriptiveProperties(item)
        dc.title = new

    def hasAdding(self):
        """Returns true if an adding view is available."""
        adding = zapi.queryMultiAdapter((self.context, self.request), name="+")
        return (adding is not None)

    def addObject(self):
        request = self.request
        if IContainerNamesContainer.providedBy(self.context):
            new = ""
        else:
            new = request["new_value"]

        adding = zapi.queryMultiAdapter((self.context, self.request), name="+")
        if adding is None:
            adding = Adding(self.context, request)
        else:
            # Set up context so that the adding can build a url
            # if the type name names a view.
            # Note that we can't so this for the "adding is None" case
            # above, because there is no "+" view.
            adding.__parent__ = self.context
            adding.__name__ = '+'

        adding.action(request['type_name'], new)

    def removeObjects(self):
        """Remove objects specified in a list of object ids"""
        request = self.request
        ids = request.get('ids')
        if not ids:
            self.error = _("You didn't specify any ids to remove.")
            return

        container = self.context
        for id in ids:
            del container[id]

    def copyObjects(self):
        """Copy objects specified in a list of object ids"""
        request = self.request
        ids = request.get('ids')
        if not ids:
            self.error = _("You didn't specify any ids to copy.")
            return

        container_path = zapi.getPath(self.context)

        # For each item, check that it can be copied; if so, save the
        # path of the object for later copying when a destination has
        # been selected; if not copyable, provide an error message
        # explaining that the object can't be copied.
        items = []
        for id in ids:
            ob = self.context[id]
            copier = IObjectCopier(ob)
            if not copier.copyable():
                m = {"name": id}
                title = getDCTitle(ob)
                if title:
                    m["title"] = title
                    self.error = _(
                        "Object '${name}' (${title}) cannot be copied",
                        mapping=m)
                else:
                    self.error = _("Object '${name}' cannot be copied",
                                   mapping=m)
                return
            items.append(zapi.joinPath(container_path, id))

        # store the requested operation in the principal annotations:
        clipboard = getPrincipalClipboard(self.request)
        clipboard.clearContents()
        clipboard.addItems('copy', items)

    def cutObjects(self):
        """move objects specified in a list of object ids"""
        request = self.request
        ids = request.get('ids')
        if not ids:
            self.error = _("You didn't specify any ids to cut.")
            return

        container_path = zapi.getPath(self.context)

        # For each item, check that it can be moved; if so, save the
        # path of the object for later moving when a destination has
        # been selected; if not movable, provide an error message
        # explaining that the object can't be moved.
        items = []
        for id in ids:
            ob = self.context[id]
            mover = IObjectMover(ob)
            if not mover.moveable():
                m = {"name": id}
                title = getDCTitle(ob)
                if title:
                    m["title"] = title
                    self.error = _(
                        "Object '${name}' (${title}) cannot be moved",
                        mapping=m)
                else:
                    self.error = _("Object '${name}' cannot be moved",
                                   mapping=m)
                return
            items.append(zapi.joinPath(container_path, id))

        # store the requested operation in the principal annotations:
        clipboard = getPrincipalClipboard(self.request)
        clipboard.clearContents()
        clipboard.addItems('cut', items)


    def pasteable(self):
        """Decide if there is anything to paste
        """
        target = self.context
        clipboard = getPrincipalClipboard(self.request)
        items = clipboard.getContents()
        for item in items:
            try:
                obj = zapi.traverse(target, item['target'])
            except TraversalError:
                pass
            else:
                if item['action'] == 'cut':
                    mover = IObjectMover(obj)
                    moveableTo = self.safe_getattr(mover, 'moveableTo', None)
                    if moveableTo is None or not moveableTo(target):
                        return False
                elif item['action'] == 'copy':
                    copier = IObjectCopier(obj)
                    copyableTo = self.safe_getattr(copier, 'copyableTo', None)
                    if copyableTo is None or not copyableTo(target):
                        return False
                else:
                    raise

        return True


    def pasteObjects(self):
        """Paste ojects in the user clipboard to the container
        """
        target = self.context
        clipboard = getPrincipalClipboard(self.request)
        items = clipboard.getContents()
        moved = False
        not_pasteable_ids = []
        for item in items:
            duplicated_id = False
            try:
                obj = zapi.traverse(target, item['target'])
            except TraversalError:
                pass
            else:
                if item['action'] == 'cut':
                    mover = IObjectMover(obj)
                    try:
                        mover.moveTo(target)
                        moved = True
                    except DuplicateIDError:
                        duplicated_id = True
                elif item['action'] == 'copy':
                    copier = IObjectCopier(obj)
                    try:
                        copier.copyTo(target)
                    except DuplicateIDError:
                        duplicated_id = True
                else:
                    raise

            if duplicated_id:
                not_pasteable_ids.append(zapi.getName(obj))

        if moved:
            # Clear the clipboard if we do a move, but not if we only do a copy
            clipboard.clearContents()

        if not_pasteable_ids != []:
            # Show the ids of objects that can't be pasted because
            # their ids are already taken.
            # TODO Can't we add a 'copy_of' or something as a prefix
            # instead of raising an exception ?
            raise UserError(
                _("The given name(s) %s is / are already being used" %(
                str(not_pasteable_ids))))

    def hasClipboardContents(self):
        """Interogate the ``PrinicipalAnnotation`` to see if clipboard
        contents exist."""

        if not self.supportsPaste:
            return False

        # touch at least one item to in clipboard confirm contents
        clipboard = getPrincipalClipboard(self.request)
        items = clipboard.getContents()
        for item in items:
            try:
                zapi.traverse(self.context, item['target'])
            except TraversalError:
                pass
            else:
                return True

        return False

    contents = ViewPageTemplateFile('contents.pt')
    contentsMacros = contents

    _index = ViewPageTemplateFile('index.pt')

    def index(self):
        if 'index.html' in self.context:
            self.request.response.redirect('index.html')
            return ''

        return self._index()

class JustContents(Contents):
    """Like Contents, but does't delegate to item named index.html"""

    def index(self):
        return self._index()


def getDCTitle(ob):
    dc = IDCDescriptiveProperties(ob, None)
    if dc is None:
        return None
    else:
        return dc.title


def getPrincipalClipboard(request):
    """Return the clipboard based on the request."""
    user = request.principal
    annotationutil = zapi.getUtility(IPrincipalAnnotationUtility)
    annotations = annotationutil.getAnnotations(user)
    return IPrincipalClipboard(annotations)
