from rest_framework import serializers
from core_ai.serializers.codefile import ObjectIdField

class AIExplanationSerializer(serializers.Serializer):
    id = ObjectIdField(read_only=True)
    analysis_id = ObjectIdField()
    explanation_type = serializers.CharField(max_length=20) # high_level أو low_level
    content = serializers.CharField()
    created_at = serializers.DateTimeField(read_only=True)

  