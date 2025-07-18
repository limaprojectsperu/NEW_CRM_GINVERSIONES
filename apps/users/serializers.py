from rest_framework import serializers
from .models import Users, UserTokens, Permissions, Perfiles, PerfilPermissions

class UsersSerializer(serializers.ModelSerializer):
    perfil = serializers.SerializerMethodField()

    class Meta:
        model = Users
        fields = '__all__'
        extra_kwargs = {
            'password': {'write_only': True}
        }
        
    def get_perfil(self, obj):
        try:
            perfil_instance = Perfiles.objects.get(co_perfil=obj.co_perfil)
            return {
                'id': perfil_instance.co_perfil,
                'perfil': perfil_instance.nc_perfil
            }
        except Perfiles.DoesNotExist:
            return None

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