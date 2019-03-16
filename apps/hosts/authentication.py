from rest_framework.authentication import TokenAuthentication
from hosts.models import MyOwnToken

class MyOwnTokenAuthentication(TokenAuthentication):
    model = MyOwnToken