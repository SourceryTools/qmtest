import qm.fields
from   qm.test.base import Result

class Count:
    """Tutorial test class.

    A 'Count' test counts up the number of characters in a string, given
    by the value of the "Input" field.  The test passes if the length
    matches the value of the "Expected Value" field."""

    fields = [
        qm.fields.TextField(
            name="input",
            title="Input",
            description="The input string."),

        qm.fields.IntegerField(
            name="expected_value",
            title="Expected Value",
            description="The expected length of the input string."),
        ]

    def __init__(self, input, expected_value):
        # Store the arguments for later.
        self.__input = input
        self.__expected_value = expected_value

    def Run(self, context):
        # Compute the length.
        length = len(self.__input)
        # Compare it to the expected value.
        if length == self.__expected_value:
            return Result(Result.PASS)
        else:
            return Result(Result.FAIL)
