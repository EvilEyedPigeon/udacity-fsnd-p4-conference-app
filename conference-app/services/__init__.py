import endpoints
from functools import wraps

from utils import getUserId


#------ Base service ----------------------------------------------------------

class BaseService(object):
    """Base service with basic functionality for other services.

    Includes methods to get the current user and user id.
    
    Note that when using subclasses of this service it is not necessary
    to pass the current user to the service methods.
    """

    def get_user(self):
        return endpoints.get_current_user()

    def get_user_id(self):
        return getUserId(self.get_user())


#------ Utility functions -----------------------------------------------------

def login_required(func):
    """Decorates a method to ensure that only logged in users can access it.

    Raises:
        endpoints.UnauthorizedException
    """
    @wraps(func)
    def login_required_method(*args, **kargs):
        user = endpoints.get_current_user()
        if not user:
            raise endpoints.UnauthorizedException("Authorization required")
        return func(*args, **kargs)

    return login_required_method

#------------------------------------------------------------------------------
