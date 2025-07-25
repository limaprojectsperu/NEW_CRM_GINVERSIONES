from rest_framework import serializers
from .models import Users, UserTokens, Perfiles, Acceso, AccesoPerfil

class UsersSerializer(serializers.ModelSerializer):
    perfil = serializers.SerializerMethodField()

    class Meta:
        model = Users
        fields = '__all__'
        extra_kwargs = {
            'password': {'write_only': True},
            'password_app': {'write_only': True}
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

class PerfilesSerializer(serializers.ModelSerializer):
    class Meta:
        model = Perfiles
        fields = '__all__'

class AccesoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Acceso
        fields = ['acceso_id', 'acceso', 'icono', 'estado']

class AccesoPerfilSerializer(serializers.ModelSerializer):
    class Meta:
        model = AccesoPerfil
        fields = ['acceso_id', 'perfil_id']

class AccesoTreeSerializer(serializers.Serializer):
    id = serializers.CharField()
    label = serializers.CharField()
    children = serializers.ListField(child=serializers.DictField(), required=False)