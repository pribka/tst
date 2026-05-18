<template>
    <div class="consolidation_filters">
        <a-select
            :value="scope"
            style="width: 220px;"
            size="large"
            :getPopupContainer="getPopupContainer"
            :placeholder="$t('workplan.select_type')"
            @change="handleScopeChange">
            <a-select-option
                v-for="item in scopeOptions"
                :key="item.value"
                :value="item.value">
                {{ item.label }}
            </a-select-option>
        </a-select>

        <ProjectSelect
            v-if="scope === 'project'"
            ref="projectSelect"
            :value="relatedObject"
            inputType="defaultInput"
            placement="bottomLeft"
            :autoAdjustOverflow="false"
            :style="isMobile ? 'width: 100%;' : 'max-width: 300px;'"
            @input="$emit('update:relatedObject', $event)" />

        <OrgSelect
            v-if="scope === 'organization' || scope === 'root_organization'"
            ref="orgSelect"
            :value="relatedObject"
            :showDefaultOrganizationSwitcher="false"
            inputType="defaultInput"
            placement="bottomLeft"
            :autoAdjustOverflow="false"
            :style="isMobile ? 'width: 100%;' : 'max-width: 300px;'"
            @input="$emit('update:relatedObject', $event)" />

        <UserDrawer
            v-if="scope === 'user'"
            id="consolidation_user"
            ref="userSelect"
            :value="normalizedUserValue"
            multiple
            :style="isMobile ? 'width: 100%;' : 'max-width: 300px;min-width: 300px;'"
            :inputPlaceholder="$t('workplan.filter_user')"
            :title="$t('workplan.filter_user')"
            @input="$emit('update:relatedObject', $event)" />

        <transition name="slide-in-left">
            <AiButton
                v-if="canRequest"
                type="primary"
                size="large"
                :block="isMobile"
                :loading="generateLoading"
                class="consolidation_filters__action"
                @click="$emit('generate-summary')">
                {{ $t('workplan.ai_consolidation_generate_btn') }}
            </AiButton>
        </transition>
    </div>
</template>

<script>
export default {
    components: {
        AiButton: () => import('@apps/UIModules/AIButton/index.vue'),
        ProjectSelect: () => import("@apps/DrawerSelect/ProjectSelect.vue"),
        OrgSelect: () => import("@apps/DrawerSelect/OrgSelect.vue"),
        UserDrawer: () => import('@apps/DrawerSelect/index.vue')
    },
    props: {
        scope: {
            type: String,
            default: null
        },
        relatedObject: {
            type: [Object, Array, String],
            default: () => null
        },
        scopeOptions: {
            type: Array,
            default: () => []
        },
        isMobile: {
            type: Boolean,
            default: false
        },
        canRequest: {
            type: Boolean,
            default: false
        },
        generateLoading: {
            type: Boolean,
            default: false
        },
        getPopupContainer: {
            type: Function,
            default: (trigger) => trigger?.parentNode || document.body
        }
    },
    computed: {
        normalizedUserValue() {
            return Array.isArray(this.relatedObject) ? this.relatedObject : []
        }
    },
    methods: {
        handleScopeChange(val) {
            this.$emit('update:scope', val)
            if (!this.isMobile) {
                setTimeout(() => this.tryOpenRelatedSelect(val, 0), 100)
            }
        },
        tryOpenRelatedSelect(scopeVal, attempt) {
            if (attempt > 15) return

            const refMap = {
                project: 'projectSelect',
                organization: 'orgSelect',
                root_organization: 'orgSelect',
                user: 'userSelect'
            }
            const refKey = refMap[scopeVal]
            if (!refKey) return

            const ref = this.$refs[refKey]
            if (!ref) {
                setTimeout(() => this.tryOpenRelatedSelect(scopeVal, attempt + 1), 80)
                return
            }

            // ProjectSelect / UserDrawer expose open() directly
            if (typeof ref.open === 'function') {
                ref.open()
                return
            }

            // OrgSelect is a wrapper — open() lives on first child (Desktop/Mobile)
            const child = ref.$children?.[0]
            if (child && typeof child.open === 'function') {
                child.open()
                return
            }

            // Fallback: click the input element
            if (ref.$el) {
                const el = ref.$el.querySelector('input, [role="combobox"], .select_tag, .ant-select-selector')
                if (el) el.click()
                else ref.$el.click()
            }
        }
    }
}
</script>

<style lang="scss" scoped>
.consolidation_filters{
    display: flex;
    align-items: center;
    gap: 10px;
    margin-bottom: 10px;
    &__action{
        flex-shrink: 0;
    }
}

.slide-in-left-enter-active,
.slide-in-left-leave-active {
    transition: opacity .22s ease, transform .22s ease;
}

.slide-in-left-enter,
.slide-in-left-leave-to {
    opacity: 0;
    transform: translateX(-16px);
}

@media (max-width: 768px) {
    .consolidation_filters{
        flex-direction: column;
        align-items: stretch;
        justify-content: stretch;
        gap: 8px;
        > * {
            width: 100% !important;
        }
    }
}
</style>
