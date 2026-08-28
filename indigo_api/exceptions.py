from allauth.account.utils import user_display
from django.utils.translation import gettext as _
from rest_framework import serializers
from rest_framework.exceptions import APIException


def serialize_user(user):
    """The small, stable user representation included in conflict responses."""
    return {
        'id': user.id,
        'display_name': user_display(user),
        'username': user.username,
    }


class DocumentChanged(APIException):
    status_code = 409
    default_code = 'document_changed'

    def __init__(self, document, expected_updated_at):
        current_updated_at = serializers.DateTimeField().to_representation(document.updated_at)
        expected_updated_at = serializers.DateTimeField().to_representation(expected_updated_at)
        updated_by_user = document.updated_by_user
        updated_by_name = user_display(updated_by_user) if updated_by_user else None

        if updated_by_name:
            detail = _(
                'This document was changed by %(user)s after you opened it. '
                'Your changes have not been saved.'
            ) % {'user': updated_by_name}
        else:
            detail = _(
                'This document was changed after you opened it. '
                'Your changes have not been saved.'
            )

        payload = {
            'code': self.default_code,
            'detail': detail,
            'expected_updated_at': expected_updated_at,
            'current_updated_at': current_updated_at,
            'updated_by_user': serialize_user(updated_by_user) if updated_by_user else None,
        }
        super().__init__(detail, self.default_code)
        # APIException recursively converts values to ErrorDetail strings. Keep
        # this conflict response as structured JSON (notably the numeric user id).
        self.detail = payload


class DocumentLocked(APIException):
    status_code = 409
    default_code = 'document_locked'

    def __init__(self, lease):
        detail = _('Saving is currently reserved by %(user)s. You can continue editing.') % {
            'user': user_display(lease.user),
        }
        super().__init__(detail, self.default_code)
        self.detail = {
            'code': self.default_code,
            'detail': detail,
            'holder': serialize_user(lease.user),
            'acquired_at': serializers.DateTimeField().to_representation(lease.acquired_at),
            'expires_at': serializers.DateTimeField().to_representation(lease.expires_at),
        }


class EditLeaseLost(APIException):
    status_code = 409
    default_code = 'edit_lease_lost'

    def __init__(self):
        detail = _('Your saving access has expired or was replaced. Your changes have not been saved.')
        super().__init__(detail, self.default_code)
        self.detail = {'code': self.default_code, 'detail': detail}
