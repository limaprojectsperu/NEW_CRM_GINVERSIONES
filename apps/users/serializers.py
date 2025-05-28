from rest_framework import serializers
from .models import Marca, Users, UserTokens, Permissions, Perfiles, PerfilPermissions

class MarcaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Marca
        fields = '__all__'

class UsersSerializer(serializers.ModelSerializer):
    class Meta:
        model = Users
        fields = '__all__'
        extra_kwargs = {
            'password': {'write_only': True}
        }

class UserTokensSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserTokens
        fields = '__all__'

class PermissionsSerializer(serializers.ModelSerializer):
    class Meta:
        model = Permissions
        fields = '__all__'

class PerfilesSerializer(serializers.ModelSerializer):
    class Meta:
        model = Perfiles
        fields = '__all__'

class PerfilPermissionsSerializer(serializers.ModelSerializer):
    class Meta:
        model = PerfilPermissions
        fields = '__all__'