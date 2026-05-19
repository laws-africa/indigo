from rest_framework.authentication import TokenAuthentication


class BearerAuthentication(TokenAuthentication):
    """The preferred authentication method, which is more common than Token authentication.
    """
    keyword = 'Bearer'
