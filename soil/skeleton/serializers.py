from rest_framework import serializers

from .models import Farm, Reading, Site, ReadingType

class ReadingTypeSerializer(serializers.ModelSerializer):

    class Meta:
        model = ReadingType
        fields = '__all__'

class ReadingSerializer(serializers.ModelSerializer):
    type = ReadingTypeSerializer(many=False, read_only=True, required=False)

    class Meta:
        model = Reading
        fields = '__all__'

class SiteSerializer(serializers.ModelSerializer):
    readings = ReadingSerializer(many=True, read_only=True, required=False)

    class Meta:
        model = Site
        fields = '__all__'

class FarmSerializer(serializers.ModelSerializer):

    class Meta:
        model = Farm
        fields = '__all__'
