# core_ai/serializers/conflict_serializer.py
from rest_framework import serializers


class ConflictRequestSerializer(serializers.Serializer):
    """
    Serializer للمدخلات الجديدة (project_id > file_id > version_id).

    ─────────────────────────────────────────────────────────────
    code_vs_code:
        project_id, file_id, version_a_id, version_b_id

    code_vs_doc:
        project_id, file_id, version_id, [doc_version_id]

    full_analysis:
        project_id, file_id, version_a_id, version_b_id
        (التوثيق يُجلب تلقائياً من الـ backend)
    ─────────────────────────────────────────────────────────────
    """

    analysis_type = serializers.ChoiceField(
        choices=["code_vs_code", "code_vs_doc", "full_analysis"],
        default="code_vs_code"
    )
    project_id = serializers.CharField(required=True)
    file_id    = serializers.CharField(required=True)

    # لـ code_vs_code و full_analysis
    version_a_id = serializers.CharField(required=False, allow_null=True, default=None)
    version_b_id = serializers.CharField(required=False, allow_null=True, default=None)

    # لـ code_vs_doc
    version_id     = serializers.CharField(required=False, allow_null=True, default=None)
    doc_version_id = serializers.CharField(
        required=False, allow_null=True, default=None,
        help_text="اختياري - إذا لم يُحدد يجلب الـ backend أحدث توثيق مرتبط"
    )

    def validate(self, data):
        analysis_type = data.get("analysis_type", "code_vs_code")

        if analysis_type in ("code_vs_code", "full_analysis"):
            if not data.get("version_a_id") or not data.get("version_b_id"):
                raise serializers.ValidationError({
                    "version_a_id": "مطلوب لـ code_vs_code و full_analysis",
                    "version_b_id": "مطلوب لـ code_vs_code و full_analysis",
                })

        elif analysis_type == "code_vs_doc":
            if not data.get("version_id"):
                raise serializers.ValidationError({
                    "version_id": "مطلوب لـ code_vs_doc"
                })

        return data
