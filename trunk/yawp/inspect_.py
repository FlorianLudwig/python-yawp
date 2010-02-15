"""This module is module is monky patching the python inspect module.

This is usefull to get better error messages in development mode.

For more information:
 - cherrypy bug report: U{http://www.cherrypy.org/ticket/883}
 - following code based on: U{http://kbyanc.blogspot.com/2007/07/python-more-generic-getargspec.html}
"""

import inspect
_getargspec = inspect.getargspec


def getargspec(obj):
    """Get the names and default values of a callable's
       arguments

       A tuple of four things is returned: (args, varargs,
       varkw, defaults).
         - args is a list of the argument names (it may
           contain nested lists).
         - varargs and varkw are the names of the * and
           ** arguments or None.
         - defaults is a tuple of default argument values
           or None if there are no default arguments; if
           this tuple has n elements, they correspond to
           the last n elements listed in args.

       Unlike inspect.getargspec(), can return argument
       specification for functions, methods, callable
       objects, and classes.  Does not support builtin
       functions or methods.
    """
    if not callable(obj):
        raise TypeError, "%s is not callable" % type(obj)
    try:
        if inspect.isfunction(obj):
            return _getargspec(obj)
        elif hasattr(obj, 'im_func'):
            # NB: We use im_func so we work with
            #     instancemethod objects also.
            spec = list(inspect.getargspec(obj.im_func))
            return spec
        elif inspect.isclass(obj):
            return _getargspec(obj.__init__)
        elif hasattr(obj, '__call__'):
            return _getargspec(obj.__call__)
    except NotImplementedError:
        # If a nested call to our own getargspec()
        # raises NotImplementedError, re-raise the
        # exception with the real object type to make
        # the error message more meaningful (the caller
        # only knows what they passed us; they shouldn't
        # care what aspect(s) of that object we actually
        # examined).
        pass
    raise NotImplementedError, \
          "do not know how to get argument list for %s" % \
          type(obj)


def patch():
    """Applies monkeypatch."""
    inspect.getargspec = getargspec


