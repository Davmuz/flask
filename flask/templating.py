# -*- coding: utf-8 -*-
"""
    flask.templating
    ~~~~~~~~~~~~~~~~

    Implements the bridge to Jinja2.

    :copyright: (c) 2010 by Armin Ronacher.
    :license: BSD, see LICENSE for more details.
"""
import posixpath

from .globals import _request_ctx_stack
from .signals import template_rendered


def _default_template_ctx_processor():
    """Default template context processor.  Injects `request`,
    `session` and `g`.
    """
    reqctx = _request_ctx_stack.top
    return dict(
        config=reqctx.app.config,
        request=reqctx.request,
        session=reqctx.session,
        g=reqctx.g
    )

def _render(template, context, app):
    """Renders the template and fires the signal"""
    rv = template.render(context)
    template_rendered.send(app, template=template, context=context)
    return rv


def render_template(template_name, **context):
    """Renders a template from the template folder with the given
    context.

    :param template_name: the name of the template to be rendered
    :param context: the variables that should be available in the
                    context of the template.
    """
    ctx = _request_ctx_stack.top
    ctx.app.update_template_context(context)
    return _render(ctx.app.jinja_env.get_template(template_name),
                   context, ctx.app)


def render_template_string(source, **context):
    """Renders a template from the given template source string
    with the given context.

    :param template_name: the sourcecode of the template to be
                          rendered
    :param context: the variables that should be available in the
                    context of the template.
    """
    ctx = _request_ctx_stack.top
    ctx.app.update_template_context(context)
    return _render(ctx.app.jinja_env.from_string(source),
                   context, ctx.app)
