from django.contrib.auth import get_user_model
from rest_framework import serializers

from .models import Country


class UserDetailsSerializer(serializers.ModelSerializer):
    """
    Override the default DjangoRestAuth user serializer to include
    extra details.
    """
    permissions = serializers.SerializerMethodField()
    country_code = serializers.CharField(allow_null=True, max_length=2, min_length=2, source='editor.country_code')

    class Meta:
        model = get_user_model()
        fields = ('username', 'email', 'first_name', 'last_name', 'permissions', 'country_code')
        read_only_fields = ('email', )

    def get_permissions(self, user):
        return [p for p in user.get_all_permissions() if p.startswith('indigo_api.')]

    def validate_country_code(self, value):
        if value is not None:
            value = value.upper()
            try:
                Country.objects.get(country_id=value)
            except Country.DoesNotExist:
                countries = [c.country_id for c in Country.objects.all()]
                countries.sort()
                raise serializers.ValidationError("That country is not configured or is invalid. Possibilities are: %s" % ", ".join(countries))
        return value

    def save(self):
        if 'editor' in self.validated_data:
            data = self.validated_data.pop('editor')
            if 'country_code' in data:
                self.instance.editor.country_code = data['country_code']
                self.instance.editor.save()

        super(UserDetailsSerializer, self).save()
