from HttpHelper import HTTP
from rest_framework.viewsets import ModelViewSet


class Api(ModelViewSet):

    @staticmethod
    def heartbeat(_):
        return HTTP.response(200, '')
