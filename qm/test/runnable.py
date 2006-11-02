########################################################################
#
# File:   runnable.py
# Author: Mark Mitchell
# Date:   10/11/2002
#
# Contents:
#   QMTest Runnable class.
#
# Copyright (c) 2002, 2003 by CodeSourcery, LLC.  All rights reserved. 
#
# For license terms see the file COPYING.
#
########################################################################

########################################################################
# Imports
########################################################################

import qm
import qm.extension
from   qm.fields import AttachmentField, TupleField, SetField

########################################################################
# Classes
########################################################################

class Runnable(qm.extension.Extension):
    """A 'Runnable' can run on a 'Target'.

    'Runnable' is an abstract base class for 'Test' and 'Resource'."""

    class ResourceField(qm.fields.ChoiceField):
        """A 'ResourceField' contains the name of a resource.

        The exact format of the name depends on the test database in use."""

        def GetItems(self):

            database = qm.test.cmdline.get_qmtest().GetDatabase()
            return database.GetResourceIds()



    EXTRA_ID = "qmtest_id"
    """The name of the extra keyword argument to '__init__' that
    specifies the name of the test or resource."""
    
    EXTRA_DATABASE = "qmtest_database"
    """The name of the extra keyword argument to '__init__' that
    specifies the database containing the test or resource."""

    RESOURCE_FIELD_ID = "resources"
    """The name of the field that contains the resources on which this
    test or resource depends."""
    
    arguments = [
        qm.fields.SetField(
            ResourceField(
                name = RESOURCE_FIELD_ID,
                title = "Resources",
                description = \
                """Resources on which this test or resource depends.
                
                Before this test or resource is executed, the
                resources on which it depends will be set up.""",
                not_empty_text = "true",
                )),
        ]

    
    def __init__(self, arguments = None, **args):
        """Construct a new 'Runnable'.

        'arguments' -- As for 'Extension.__init__'.

        'args' -- As for 'Extension.__init__."""

        self.__id = args.pop(self.EXTRA_ID)
        self.__database = args.pop(self.EXTRA_DATABASE)
        if arguments: args.update(arguments)
        super(Runnable, self).__init__(**args)
        
        
        
    def GetId(self):
        """Return the name of this test or resource.

        'context' -- The 'Context' in which this entity is running.
        
        returns -- The name of this test or resource."""

        return self.__id


    def GetDatabase(self):
        """Return the 'Database' in which this test or resource is stored.

        returns -- The 'Database' in which this test or resource is
        stored."""

        return self.__database


    def GetAttachments(self):
        """Return the 'Attachment's to this 'Runnable'.

        returns -- A sequence consisting of the 'Attachment' objects
        associated with this runnable."""

        attachments = []
        for f in qm.extension.get_class_arguments(self.__class__):
            self.__GetAttachments(f,
                                  getattr(self, f.GetName()),
                                  attachments)
        return attachments


    def __GetAttachments(self, field, value, attachments):
        """Return the 'Attachments' that are part of 'field'.

        'field' -- The 'Field' being examined.

        'value' -- The value of that 'Field' in 'self'.

        'attachments' -- A sequence consisting of the attachments
        found so far.  Additional 'Attachment's are appended to this
        sequence by this function."""

        if isinstance(field, AttachmentField):
            attachments.append(getattr(self, field.GetName()))
        elif isinstance(field, TupleField):
            subfields = field.GetSubfields()
            for i in xrange(len(subfields)):
                self.__GetAttachments(subfields[i], value[i],
                                      attachments)
        elif isinstance(field, SetField):
            subfield = field.GetSubfields()[0]
            for i in xrange(len(value)):
                self.__GetAttachments(subfield, value[i],
                                      attachments)

        return
                
