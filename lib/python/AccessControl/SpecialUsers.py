##############################################################################
#
# Copyright (c) 2002 Zope Corporation and Contributors. All Rights Reserved.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE.
#
##############################################################################
"""Place to find special users

This is needed to avoid a circular import problem.  The 'real' values
are stored here by the AccessControl.User module as part of it's
initialization.

$Id: SpecialUsers.py 40218 2005-11-18 14:39:19Z andreasjung $
"""
nobody = None
system = None
emergency_user = None

# Note: use of the 'super' name is deprecated.
super = None
