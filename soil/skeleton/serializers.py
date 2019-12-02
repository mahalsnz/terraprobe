from rest_framework import serializers

from .models import Report, Season, Farm, Reading, Site, ReadingType, ETReading, KCReading
from address.models import Address, Locality, State, Country

class ETReadingSerializer(serializers.ModelSerializer):

    class Meta:
        model = ETReading
        fields = '__all__'

class KCReadingSerializer(serializers.ModelSerializer):

    class Meta:
        model = KCReading
        fields = '__all__'

class CountrySerializer(serializers.ModelSerializer):

    class Meta:
        model = Country
        fields = '__all__'

class StateSerializer(serializers.ModelSerializer):
    country = CountrySerializer(many=False, read_only=True, required=False)
    class Meta:
        model = State
        fields = '__all__'

class LocalitySerializer(serializers.ModelSerializer):
    state = StateSerializer(many=False, read_only=True, required=False)

    class Meta:
        model = Locality
        fields = '__all__'

class AddressSerializer(serializers.ModelSerializer):
    locality = LocalitySerializer(many=False, read_only=True, required=False)

    class Meta:
        model = Address
        fields = '__all__'

class ReportSerializer(serializers.ModelSerializer):

    class Meta:
        model = Report
        fields = '__all__'

class SeasonSerializer(serializers.ModelSerializer):

    class Meta:
        model = Season
        fields = '__all__'

class ReadingTypeSerializer(serializers.ModelSerializer):

    class Meta:
        model = ReadingType
        fields = '__all__'

class ReadingSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = Reading
        fields = '__all__'

class SiteSerializer(serializers.ModelSerializer):
    readings = ReadingSerializer(many=True, read_only=True, required=False)
    upper_limit = ReadingTypeSerializer(many=False, read_only=True, required=False)
    lower_limit = ReadingTypeSerializer(many=False, read_only=True, required=False)
    class Meta:
        model = Site
        fields = '__all__'

class FarmSerializer(serializers.ModelSerializer):
    report = ReportSerializer(many=False, read_only=True, required=False)
    address = AddressSerializer(many=False, read_only=True, required=False)

    class Meta:
        model = Farm
        fields = '__all__'
