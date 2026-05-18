<template>
    <component 
        ref="pageFilter"
        :is="filterWidget"
        :model="model"
        :transitionName="transitionName"
        :page_name="page_name"
        :placement="placement"
        :mode="mode"
        :size="size"
        :showSearch="showSearch"
        :scrollElements="scrollElements"
        :queryParams="queryParams"
        :excludeFields="excludeFields"
        :width="width"
        :vertical="vertical"
        :hideResetBtn="hideResetBtn"
        :hideClearBtn="hideClearBtn"
        :buttonsActive="buttonsActive"
        :zIndex="zIndex"
        :getPopupContainer="getPopupContainer"
        :onlySearch="onlySearch"
        :align="align"
        :filterPrefix="filterPrefix"
        :modelLabel="modelLabel"
        :injectSelectParams="injectSelectParams"
        :forceInit="forceInit"
        :popoverMaxWidth="popoverMaxWidth"
        :initInputFocus="initInputFocus"
        :autoAdjustOverflow="autoAdjustOverflow"
        :filterButtonSize="filterButtonSize" />
</template>

<script>
import { mapState } from 'vuex'
import initProps from './props.js'
export default {
    props: {...initProps},
    computed: {
        ...mapState({
            isMobile: state => state.isMobile
        })
    },
    methods: {
        searchFocus() {
            if(this.$refs.pageFilter)
                this.$refs.pageFilter.searchFocus()
        }
    },
    data() {
        return {
            filterWidget: null
        }
    },
    created() {
        this.filterWidget = this.isMobile
            ? () => import('./Mobile.vue')
            : () => import('./Desktop.vue')
    }
}
</script>
