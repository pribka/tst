<template>
    <a-popover
        :placement="placement"
        trigger="click"
        v-model="visible"
        transitionName=""
        :destroyTooltipOnHide="true"
        overlayClassName="wiki_select_popover"
        :getPopupContainer="getPopupContainer"
        @visibleChange="visibleChange">
        <div class="popover_input ant-input flex items-center relative ant-input-lg truncate" :class="disabled && 'disabled'" :title="value ? value.name : placeholder">
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
        <template #content>
            <a-input-search
                ref="searchInput"
                class="mb-2 search_input"
                :loading="searchLoading"
                v-model="search"
                @input="onSearch"
                :placeholder="$t('support.searchLabel')" />
            <div class="popover_list">
                <div
                    v-for="item in itemList"
                    :key="item.id"
                    :title="item.name"
                    :class="checkSelected(item)"
                    class="cursor-pointer wiki_item p-2 flex items-center truncate"
                    @click="selectEntity(item)">
                    <div class="truncate">
                        {{ item.name }}
                    </div>
                </div>
                <div v-if="page === 1 && loading" class="flex justify-center">
                    <a-spin size="small" />
                </div>
                <infinite-loading :identifier="infiniteId" ref="wikiInfinite" @infinite="getItemList" v-bind:distance="10">
                    <div slot="spinner"><a-spin v-if="page !== 1" size="small" /></div>
                    <div slot="no-more"></div>
                    <div slot="no-results"></div>
                </infinite-loading>
            </div>
            <div class="pt-1">
                <a-button type="ui_ghost" block size="small" @click="visible = false">
                    {{ $t('support.close') }}
                </a-button>
            </div>
        </template>
    </a-popover>
</template>

<script>
import mixin from './mixins'

export default {
    mixins: [mixin]
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
.popover_list{
    max-height: 180px;
    overflow-y: auto;
    max-width: 280px;
    min-width: 280px;
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
