from rest_framework.authentication import TokenAuthentication
from base.models import MyOwnToken

class MyOwnTokenAuthentication(TokenAuthentication):
    model = MyOwnToken