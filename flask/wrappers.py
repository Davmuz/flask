# -*- coding: utf-8 -*-
"""
    flask.wrappers
    ~~~~~~~~~~~~~~

    Implements the WSGI wrappers (request and response).

    :copyright: (c) 2010 by Armin Ronacher.
    :license: BSD, see LICENSE for more details.
"""

from werkzeug import Request as RequestBase, Response as ResponseBase, \
    cached_property, import_string
from werkzeug.routing import Rule as RuleBase

from .helpers import json, _assert_have_json
from .globals import _request_ctx_stack


class Request(RequestBase):
    """The request object used by default in Flask.  Remembers the
    matched endpoint and view arguments.

    It is what ends up as :class:`~flask.request`.  If you want to replace
    the request object used you can subclass this and set
    :attr:`~flask.Flask.request_class` to your subclass.
    """

    #: the internal URL rule that matched the request.  This can be
    #: useful to inspect which methods are allowed for the URL from
    #: a before/after handler (``request.url_rule.methods``) etc.
    #:
    #: .. versionadded:: 0.6
    url_rule = None

    #: a dict of view arguments that matched the request.  If an exception
    #: happened when matching, this will be `None`.
    view_args = None
    #: if matching the URL failed, this is the exception that will be
    #: raised / was raised as part of the request handling.  This is
    #: usually a :exc:`~werkzeug.exceptions.NotFound` exception or
    #: something similar.
    routing_exception = None

    @property
    def max_content_length(self):
        """Read-only view of the `MAX_CONTENT_LENGTH` config key."""
        ctx = _request_ctx_stack.top
        if ctx is not None:
            return ctx.app.config['MAX_CONTENT_LENGTH']

    @property
    def endpoint(self):
        """The endpoint that matched the request.  This in combination with
        :attr:`view_args` can be used to reconstruct the same or a
        modified URL.  If an exception happened when matching, this will
        be `None`.
        """
        if self.url_rule is not None:
            return self.url_rule.endpoint

    @cached_property
    def json(self):
        """If the mimetype is `application/json` this will contain the
        parsed JSON data.
        """
        if __debug__:
            _assert_have_json()
        if self.mimetype == 'application/json':
            return json.loads(self.data)


class Response(ResponseBase):
    """The response object that is used by default in Flask.  Works like the
    response object from Werkzeug but is set to have an HTML mimetype by
    default.  Quite often you don't have to create this object yourself because
    :meth:`~flask.Flask.make_response` will take care of that for you.

    If you want to replace the response object used you can subclass this and
    set :attr:`~flask.Flask.response_class` to your subclass.
    """
    default_mimetype = 'text/html'


class Rule(RuleBase):
    """Extends Werkzeug routing to support the OPTIONS method and set the view
    function.
    """
    def __init__(self, *args, **kwargs):
        """
        :param view_func: a view function.
        """
        # Setup OPTIONS parameter
        methods = kwargs.pop('methods', ('GET',))
        provide_automatic_options = False
        if 'OPTIONS' not in methods:
            methods = tuple(methods) + ('OPTIONS',)
            provide_automatic_options = True
        kwargs['methods'] = methods
        self.provide_automatic_options = provide_automatic_options
        
        # Set the view function
        endpoint = kwargs.get('endpoint', None)
        view_func = kwargs.pop('view_func', None)
        if not view_func:
            if callable(endpoint):
                view_func = endpoint
                endpoint = endpoint.__name__
            elif type(endpoint) is str:
                view_func = import_string(endpoint)
        
        self.view_func = view_func
        kwargs['endpoint'] = endpoint
        RuleBase.__init__(self, *args, **kwargs)
        
    def empty(self):
        """Return an unbound copy of this rule.  This can be useful if you
        want to reuse an already bound URL for another map."""
        defaults = None
        if self.defaults is not None:
            defaults = dict(self.defaults)
        return Rule(self.rule, defaults, self.subdomain, self.methods,
                    self.build_only, self.endpoint, self.strict_slashes,
                    self.redirect_to, view_func=self.view_func)
