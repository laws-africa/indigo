from django.contrib.auth import get_user_model
from rest_framework import serializers

from indigo_api.models import Amendment, Work
from .models import Country


class UserDetailsSerializer(serializers.ModelSerializer):
    """
    Override the default DjangoRestAuth user serializer to include
    extra details.
    """
    permissions = serializers.SerializerMethodField()
    country_code = serializers.CharField(allow_null=True, max_length=2, min_length=2, source='editor.country_code')
    auth_token = serializers.SerializerMethodField()

    class Meta:
        model = get_user_model()
        fields = ('id', 'username', 'email', 'first_name', 'last_name', 'permissions', 'country_code', 'is_staff',
                  'auth_token')
        read_only_fields = ('email', 'is_staff', 'id')

    def get_permissions(self, user):
        return [p for p in user.get_all_permissions() if p.startswith('indigo_api.')]

    def get_auth_token(self, user):
        if self.context['request'].user == user:
            return user.editor.api_token().key

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


class AmendingWorkSerializer(serializers.ModelSerializer):
    numbered_title_localised = serializers.SerializerMethodField()

    class Meta:
        model = Work
        fields = ('frbr_uri', 'title', 'doctype', 'subtype', 'numbered_title_localised')

    def get_numbered_title_localised(self, obj):
        # this is injected so that the numbered title of the amending work is localised to the current document
        if self.context["work_detail_plugin"]:
            return self.context["work_detail_plugin"].work_numbered_title(obj) or obj.title


class WorkAmendmentDetailSerializer(serializers.ModelSerializer):
    amending_work = AmendingWorkSerializer()

    class Meta:
        model = Amendment
        fields = ('amending_work', 'date')
        read_only_fields = fields
