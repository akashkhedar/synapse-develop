from django.utils.functional import cached_property


class OrganizationMixin:
    @cached_property
    def active_members(self):
        return self.members.filter(deleted_at__isnull=True)


class OrganizationMemberMixin:
    def has_permission(self, user):
        if user.active_organization_id == self.organization_id:
            return True
        return False





