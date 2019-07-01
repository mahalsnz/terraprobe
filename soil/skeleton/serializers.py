from rest_framework import serializers

from .models import Farm, Reading

class FarmSerializer(serializers.ModelSerializer):

    class Meta:
        model = Farm
        fields = '__all__'

class ReadingSerializer(serializers.ModelSerializer):

    class Meta:
        model = Reading
        fields = '__all__'
