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
"""Define view component for naive file editing.

$Id: image.py 67713 2006-04-28 11:04:17Z dobe $
"""
__docformat__ = 'restructuredtext'

from zope.size.interfaces import ISized
from zope.app import zapi
from zope.app.file.browser.file import FileView
class ImageData(FileView):

    def __call__(self):
        return self.show()

    def tag(self, height=None, width=None, alt=None,
            scale=0, xscale=0, yscale=0, css_class=None, **args):
        """
        Generate an HTML IMG tag for this image, with customization.
        Arguments to ``self.tag()`` can be any valid attributes of an IMG tag.
        `src` will always be an absolute pathname, to prevent redundant
        downloading of images. Defaults are applied intelligently for
        `height`, `width`, and `alt`. If specified, the `scale`, `xscale`,
        and `yscale` keyword arguments will be used to automatically adjust
        the output height and width values of the image tag.

        Since 'class' is a Python reserved word, it cannot be passed in
        directly in keyword arguments which is a problem if you are
        trying to use ``tag()`` to include a CSS class. The `tag()` method
        will accept a `css_class` argument that will be converted to
        ``class`` in the output tag to work around this.
        """
        if width is None:
            width = self.context.getImageSize()[0]
        if height is None:
            height = self.context.getImageSize()[1]

        # Auto-scaling support
        xdelta = xscale or scale
        ydelta = yscale or scale

        if xdelta and width:
            width = str(int(round(int(width) * xdelta)))
        if ydelta and height:
            height = str(int(round(int(height) * ydelta)))

        if self.request is not None:
            result = '<img src="%s"' % zapi.absoluteURL(self.context,
                                                        self.request)
        else:
            result = '<img '       
 
        if alt is None:
            alt = getattr(self, 'title', '')
        result = '%s alt="%s"' % (result, alt)

        if height is not None:
            result = '%s height="%s"' % (result, height)

        if width is not None:
            result = '%s width="%s"' % (result, width)

        if not 'border' in [a.lower() for a in args.keys()]:
            result = '%s border="0"' % result

        if css_class is not None:
            result = '%s class="%s"' % (result, css_class)

        for key in args.keys():
            value = args.get(key)
            result = '%s %s="%s"' % (result, key, value)

        return '%s />' % result


class ImageUpload(object):
    """Image edit view mix-in that provides access to image size info"""

    def size(self):
        sized = ISized(self.context)
        return sized.sizeForDisplay()

class ImageAdd(object):
    
    def update(self):
        
        if self.update_status is not None:
            # We've been called before. Just return the previous result.
            return self.update_status

        # set the name of the image if not defined
        if not self.request.form.get('add_input_name'):
            filename = getattr(self.request.form.get("field.data"),
                               "filename", None)
            if filename is not None:
                self.request.form["add_input_name"] = filename

        return super(ImageAdd,self).update()
