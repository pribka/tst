<template>
    <div>
        <div
            class="popover_input ant-input flex items-center relative ant-input-lg truncate"
            :class="disabled && 'disabled'"
            :title="value ? value.name : placeholder"
            @click="openSelect">
            <a-tooltip v-if="value" :title="value.name" destroyTooltipOnHide class="mr-2">
                <a-tag color="blue" class="tag_block truncate">
                    {{ value.name }}
                </a-tag>
            </a-tooltip>
            <span v-else class="dummy_placeholder">{{ placeholder }}</span>
            <a-button
                class="ml-auto"
                flaticon
                size="small"
                icon="fi-rr-angle-small-down"
                shape="circle"
                style="max-height: 20px;max-width: 20px;min-width: 20px;"
                type="ui_ghost" />
        </div>

        <DrawerTemplate
            v-model="visible"
            :width="windowWidth"
            :title="title"
            :wrapClassName="drawerWrapClass"
            @close="visible = false">
            <div class="drawer_content">
                <a-input-search
                    class="mb-2 search_input"
                    :loading="searchLoading"
                    v-model="search"
                    @input="onSearch"
                    :placeholder="$t('support.searchLabel')" />

                <div class="drawer_list">
                    <div
                        v-for="item in itemList"
                        :key="item.id"
                        :title="item.name"
                        :class="checkSelected(item)"
                        class="cursor-pointer wiki_item py-2 flex items-center truncate"
                        @click="selectEntity(item)">
                        <div class="truncate">{{ item.name }}</div>
                    </div>

                    <div v-if="page === 1 && loading" class="flex justify-center mt-2">
                        <a-spin size="small" />
                    </div>

                    <infinite-loading
                        ref="wikiInfinite"
                        :identifier="infiniteId"
                        :force-use-infinite-wrapper="infiniteWrapperSelector"
                        @infinite="getItemList"
                        v-bind:distance="10">
                        <div slot="spinner"><a-spin v-if="page !== 1" size="small" /></div>
                        <div slot="no-more"></div>
                        <div slot="no-results"></div>
                    </infinite-loading>
                </div>
            </div>

            <template #footer>
                <a-button type="ui_ghost" size="large" block @click="visible = false">
                    {{ $t('support.close') }}
                </a-button>
            </template>
        </DrawerTemplate>
    </div>
</template>

<script>
import DrawerTemplate from '@/components/DrawerTemplate.vue'
import mixin from './mixins'

export default {
    components: {
        DrawerTemplate
    },
    mixins: [mixin],
    computed: {
        drawerWrapClass() {
            return `wiki_select_mobile_drawer_${this._uid}`
        },
        infiniteWrapperSelector() {
            return `.${this.drawerWrapClass} .drawer_body`
        }
    }
}
</script>

<style lang="scss" scoped>
.dummy_placeholder{
    color: #888888;
}
.popover_input.disabled{
    opacity: 0.6;
    cursor: not-allowed;
}
.drawer_list{
    width: 100%;
}
.drawer_content{
    width: 100%;
}
.wiki_item{
    transition: all 0.3s cubic-bezier(0.645, 0.045, 0.355, 1);
    border-radius: 8px;
    margin-bottom: 3px;
    &:hover,
    &.active{
        background: #f7f9fc;
    }
}
.search_input{
    &::v-deep{
        .ant-input{
            background: #f7f9fc;
            border-color: #f7f9fc;
            box-shadow: initial!important;
            min-height: 36px;
            color: var(--text);
        }
    }
}
</style>
