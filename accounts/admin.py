from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import Group

from accounts.models import User, MASTPermissions


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ('username', 'email', 'full_name', 'affiliation', 'is_registered', 'is_active', 'group_list')
    list_filter = ('is_registered', 'is_active', 'is_staff', 'groups')
    search_fields = ('username', 'email', 'first_name', 'last_name', 'affiliation')
    ordering = ('username',)

    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('Personal info', {'fields': ('prefix', 'first_name', 'middle_name', 'last_name', 'email', 'affiliation')}),
        ('Access', {'fields': ('is_active', 'is_registered', 'is_staff', 'groups')}),
    )
    add_fieldsets = (
        (None, {'fields': ('username', 'password1', 'password2')}),
        ('Personal info', {'fields': ('prefix', 'first_name', 'middle_name', 'last_name', 'email', 'affiliation')}),
        ('Access', {'fields': ('is_active', 'is_registered', 'groups')}),
    )

    filter_horizontal = ('groups',)

    actions = ['approve_users', 'deactivate_users']

    @admin.display(description='Groups')
    def group_list(self, obj):
        return ', '.join(g.name for g in obj.groups.all()) or '—'

    @admin.action(description='Approve selected users')
    def approve_users(self, request, queryset):
        updated = queryset.update(is_registered=True, is_active=True)
        self.message_user(request, f'{updated} user(s) approved.')

    @admin.action(description='Deactivate selected users')
    def deactivate_users(self, request, queryset):
        updated = queryset.update(is_active=False)
        self.message_user(request, f'{updated} user(s) deactivated.')


admin.site.unregister(Group)

@admin.register(Group)
class GroupAdmin(admin.ModelAdmin):
    list_display = ('name', 'permission_list')
    filter_horizontal = ('permissions',)

    @admin.display(description='Permissions')
    def permission_list(self, obj):
        return ', '.join(
            p.codename for p in obj.permissions.filter(content_type__app_label='accounts')
        ) or '—'
