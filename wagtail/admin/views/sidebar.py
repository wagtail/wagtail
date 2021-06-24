from rest_framework import serializers
from rest_framework.response import Response
from rest_framework.views import APIView


class SidebarPreferencesSerializer(serializers.Serializer):
    collapsed = serializers.BooleanField(initial=False)


class SetSidebarPreferencesView(APIView):
    http_method_names = ['post']

    def post(self, request):
        ser = SidebarPreferencesSerializer(data=request.data)
        ser.is_valid(raise_exception=True)

        request.session['sidebar_preferences'] = ser.data
        return Response(data=ser.data)
