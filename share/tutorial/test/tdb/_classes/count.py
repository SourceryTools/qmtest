import qm.fields
from   qm.test.base import Result

class Count:
    fields = [
        qm.fields.TextField(
            name="input",
            description="The input string."),
        qm.fields.IntegerField(
            name="expected_value",
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
