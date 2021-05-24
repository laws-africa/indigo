from rest_framework.permissions import BasePermission, SAFE_METHODS, DjangoModelPermissions


class ModelPermissions(DjangoModelPermissions):
    """ Similar to DjangoModelPermissions, but read-only operations require view permissions.
    """
    def __init__(self):
        super().__init__()
        perms_map = {
            'GET': ['%(app_label)s.view_%(model_name)s'],
            'HEAD': ['%(app_label)s.view_%(model_name)s'],
            'OPTIONS': ['%(app_label)s.view_%(model_name)s'],
        }
        perms_map.update(self.perms_map)
        self.perms_map = perms_map


class DocumentPermissions(BasePermission):
    """
    Document-level permissions.

    1. read-only changes require view permissions on the document
    2. mutating changes require view and country permissions on the document, and and non-draft (published) documents
       require publication permissions.
    """
    def has_object_permission(self, request, view, obj):
        # all methods require view access
        if not request.user.has_perm('indigo_api.view_document'):
            return False

        # read-only methods only require view access
        if request.method in SAFE_METHODS:
            return True

        # only some users can save/edit non-drafts
        okay = obj.draft or request.user.has_perm('indigo_api.publish_document')

        # check country perms
        okay = okay and request.user.editor.has_country_permission(obj.work.country)

        return okay

    def update_allowed(self, request, serializer):
        # only publishers can change draft to True
        return 'draft' not in serializer.validated_data or \
               serializer.validated_data['draft'] == serializer.instance.draft or \
               request.user.has_perm('indigo_api.publish_document')


class WorkPermissions(BasePermission):
    def has_object_permission(self, request, view, obj):
        # all methods require view access
        if not request.user.has_perm('indigo_api.view_work'):
            return False

        # safe methods require view access
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
        # must have the basic view_document permission
        if not request.user.has_perm('indigo_api.view_document'):
            return

        # so we'll always allow GET, HEAD or OPTIONS requests.
        if request.method in SAFE_METHODS:
            return True

        if obj.id is None:
            return True

        if view.action == 'task':
            # can this user create a task for this annotation?
            return request.user.has_perm('indigo_api.add_task')

        return request.user.is_authenticated and (
            obj.created_by_user == request.user or request.user.is_staff)


class RelatedDocumentPermissions(BasePermission):
    """ Ensure a user has permissions to change resources related to a document.

    1. read-only changes require view permissions on the document
    2. mutating changes require change permissions on the document
    """
    def has_permission(self, request, view):
        return self.has_document_permission(request, view, view.document)

    def has_object_permission(self, request, view, obj):
        return self.has_document_permission(request, view, obj.document)

    def has_document_permission(self, request, view, document):
        if DocumentPermissions().has_object_permission(request, view, document):
            # mutating changes to related resources require document change perms
            return request.method in SAFE_METHODS or request.user.has_perm('indigo_api.change_document')


class RevisionPermissions(RelatedDocumentPermissions):
    def has_object_permission(self, request, view, obj):
        return self.has_document_permission(request, view, view.document)
