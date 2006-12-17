##############################################################################
#
# Copyright (c) 2006 Zope Corporation and Contributors.
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
"""Evolve moved Zope Dublin Core Annotatable data

$Id: evolve5.py 68965 2006-07-04 12:24:08Z oestermeier $
"""
__docformat__ = "reStructuredText"
from zope.annotation.interfaces import IAnnotatable, IAnnotations
from zope.dublincore.interfaces import IWriteZopeDublinCore
from zope.dublincore.annotatableadapter import ZDCAnnotatableAdapter
from zope.dublincore.annotatableadapter import DCkey
from zope.app.generations.utility import findObjectsProviding
from zope.app.zopeappgenerations import getRootFolder

generation = 5

def evolve(context):
    root = getRootFolder(context)
    for obj in findObjectsProviding(root, IAnnotatable):
        dc = IWriteZopeDublinCore(obj)
        if isinstance(dc, ZDCAnnotatableAdapter):
            # simply mark the ZDCAnnotationData object as dirty so
            # that it gets repickled
            dc._mapping._p_activate()
            dc._mapping._p_changed = True

            # also mark the object holding a reference to it (the
            # annotations mapping) as dirty.  It contains a reference
            # to the old class path for ghosts
            annotations = IAnnotations(obj)
            if DCkey in annotations :
                annotations[DCkey] = annotations[DCkey]
