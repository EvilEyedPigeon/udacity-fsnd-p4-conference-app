"""Basic App Engine data & ProtoRPC models."""

import httplib
import endpoints
import operator

from protorpc import messages
from google.appengine.ext import ndb


#------ Basic messages and exceptions -----------------------------------------

class ConflictException(endpoints.ServiceException):
    """ConflictException -- exception mapped to HTTP 409 response"""
    http_status = httplib.CONFLICT

class StringMessage(messages.Message):
    """StringMessage-- outbound (single) string message"""
    data = messages.StringField(1, required=True)

class BooleanMessage(messages.Message):
    """BooleanMessage-- outbound Boolean value message"""
    data = messages.BooleanField(1)


#------ Queries ---------------------------------------------------------------

# Operator strings that can be passed to query filters,
# and corresponding python operators (as strings)
QUERY_OPERATORS = {
    'EQ':   '=',
    'GT':   '>',
    'GTEQ': '>=',
    'LT':   '<',
    'LTEQ': '<=',
    'NE':   '!='
}

# Python operators (used for queries) as strings,
# and corresponding python operators.
OPERATOR_LOOKUP = {
    '=':  operator.eq,
    '>':  operator.gt,
    '>=': operator.ge,
    '<':  operator.lt,
    '<=': operator.le,
    '!=': operator.ne
}

# Generic query filter
class QueryForm(messages.Message):
    """QueryForm -- Query inbound form message"""
    field = messages.StringField(1)
    operator = messages.StringField(2)
    value = messages.StringField(3)

# Generic list of query filters
class QueryForms(messages.Message):
    """QueryForms -- multiple QueryForm inbound form message"""
    filters = messages.MessageField(QueryForm, 1, repeated = True)

#------------------------------------------------------------------------------
