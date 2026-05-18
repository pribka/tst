from django.contrib import admin
from common.catalogs.admin import LocalPointInline
from gallery.admin import GalleryModelInline

from . import models


class SportTypesInline(admin.TabularInline):
    model = models.SportFacilityInfoM2MSportTypeModel
    extra = 0
    fk_name = 'sport_facility_info'
    fields = (
        'sport_type',
        'repub_comp',
    )
    autocomplete_fields = ('sport_type',)


class TPSportBuildingModelInline(admin.TabularInline):
    model = models.TPSportFacilityBuildingModel
    extra = 0
    fk_name = 'owner'
    fields = (
        'purpose_type',
        'name',
    )


class TPSportSectionModelInline(admin.TabularInline):
    model = models.TPSportSectionModel
    extra = 0
    fk_name = 'owner'
    fields = (
        'sport_type',
    )


@admin.register(models.SportFacilityInfoModel)
class SportFacilityInfoModelAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'name',
        'organization',
        'location',
        'admin_area',
        'location_point',
        'is_countryside',
        'update_requested',
        'status',
        'is_active',
        'created_at',
        'updated_at',
    )
    readonly_fields = (
        'author',
        'created_at',
        'updated_at',
    )
    list_filter = ('is_active', 'update_requested', 'status',)
    ordering = ('-created_at',)
    autocomplete_fields = ('organization', 'location',)
    inlines = (
        LocalPointInline,
        SportTypesInline,
        TPSportBuildingModelInline,
        TPSportSectionModelInline,
        GalleryModelInline,)
    search_fields = ('name', 'location_points__address', 'location__name')


@admin.register(models.SportFacilityOwnershipFormModel)
class SportFacilityOwnershipFormModelAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'name',
        'code',
        'created_at',
        'is_active',
    )
    readonly_fields = ('author', 'created_at', 'updated_at',)
    ordering = ('-created_at',)


@admin.register(models.SportFacilityHeatingTypeModel)
class SportFacilityHeatingTypeModelAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'name',
        'code',
        'created_at',
        'is_active',
    )
    readonly_fields = ('author', 'created_at', 'updated_at',)
    ordering = ('-created_at',)


@admin.register(models.SportFacilityTypeModel)
class SportFacilityTypeModelAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'name',
        'parent',
        'full_name',
        'code',
        'sort',
        'created_at',
        'is_active',
    )
    readonly_fields = ('author', 'created_at', 'updated_at',)
    ordering = ('-created_at',)
    list_editable = ('sort',)


@admin.register(models.SportFacilityPurposeModel)
class SportFacilityPurposeModelAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'name',
        'parent',
        'code',
        'created_at',
        'is_active',
    )
    readonly_fields = ('author', 'created_at', 'updated_at',)
    ordering = ('-created_at',)


@admin.register(models.SportFacilityStatusModel)
class SportFacilityStatusAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'name',
        'code',
        'created_at',
        'is_active',
        'color',
        'hex_color',
    )
    readonly_fields = (
        'author', 'created_at', 'updated_at',
    )
    ordering = ('sort', 'name',)


@admin.register(models.SportTypeCategoryModel)
class SportTypeCategoryModelAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'name',
        'full_name',
        'parent',
        'code',
        'created_at',
        'is_active',
    )

    readonly_fields = ('author', 'created_at', 'updated_at',)
    ordering = ('sort', 'name',)
    search_fields = ('name', 'code', 'full_name',)


@admin.register(models.SportTypeModel)
class SportTypeModelAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'name',
        'full_name',
        'category',
        'code',
        'created_at',
        'is_active',
    )

    readonly_fields = ('author', 'created_at', 'updated_at',)
    ordering = ('sort', 'name',)
    search_fields = ('name', 'code', 'full_name',)


class RenovationWorksInline(admin.TabularInline):
    model = models. SportFacilityRenovationWorkModel
    fields = (
        'work_type',
    )
    extra = 0
    fk_name = 'renovation_info'
    autocomplete_fields = ('work_type',)


@admin.register(models.SportFacilityRenovationInfoModel)
class SportFacilityRenovationInfoModelAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'sport_facility',
        'renovation_type',
        'renovation_date',
        'is_active',
        'created_at',
        'updated_at',
        'author',
    )
    readonly_fields = ('created_at', 'updated_at', 'deleted_at', 'author',)
    inlines = (RenovationWorksInline,)
    ordering = ('-created_at',)


@admin.register(models.SportFacilityRenovationTypeModel)
class SportFacilityRenovationTypeModelAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'name',
        'code',
        'created_at',
        'sort',
        'is_active',
    )
    readonly_fields = ('created_at', 'updated_at', 'deleted_at', 'author',)
    ordering = ('sort', 'name',)


@admin.register(models.SportFacilityRenovationWorkTypeModel)
class SportFacilityRenovationWorkTypeModelAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'code',
        'full_name',
        'parent',
        'created_at',
        'sort',
        'is_active',
    )
    search_fields = ('code', 'name',)
    ordering = ('sort', 'full_name',)
    autocomplete_fields = ('parent',)


class SportBuildingPurposeTypeThrough(admin.TabularInline):
    model = models.SportBuildingPurposeTypeThroughModel
    fields = (
        'building_type',
    )
    ordering = ('-created_at',)
    fk_name = 'purpose'
    extra = 0


@admin.register(models.SportBuildingPurposeModel)
class SportBuildingPurposeModelAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'code',
        'name',
        'sort',
        'is_active',
        'created_at',
        'updated_at',
    )
    search_fields = ('code', 'name',)
    readonly_fields = ('author', 'created_at', 'updated_at',)
    inlines = (SportBuildingPurposeTypeThrough,)


class SportBuildingTypePurposeThrough(admin.TabularInline):
    model = models.SportBuildingPurposeTypeThroughModel
    fields = (
        'purpose',
    )
    ordering = ('-created_at',)
    fk_name = 'building_type'
    extra = 0


@admin.register(models.SportBuildingTypeModel)
class SportBuildingTypeModelAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'code',
        'name',
        'sort',
        'is_active',
        'created_at',
        'updated_at',
    )
    search_fields = ('code', 'name',)
    readonly_fields = ('author', 'created_at', 'updated_at',)
    inlines = (SportBuildingTypePurposeThrough,)


@admin.register(models.SportBuildingTechnicalConditionModel)
class SportBuildingTechnicalConditionModelAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'code',
        'name',
        'sort',
        'is_active',
        'created_at',
        'updated_at',
        'deleted_at',
    )
    search_fields = ('code', 'name',)
    readonly_fields = ('author', 'created_at', 'updated_at',)


@admin.register(models.SportBuildingFloorCoveringTypeModel)
class SportBuildingFloorCoveringTypeModelAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'code',
        'name',
        'sort',
        'is_active',
        'created_at',
        'updated_at',
        'deleted_at',
    )
    search_fields = ('code', 'name',)
    readonly_fields = ('author', 'created_at', 'updated_at',)


# Кружки/секции
@admin.register(models.SportGroupTypeCatalog)
class SportGroupTypeCatalogAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'code',
        'name',
        'name_plural',
        'sort',
        'is_active',
        'created_at',
        'updated_at',
    )
    search_fields = ('code', 'name', 'name_plural',)
    readonly_fields = ('author', 'created_at', 'updated_at',)


@admin.register(models.SportCoachTypeCatalog)
class SportCoachTypeCatalogAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'code',
        'name',
        'name_plural',
        'sort',
        'is_active',
        'created_at',
        'updated_at',
    )
    search_fields = ('code', 'name', 'name_plural',)
    readonly_fields = ('author', 'created_at', 'updated_at',)