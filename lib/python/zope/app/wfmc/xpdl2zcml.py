##############################################################################
#
# Copyright (c) 2004 Zope Corporation and Contributors.
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
"""Utility script to generate a zcml skeletin from an xpdl file

Usage: xpdl2zcml xpdl_file process id

The zope package must be in the python path.

$Id: xpdl2zcml.py 29288 2005-02-24 22:09:57Z jim $
"""

import sys
import zope.wfmc.xpdl

def main(args = sys.argv[1:]):
    [xpdl_file, pname, pid] = args

    package = zope.wfmc.xpdl.read(open(xpdl_file))
    pd = package[pname]

    print """\
<configure
    xmlns="http://namespaces.zope.org/zope"
    xmlns:wfmc="http://namespaces.zope.org/wfmc"
    >
"""

    print """\
<wfmc:xpdl
    file="%s"
    process="%s"
    id="%s"
    />
""" % (xpdl_file, pname, pid)

    print "<!-- Participants -->\n"

    participants = pd.participants.items()
    participants.sort()
    for participant in [p for (i, p) in participants]:
        print """\
 <!-- %s -->
 <adapter
    for="zope.wfmc.interfaces.IActivity"
    provides="zope.wfmc.interfaces.IParticipant"
    factory="%s.%s"
    name="%s.%s"
    />
""" % (participant.__name__, pid, participant.id, pid, participant.id)


    print "<!-- Applications -->\n"

    applications = pd.applications.items()
    applications.sort()
    for application in [a for (i, a) in applications]:

        parms = []
        for parm in application.parameters:
            parms.append(parm.__name__
                         + (parm.input and ' : input' or '')
                         + (parm.output and ' : output' or '')
                         )

        descr = "%s (%s) " % (
            getattr(application, '__name__', application.id),
            ', '.join(parms),
            )
        
        print """\
<!-- %s -->
<adapter
    for="zope.wfmc.interfaces.IParticipant"
    provides="zope.wfmc.interfaces.IWorkItem"
    factory="%s.%s"
    name="%s.%s"
    />
""" % (descr, pid, application.id, pid, application.id)

    print "</configure>"

if __name__ == '__main__':
    main()
