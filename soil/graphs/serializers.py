from rest_framework import serializers
from .models import vsw_reading, vsw_strategy
from skeleton.models import SeasonStartEnd

class VSWSerializer(serializers.ModelSerializer):

    class Meta:
        model = vsw_reading
        fields = '__all__'

class VSWStrategySerializer(serializers.ModelSerializer):

    class Meta:
        model = vsw_strategy
        fields = '__all__'

class VSWDateSerializer(serializers.ModelSerializer):
    class Meta:
        model = SeasonStartEnd
        fields = '__all__'
