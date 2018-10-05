from rest_framework.permissions import BasePermission, SAFE_METHODS


class DocumentPermissions(BasePermission):
    """
    Document-level permissions.

    Only some users can publish documents.
    Users must have country-level permissions.
    """
    def update_allowed(self, request, serializer):
        # only publishers can change draft to True
        return 'draft' not in serializer.validated_data or\
            serializer.validated_data['draft'] == serializer.instance.draft or\
            request.user.has_perm('indigo_api.publish_document')

    def has_object_permission(self, request, view, obj):
        # so we'll always allow GET, HEAD or OPTIONS requests.
        if request.method in SAFE_METHODS:
            return True

        # only some users can save/edit non-drafts
        okay = obj.draft or request.user.has_perm('indigo_api.publish_document')

        # check country perms
        okay = okay and request.user.editor.has_country_permission(obj.work.country)

        return okay


class WorkPermissions(BasePermission):
    def has_object_permission(self, request, view, obj):
        # so we'll always allow GET, HEAD or OPTIONS requests.
        if request.method in SAFE_METHODS:
            return True
        return request.user.editor.has_country_permission(obj.country)

    def create_allowed(self, request, serializer):
        return request.user.editor.has_country_permission(serializer.validated_data['country']['code'])

    def update_allowed(self, request, serializer):
        return 'country' not in serializer.validated_data or \
            request.user.editor.has_country_permission(serializer.validated_data['country']['code'])


class AnnotationPermissions(BasePermission):
    """
    Annotation-level permissions.

    Only staff and users who created a comment can modify it.
    """
    def has_object_permission(self, request, view, obj):
        # so we'll always allow GET, HEAD or OPTIONS requests.
        if request.method in SAFE_METHODS:
            return True

        if obj.id is None:
            return True

        return request.user.is_authenticated and (
            obj.created_by_user == request.user or request.user.is_staff)


class AttachmentPermissions(BasePermission):
    def has_permission(self, request, view):
        return DocumentPermissions().has_object_permission(request, view, view.document)

    def has_object_permission(self, request, view, obj):
        return DocumentPermissions().has_object_permission(request, view, obj.document)
