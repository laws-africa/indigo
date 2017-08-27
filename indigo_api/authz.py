from rest_framework.permissions import BasePermission, SAFE_METHODS


class DocumentPermissions(BasePermission):
    """
    Document-level permissions.

    Only some users can publish documents.
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
        return obj.draft or request.user.has_perm('indigo_api.publish_document')


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
            obj.created_by_user == request.user
            or request.user.is_staff)
