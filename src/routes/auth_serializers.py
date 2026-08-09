from rest_framework import serializers


class LoginSerializer(serializers.Serializer):
    username = serializers.CharField(max_length=150)
    password = serializers.CharField(write_only=True, style={"input_type": "password"})


class RefreshSerializer(serializers.Serializer):
    refresh = serializers.CharField()


class LogoutSerializer(serializers.Serializer):
    refresh = serializers.CharField()


class UsuarioSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    username = serializers.CharField()
    email = serializers.CharField()
    is_staff = serializers.BooleanField()
    nome = serializers.CharField(source="get_full_name", required=False)


class TokenResponseSerializer(serializers.Serializer):
    refresh = serializers.CharField()
    access = serializers.CharField()
    user = UsuarioSerializer()


class RefreshResponseSerializer(serializers.Serializer):
    access = serializers.CharField()


class MeResponseSerializer(serializers.Serializer):
    autenticado = serializers.BooleanField()
    tipo = serializers.CharField(required=False, allow_null=True)
    usuario = UsuarioSerializer(required=False, allow_null=True)
