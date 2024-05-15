"""
Wrapper for exception handling.
"""


class ConvertExceptions:   # pylint: disable=too-few-public-methods
    """
    Wrapper function for handling exceptions. The first
    parameter is the Exception to catch, the second is
    what to return instead (default is None). Example:

    @ConvertExceptions(TypeError, '')
    def do_the_thing(blah):
        make_attempt = try_it(blah)
        return make_attempt['result']

    If a TypeError Exception occurs during do_the_thing, the function
    returns a blank string.
    """

    func = None

    def __init__(self, exceptions, replacement=None):
        self.exceptions = exceptions
        self.replacement = replacement

    def __call__(self, *args, **kwargs):
        if self.func is None:
            self.func = args[0]
            return self
        try:
            return self.func(*args, **kwargs)
        except self.exceptions:
            return self.replacement
