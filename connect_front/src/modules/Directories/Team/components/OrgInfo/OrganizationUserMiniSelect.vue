<template>
    <component
        :is="viewComponent"
        v-bind="componentBinds"
        v-on="$listeners">
        <template #item="{ work }">
            <div class="flex items-center truncate w-full">
                <div class="mr-2 flex-shrink-0">
                    <a-avatar
                        :size="20"
                        icon="team"
                        :src="work.avatar ? work.avatar.path : null" />
                </div>
                <div class="truncate">
                    <div class="truncate">{{ work.full_name }}</div>
                    <div
                        v-if="work.email"
                        class="organization_user_mini_select__email truncate">
                        {{ work.email }}
                    </div>
                </div>
            </div>
        </template>
    </component>
</template>

<script>
export default {
    inheritAttrs: false,
    props: {
        value: { type: [Object, Array, String] },
        organizationId: {
            type: String,
            required: true
        },
        excludedUserIds: {
            type: Array,
            default: () => []
        },
        inputType: {
            type: String,
            default: 'bordered_input'
        },
        placeholder: {
            type: String,
            default: ''
        },
        placement: {
            type: String,
            default: 'bottomLeft'
        },
        pageName: {
            type: String,
            default: 'organization_user_mini_select'
        },
        pageSize: {
            type: Number,
            default: 15
        },
        disabled: {
            type: Boolean,
            default: false
        },
        showIcon: {
            type: Boolean,
            default: false
        },
        showSearch: {
            type: Boolean,
            default: true
        },
        showRecent: {
            type: Boolean,
            default: false
        },
        size: {
            type: String,
            default: 'default'
        },
        getPopupContainer: {
            type: Function,
            default: null
        }
    },
    computed: {
        componentBinds() {
            return {
                ...this.$attrs,
                ...this.$props
            }
        },
        isMobile() {
            return this.$store.state.isMobile
        },
        viewComponent() {
            if (this.isMobile) {
                return () => import('./OrganizationUserMiniSelectWidget/Mobile.vue')
            }

            return () => import('./OrganizationUserMiniSelectWidget/Desktop.vue')
        }
    }
}
</script>

<style lang="scss" scoped>
.organization_user_mini_select__email {
    color: #6b7f99;
    font-size: 12px;
}
</style>
