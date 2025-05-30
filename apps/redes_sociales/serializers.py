from rest_framework import serializers
from .models import Marca, MessengerPlantilla, EstadoLead, SubEstadoLead

class MarcaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Marca
        fields = '__all__'

class MessengerPlantillaSingleSerializer(serializers.ModelSerializer):
    class Meta:
        model = MessengerPlantilla
        fields = '__all__'

class MessengerPlantillaSerializer(serializers.ModelSerializer):
    marca = MarcaSerializer(source='marca_id', read_only=True)
    
    class Meta:
        model = MessengerPlantilla
        fields = '__all__'


class EstadoLeadSerializer(serializers.ModelSerializer):
    class Meta:
        model = EstadoLead
        fields = '__all__'

class SubEstadoLeadSingleSerializer(serializers.ModelSerializer):
    class Meta:
        model = SubEstadoLead
        fields = '__all__'

class SubEstadoLeadSerializer(serializers.ModelSerializer):
    estado_lead = EstadoLeadSerializer(source='IDEL', read_only=True) 
    id_estado_lead = serializers.PrimaryKeyRelatedField(
        queryset=EstadoLead.objects.all(),
        source='IDEL',
        write_only=True
    )

    class Meta:
        model = SubEstadoLead
        fields = '__all__'