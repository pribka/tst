<template>
    <a-popover
        placement="topLeft"
        trigger="click"
        v-model="visible"
        transitionName=""
        :destroyTooltipOnHide="true"
        overlayClassName="calendar_popover"
        :getPopupContainer="getPopupContainer"
        @visibleChange="visibleChange">
        <a-button v-if="inputType === 'button'" type="flat" class="sel_p_btn select-none" :title="value ? `${$t('project_label')}: ${value.string_view}` : $t('project_label')">
            <div v-if="value" class="flex items-center gap-2 truncate">
                {{ $t('project_label') }}:
                <div class="flex items-center truncate">
                    <div class="mr-2">
                        <a-badge :color="value.color" />
                    </div>
                    <span class="truncate">{{value.string_view}}</span>
                </div>
                <div v-if="showClear" class="ml-1" @click.stop="clear()">
                    <i class="fi fi-rr-cross-small flex" />
                </div>
            </div>
            <div v-else class="flex items-center">
                <i class="fi fi-rr-folder mr-2" />
                {{ $t('project_label') }}
            </div>
        </a-button>
        <div v-if="inputType === 'input'" class="ant-input ant-input-ghost select-none cursor-pointer" :title="value ? `${$t('project_label')}: ${value.string_view}` : placeholder">
            <div v-if="value" class="flex items-center truncate">
                <div class="mr-2">
                    <a-badge :color="value.color" />
                </div>
                <span class="truncate">{{value.string_view}}</span>
            </div>
            <div v-else class="dummy_placeholder">
                {{ placeholder }}
            </div>
        </div>
        <div
            v-else-if="inputType === 'defaultInput'"
            class="popover_input ant-input flex items-center justify-between relative ant-input-lg truncate"
            :title="value ? value.string_view : placeholder">
            <a-tag
                v-if="value"
                color="blue"
                class="tag_block truncate">
                <div class="flex items-center truncate">
                    <div class="mr-1">
                        <a-badge :color="value.color" />
                    </div>
                    <span class="truncate">{{value.string_view}}</span>
                </div>
            </a-tag>
            <a-button
                v-if="value"
                @click.stop="clear()"
                type="link"
                icon="close-circle"
                class="px-0 text-current remove_brn flex items-center justify-center ml-1" />
        </div>

        <template #content>
            <a-input-search
                class="mb-2 search_input"
                :loading="searchLoading"
                v-model="search"
                ref="searchInput"
                @input="onSearch"
                placeholder="Введите название" />
            <div class="popover_list">
                <div
                    v-for="work in workList"
                    :key="work.id"
                    :title="work.string_view"
                    :class="checkSelected(work)"
                    class="cursor-pointer project_item p-2 flex items-center truncate"
                    @click="selectWork(work)">
                    <div>
                        <a-badge :color="work.color" />
                    </div>
                    <div class="ml-2 truncate">
                        {{work.string_view}}
                    </div>
                </div>
                <div v-if="page === 1 && loading" class="flex justify-center">
                    <a-spin size="small" />
                </div>
                <infinite-loading :identifier="infiniteId" ref="userInfinite" @infinite="getWorkList" v-bind:distance="10">
                    <div slot="spinner"><a-spin v-if="page !== 1" size="small" /></div>
                    <div slot="no-more"></div>
                    <div slot="no-results"></div>
                </infinite-loading>
            </div>
            <div class="pt-1">
                <a-button type="ui_ghost" block size="small" @click="visible = false">
                    {{ $t('Close') }}
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
.block_title{
    color: #888888;
    font-size: 12px;
    line-height: 12px;
    margin-bottom: 5px;
}
.popover_list{
    max-height: 160px;
    overflow-y: auto;
    max-width: 250px;
    min-width: 250px;
}
.project_item{
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
            &::placeholder{
                color: #888888;
            }
        }
    }
}
.tag_block{
    margin-right: 0;
    max-width: calc(100% - 32px);
}
.popover_input{
    min-height: 40px;
    cursor: pointer;
}
</style>
