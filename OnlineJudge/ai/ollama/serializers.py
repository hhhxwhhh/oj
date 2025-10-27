from utils.api import serializers
from ai.models import AIModel
class OllamaModelSerializer(serializers.ModelSerializer):
    class Meta:
        model=AIModel
        fields='__all__'
        read_only_fields=('create_time','update_time')