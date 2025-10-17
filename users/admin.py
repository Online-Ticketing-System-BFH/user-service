from django.contrib import admin, messages
from unfold.admin import ModelAdmin
from .models import UserProfile

@admin.register(UserProfile)
class UserProfileAdmin(ModelAdmin):
    list_display = ('email', 'username', 'full_name', 'phone', 'created_at', 'deleted_at')
    list_filter = ('gender', 'created_at', 'updated_at', 'deleted_at')
    search_fields = ('email', 'username', 'first_name', 'last_name', 'phone')
    readonly_fields = ('auth_id', 'email', 'username', 'created_at', 'updated_at')
    actions = ['soft_delete_selected', 'restore_selected', 'hard_delete_selected']

    fieldsets = (
        ('Authentication', {
            'fields': ('auth_id', 'email', 'username')
        }),
        ('Personal Information', {
            'fields': ('first_name', 'last_name', 'phone', 'date_of_birth', 'gender')
        }),
        ('Additional Information', {
            'fields': ('address',)
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at', 'deleted_at')
        }),
    )

    def get_queryset(self, request):
        return UserProfile.objects.all()

    def has_add_permission(self, request):
        return False

    def delete_model(self, request, obj):
        obj.soft_delete()
        self.message_user(request, "Soft-deleted 1 profile", level=messages.INFO)


    def get_actions(self, request):
        actions = super().get_actions(request)
        actions.pop('delete_selected', None)
        return actions

    def soft_delete_selected(self, request, queryset):
        updated = 0
        for obj in queryset:
            if obj.deleted_at is None:
                obj.soft_delete()
                updated += 1
        self.message_user(request, f"Soft-deleted: {updated}", level=messages.INFO)
    soft_delete_selected.short_description = "Soft delete selected"

    def restore_selected(self, request, queryset):
        restored = queryset.update(deleted_at=None)
        self.message_user(request, f"Restored: {restored}", level=messages.SUCCESS)
    restore_selected.short_description = "Restore selected"

    def hard_delete_selected(self, request, queryset):
        count = queryset.count()
        queryset.delete()
        self.message_user(request, f"Permanently deleted: {count}", level=messages.WARNING)
    hard_delete_selected.short_description = "Hard delete selected (PERMANENT)"

    def full_name(self, obj):
        return f"{obj.first_name} {obj.last_name}".strip() or "-"
    full_name.short_description = "Full Name"
