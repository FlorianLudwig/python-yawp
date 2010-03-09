# Copyright (c) 2009-2010, Florian Ludwig <dino@phidev.org>
# see LICENSE

import sys
from urllib import urlencode

import cherrypy
from genshi.template import TemplateLoader


TPL = TemplateLoader(['tpl'], auto_reload=True)

DEFAULT_CONFIG = {'/': {
                        'tools.sessions.on': True,
                        'tools.sessions.on' : True,
                        'tools.sessions.timeout': 60
                        }}

default_response = {}


def cherry_go():
    if hasattr(cherrypy.engine, "signal_handler"):
        cherrypy.engine.signal_handler.subscribe()
    if hasattr(cherrypy.engine, "console_control_handler"):
        cherrypy.engine.console_control_handler.subscribe()
    cherrypy.engine.start()
    cherrypy.engine.block()


def quickstart(root):
    """quickstart a yawp/cherrypy"""
    cherrypy.tree.mount(root, "/", config=DEFAULT_CONFIG)
    cherry_go()


def quickdebug(root):
    """Start the application in debug mode using werkzeug's awesome debugger"""
    from werkzeug import DebuggedApplication

    # monkey patch the python inspect module
    import inspect_
    inspect_.patch()

    cherrypy.config.update({'global':{'request.throw_errors': True,}})
    root = cherrypy.Application(root, '/')
    root.config = DEFAULT_CONFIG

    root = DebuggedApplication(root, evalex=True)
    root.root = '/'

    cherrypy.tree.graft(root, "/")
    cherry_go()


def start(globals, Root=None):
    if Root is None and 'Root' in globals:
        Root = globals['Root']
    if Root is None:
        raise AttributeError('Couldn\'t find Root class')
    if globals['__name__'] == '__main__':
        quickdebug(Root())
    else:
        import atexit
        if cherrypy.engine.state == 0:
            cherrypy.engine.start(blocking=False)
            atexit.register(cherrypy.engine.stop)
        globals['application'] = cherrypy.Application(Root(), None)


class Response(dict):
    pass


class MetaLeaf(type):
    def __new__(cls, name, bases, dct):
        for name, obj in dct.iteritems():
            if not name.startswith('_') and callable(obj) and \
              not hasattr(obj, 'exposed') and not isinstance(obj, Leaf):
                    dct[name] = expose(obj)
                    dct[name]._func = obj
        dct['_parent'] = None
        dct['_name'] = 'TO_BE_OVERWRITTEN'
        new =  type.__new__(cls, name, bases, dct)
        for name, obj in dct.iteritems():
            if not name.startswith('_') and (callable(obj) \
              and hasattr(obj, 'exposed') and obj.exposed \
              or isinstance(obj, Leaf)):
                obj._parent = new
                obj._name = name
                if isinstance(obj, Leaf):
                    obj.__class__._parent = new
                    obj.__class__._name = name
        return new


class Leaf(object):
    """Base object to inherent controllers from"""
    __metaclass__ = MetaLeaf


def xhtml(content, w_kwargs):
    tpl = TPL.load(content['_tpl'])
    stream = TPL.load(content['_tpl']).generate(**content)
    #stream = TPL.load(path).generate(**content)
    return stream.render('xhtml')


def rss(content, w_kwargs):
    cherrypy.response.headers['Content-Type'] = 'text/rss'
    content['rss_map'] = {'title': 'title',
                          'entries': 'entries',
                          'entry_title': 'title',
                          'entry_desc': 'description',
                          'entry_date': 'date',
                          'entry_author': 'author'}
    print '*' * 20 + '\n' + repr(w_kwargs)
    if 'rss_map' in w_kwargs:
        content['rss_map'].update(w_kwargs['rss_map'])
    return _xhtml(content, {'tpl': 'rss.tpl'})


FORMATS = {'xhtml': xhtml, 'rss': rss}


def expose(*w_args, **w_kwargs):
    if len(w_args) == 1 and callable(w_args[0]):
        if not 'tpl' in w_kwargs:
            _tpl = cherrypy.request.path_info.replace('/', '_')[1:]
            if _tpl.endswith('_') or _tpl == '':
                _tpl = _tpl[:-1] + 'index'
            _tpl+= '.tpl'
        else:
            _tpl = w_kwargs['tpl']
        class Wrap(object):
            def __call__(self, *args, **kwargs):
                """Acutal function wrapper"""
                if not 'allowed' in w_kwargs:
                    w_kwargs['allowed'] = ('xhtml',)

                response = Response({'_request': cherrypy.request,
                       '_session': cherrypy.session if hasattr(cherrypy, 'session') else None,
                       '_kwargs': kwargs,
                       '_w_kwargs': w_kwargs,
                       '_context': w_args[0],
                       '_format': 'xhtml' if not 'format' in kwargs or \
                                             kwargs['format'] not in FORMATS else kwargs['format'],
                        '_tpl': _tpl
                       })
                response.update(default_response)
                response = w_args[0](self._parent, response, *args, **kwargs)

                if isinstance(response, Response):
                    if not response['_format'] in w_kwargs['allowed']:
                        raise cherrypy.HTTPError(403)
                    output = FORMATS[response['_format']](response, w_kwargs)
                elif isinstance(response, basestring):
                    output = response
                else:
                    raise NotImplementedError
                if 'elixir' in sys.modules:
                    sys.modules['elixir'].session.rollback()
                return output
        w = Wrap()
        w.exposed = True
        w._parent = None
        return w
    else:
        if len(w_args) == 1:
            w_kwargs['tpl'] = w_args[0]
        def _wrap_args(f):
            return expose(f, **w_kwargs)
        _wrap_args.exposed = True
        return _wrap_args


