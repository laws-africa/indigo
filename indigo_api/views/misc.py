from django.http import HttpResponse

from rest_framework.response import Response
from rest_framework.decorators import permission_classes, api_view
from rest_framework.permissions import IsAuthenticated
from rest_framework.authtoken.models import Token


def ping(request):
    return HttpResponse("pong", content_type="text/plain")


@api_view(['POST'])
@permission_classes((IsAuthenticated,))
def new_auth_token(request):
    Token.objects.filter(user=request.user).delete()
    token, _ = Token.objects.get_or_create(user=request.user)
    return Response({'auth_token': token.key})
