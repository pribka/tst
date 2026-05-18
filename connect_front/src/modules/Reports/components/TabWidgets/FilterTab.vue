<template>
    <div>
        <div class="mb-3 flex items-center h-[36px]">
            <a-button 
                v-if="complexFilterMode"
                :type="isMobile ? 'ui' : 'ui'"
                :shape="isMobile ? 'circle' : undefined"
                :flaticon="isMobile"
                icon="fi-rr-add"
                class="mr-1" 
                @click="addFilterGroup">
                <template v-if="!isMobile">
                    {{ $t('Add group') }}
                </template>
            </a-button>
            <a-button 
                v-if="hasFilters"
                type="ui"
                @click="resetFilters" 
                flaticon
                class="flex items-center"
                icon="fi-rr-cross-small"
                iconClass="mt-0.5"
                iconRight>
                {{ $t('Clear') }}
            </a-button>
            <div class="ml-auto flex items-center">
                <a-switch 
                    id="filterModeSwitch"
                    v-model="complexFilterMode"
                    size="small" />
                <label class="ml-2 cursor-pointer" for="filterModeSwitch">{{ $t('Complex filter') }}</label>
            </div>
        </div>
        <component :is="filterWidget" />
    </div>
</template>

<script>
import { mapState } from 'vuex'
export default {
    computed: {
        ...mapState({
            isMobile: state => state.isMobile
        }),
        activeMetadata() {
            return this.$store.state.reports.activeTemplate.metadata
        },
        hasFilters() {
            const filtersKey = this.complexFilterMode ? 'complexFilters' : 'filters'
            return this.activeMetadata[filtersKey].length
        },
        complexFilterMode: {
            get() {
                return this.$store.state.reports.activeTemplate.complexFilterMode
            },
            set(newValue) {
                this.$store.state.reports.activeTemplate.complexFilterMode = newValue
            }
        },
        filterWidget() {
            if (this.complexFilterMode) {
                return () => import('./ComplexFilterRoot.vue')
            }
            return () => import('./FilterList.vue')
        }
    },
    methods: {
        addFilterGroup() {
            this.$store.commit('reports/ADD_FILTER_GROUP')
        },
        resetFilters() {
            if (this.complexFilterMode) {
                this.$store.state.reports.activeTemplate.metadata.complexFilters.splice(0)
            } else {
                this.$store.state.reports.activeTemplate.metadata.filters.splice(0)
            }
        },
    }
}
</script>
