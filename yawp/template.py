# Copyright (c) 2010, Florian Ludwig <dino@phidev.org>
# see LICENSE

import os
import StringIO
import copy
import logging

from genshi.template import TemplateLoader, MarkupTemplate, NewTextTemplate
import genshi.template.loader


class ActionscriptTemplate(NewTextTemplate):
    """Template for langauges with /* ... */ commments

        Should work for JavaScript, Action Script, c,..."""
    def __init__(self, *args, **kwargs):
        kwargs['delims'] = ('/*%', '%*/', '/*###', '###*/')
        NewTextTemplate.__init__(self, *args, **kwargs)


class ShellStyleTemplate(NewTextTemplate):
    """Template for languages with # commentars"""
    def __init__(self, *args, **kwargs):
        kwargs['delims'] = ('#%', '%#', '##*', '*##')
        NewTextTemplate.__init__(self, *args, **kwargs)


def get_template(fpath):
    """returns template class for given filename"""
    if fpath.endswith('.css') or fpath.endswith('.as') or fpath.endswith('.js'):
        return ActionscriptTemplate
    elif fpath.endswith('.py') or fpath.endswith('.wsgi'):
        return ShellStyleTemplate
    elif fpath.endswith('.mxml'):
        return MarkupTemplate
    else:
        logging.warn('WARNING: don\'t know the file type of "%s"' % fpath)
        return NewTextTemplate


def numbered_file(fpath, mode='r'):
    """Add filenumbers to every line as comment
    
    Returns filelike object
    """
    _fileobj = open(fpath, mode)
    tmpl_cls = get_template(fpath)
    if tmpl_cls == ActionscriptTemplate:
        comment_start = '/*'  
        comment_end = '*/'
        last_symbole = ';'
    elif tmpl_cls == MarkupTemplate:
        comment_start = '<!--'  
        comment_end = '-->'
        last_symbole = '>'
    else:
        print 'WARNING: no line numbers for "%s"' % fpath
        return _fileobj

    data = []
    in_comment = False
    in_hidden_comment = False
    for number, line in enumerate(_fileobj.readlines()):
        line = line = line.rstrip()

        if not in_comment and comment_start in line:
            in_comment = True
            s = line.find(comment_start) + len(comment_start)
            if line[s:].lstrip().startswith('!'):
                in_hidden_comment = True
        if in_comment and comment_end in line:
            in_comment = False
            in_hidden_comment = False

        if not line.endswith(last_symbole):
            data.append(line)
            continue

        if in_comment:
            line += comment_end

        if line.rstrip().endswith('\\'):
            # if the lines ends with a \ we might destroy the template syntax
            continue

        count_line = line.replace('\t', '    ')
        white = 83 - len(count_line) if len(count_line) < 78 else 3

        comment = comment_start + '  Line: %i  ' + comment_end
        if in_comment:
            comment += comment_start
        if in_hidden_comment:
            comment += '!'
        data.append(line
                    + white*' '
                    + (comment % (number+1)))
    return StringIO.StringIO('\n'.join(data))

# monkey patch template loader
genshi.template.loader.open = numbered_file


class Handler(object):
    """Common handler for templates"""
    def __init__(self, path, default_args={}):
        if not isinstance(path, list):
            path = [path]
        self.loader = TemplateLoader(path)
        self.default_args = default_args

    def gen(self, src, dst, local_args={}):
        print src, '->',
        tmpl = self.loader.load(src, cls=get_template(src))
        args = copy.copy(self.default_args)
        args.update(local_args)
        stream = tmpl.generate(**args)
        print dst
        data = stream.render()
        # make sure we only touch file if we would change it
        dst_data = open(dst).read() if os.path.exists(dst) else ''
        if dst_data != data:
            open(dst, 'w').write(data)



