from rest_framework import serializers
from .models import vsw_reading, Site, Farm, ReadingType, vsw_strategy

class FarmSerializer(serializers.ModelSerializer):

    class Meta:
        model = Farm
        fields = '__all__'

class SiteSerializer(serializers.ModelSerializer):

    class Meta:
        model = Site
        fields = '__all__'

class ReadingTypeSerializer(serializers.ModelSerializer):

    class Meta:
        model = ReadingType
        fields = '__all__'

class VSWSerializer(serializers.ModelSerializer):
    site = SiteSerializer(many=False, read_only=True, required=False)
    farm = FarmSerializer(many=False, read_only=True, required=False)
    reading_type = ReadingTypeSerializer(many=False, read_only=True, required=False)
    class Meta:
        model = vsw_reading
        fields = '__all__'

class VSWStrategySerializer(serializers.ModelSerializer):
    site = SiteSerializer(many=False, read_only=True, required=False)
    reading_type = ReadingTypeSerializer(many=False, read_only=True, required=False)
    class Meta:
        model = vsw_strategy
        fields = '__all__'
