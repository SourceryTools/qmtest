########################################################################
#
# File:   state.py
# Author: Alex Samuel
# Date:   2001-05-02
#
# Contents:
#   Trigger to enforce state model.
#
# Copyright (c) 2001 by CodeSourcery, LLC.  All rights reserved. 
#
# Permission is hereby granted, free of charge, to any person
# obtaining a copy of this software and associated documentation files
# (the "Software"), to deal in the Software without restriction,
# including without limitation the rights to use, copy, modify, merge,
# publish, distribute, sublicense, and/or sell copies of the Software,
# and to permit persons to whom the Software is furnished to do so,
# subject to the following conditions:
#
# The above copyright notice and this permission notice shall be
# included in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
# MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
# NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS
# BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN
# ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN
# CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
#
########################################################################

########################################################################
# imports
########################################################################

import qm.fields
import qm.track.issue
import qm.track.issue_class
from   qm.track.issue_class import TriggerResult

########################################################################
# classes
########################################################################

class Trigger(qm.track.issue_class.Trigger):

    def __init__(self, name, state_field_name="state"):
        # Initialize the base class.
        qm.track.issue_class.Trigger.__init__(self, name)
        self.__state_field_name = state_field_name
        

    def Preupdate(self, issue, previous_issue):
        field_name = self.__state_field_name
        new_state = issue.GetField(field_name)

        if previous_issue is not None:
            # This is a revision of an existing issue.  Get the previous
            # state.
            old_state = previous_issue.GetField(field_name)
            # If the state hasn't been changed, it's fine.
            if new_state == old_state:
                return TriggerResult(self, TriggerResult.ACCEPT)

        # Extract the state field and state model.
        state_field = issue.GetClass().GetField(field_name)
        state_model = state_field.GetStateModel()

        if previous_issue is None:
            # This is a new issue.  Make sure that the specified state
            # is the initial state.
            initial_state_name = state_model.GetInitialStateName()
            if str(new_state) != initial_state_name:
                # It's not.  Complain.
                message = qm.message("not initial state",
                                     initial_state_name=initial_state_name)
                return TriggerResult(self, TriggerResult.REJECT, message)
        else:
            try:
                # Get the corresponding transition.
                transition = state_model.GetTransition(str(old_state),
                                                       str(new_state))
            except qm.track.issue_class.NoSuchTransitionError:
                # There is no transition between the indicated states.
                # Reject the issue update.
                message = qm.message("no transition",
                                     starting_state_name=str(old_state),
                                     ending_state_name=str(new_state))
                return TriggerResult(self, TriggerResult.REJECT, message)

            # Now test conditions.
            for condition in transition.GetConditions():
                # Evaluate the condition's expression.
                expression = condition.GetExpression()
                result = qm.track.issue.eval_expression(expression,
                                                        issue,
                                                        previous_issue)
                if not result:
                    # It evaluated to false, so the transition is
                    # rejected.
                    message = qm.error("transition condition failed",
                                       starting_state_name=str(old_state),
                                       ending_state_name=str(new_state),
                                       name=condition.GetName(),
                                       expression=expression)
                    return TriggerResult(self, TriggerResult.REJECT, message)
        # The transition is OK.
        return TriggerResult(self, TriggerResult.ACCEPT)



########################################################################
# Local Variables:
# mode: python
# indent-tabs-mode: nil
# fill-column: 72
# End:
