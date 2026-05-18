from django.contrib import admin
from django.contrib.auth import get_user_model
from django.contrib.auth.admin import UserAdmin
from django.utils.translation import gettext_lazy as _

from common.catalogs.models import ContractorProfileModel

from ehub.models import EhubServerUserModel

from .forms import CustomUserCreationForm, CustomUserChangeForm
from . import models


@admin.register(models.CustomUser)
class CustomUserAdmin(UserAdmin):
    add_form = CustomUserCreationForm
    form = CustomUserChangeForm
    model = models.CustomUser
    list_display = ['username', 'email', 'phone', 'gos24_id', 'last_name', 'first_name', 'date_joined']
    list_editable = ['gos24_id']
    ordering = ['-date_joined', 'email']
    search_fields = ('first_name', 'last_name', 'middle_name', 'email')
    fieldsets = (
        (None, {'fields': ('username', 'email', 'password')}),
        (_('Personal info'), {'fields': ('first_name', 'last_name', 'middle_name', 'password_generated')}),
        (_('Permissions'), {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions'),
        }),
        (_('Important dates'), {'fields': ('last_login', 'date_joined')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'password1', 'password2'),
        }),
    )


class ContractorProfileModelInline(admin.TabularInline):
    model = ContractorProfileModel
    fields = ('contractor',)
    autocomplete_fields = ('contractor',)
    fk_name = 'user'
    extra = 0
    ordering = ('contractor__name', '-created_at',)


class EhubServerUserModelInline(admin.TabularInline):
    model = EhubServerUserModel
    extra = 0
    fk_name = 'user'
    fields = ('server',)


@admin.register(models.ProfileModel)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'phone', 'temporary_blocked', 'created_at')
    autocomplete_fields = ('user', 'avatar', 'header_image', 'default_chat', 'current_contractor', 'current_work',)
    search_fields = ('user__first_name', 'user__last_name', 'user__middle_name', 'user__email',)
    list_editable = ['temporary_blocked']
    inlines = (ContractorProfileModelInline, EhubServerUserModelInline)


@admin.register(models.ResetPasswordModel)
class ResetPasswordModelAdmin(admin.ModelAdmin):
    list_display = (
        "created_at",
        "changed",
        "user",
        "uuid"
    )
    readonly_fields = (
        "created_at",
        "changed",
        "user",
        "uuid",
    )
    ordering = ('-created_at',)
    search_fields = ('user__email',)


@admin.register(models.ProfileTypeModel)
class ProfileTypeAdmin(admin.ModelAdmin):
    list_display = ('code', 'name')


@admin.register(models.ProfileModelOuterID)
class ProfileModelOuterIDAdmin(admin.ModelAdmin):
    list_display = ('outer_id', 'profile', 'email')


@admin.register(models.ProfileModelOuterLeadID)
class ProfileModelOuterLeadIDAdmin(admin.ModelAdmin):
    list_display = ('outer_id', 'profile')


@admin.register(models.C1RoleModel)
class C1RoleModelAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'name',
        'is_active',
        'has_full_access_to_order_tp',
        'has_full_access_to_order_editing',
        'can_create_logistic_task',
    )


@admin.register(models.InviteModel)
class InviteModelAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "contractor",
        "token",
        "created_at",
        "deactivate_at",
        "is_active",
    )
    autocomplete_fields = ("contractor",)
    readonly_fields = ("author", "created_at",)


@admin.register(models.EmailInviteModel)
class EmailInviteModelAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "contractor",
        "token",
        "created_at",
        "deactivate_at",
        "is_active",
        "email",
        "is_sent",
        "is_accepted",
        "accepted_user",
        "workgroup",
    )
    autocomplete_fields = ("contractor", "workgroup",)
    readonly_fields = ("author", "created_at", "accepted_user",)


@admin.register(models.GoogleTokenModel)
class GoogleTokenModelAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "profile",
        "access_token",
        "token_type",
        "refresh_token",
        "disabled"
    )
    autocomplete_fields = ("profile", )


@admin.register(models.GoogleOAuthClientIDsModel)
class GoogleOAuthClientIDsModelAdmin(admin.ModelAdmin):
    list_display = (
        "code",
        "name",
        "client_info"
    )


# @admin.register(models.DidAuthModel)
class DidAuthModelAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'profile',
        'secret',
        'created_at',
        'updated_at',
        'is_active',
    )
    autocomplete_fields = ('profile',)
    readonly_fields = ('author', 'created_at', 'updated_at',)
    ordering = ('-created_at',)
    search_fields = ('profile__user__first_name', 'profile__user__last_name', 'secret', 'created_at',)


@admin.register(models.EntryInfoModel)
class EntryInfoModelAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'user',
        'contractor',
        'data',
        'created_at',
        'updated_at',
        'is_active',
    )
    readonly_fields = ('author', 'created_at', 'updated_at',)
    autocomplete_fields = ('user', 'contractor',)

    search_fields = ('user__user__first_name', 'user__user__last_name', 'user__user__email')


@admin.register(models.LeaveRequestModel)
class LeaveRequestModelAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'phone', 'email',)
    search_fields = ('name', 'phone', 'email',)


@admin.register(models.RequestTypeModel)
class RequestTypeModelAdmin(admin.ModelAdmin):
    list_display = ('code', 'name', 'email',)


@admin.register(models.NewUserInfoModel)
class NewUserInfoModelAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'user',
        'contractor',
        'created_at',
        'updated_at',
        'is_active',
    )
    readonly_fields = ('author', 'created_at', 'updated_at',)
    autocomplete_fields = ('user', 'contractor',)
    search_fields = ('user__user__first_name', 'user__user__last_name', 'user__user__email', 'contractor__name')
