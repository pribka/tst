<template>
    <a-popover
        :placement="placement"
        :trigger="disabled ? 'none' : 'click'"
        v-model="visible"
        transitionName=""
        :disabled="disabled"
        :destroyTooltipOnHide="true"
        overlayClassName="support_user_mini_popover"
        :getPopupContainer="getPopupContainer"
        @visibleChange="visibleChange">
        <a-button type="flat_primary" :disabled="disabled" flaticon icon="fi-rr-plus">
            {{ $t('support.addEmployee') }}
        </a-button>
        <template #content>
            <a-input-search
                v-if="showSearch"
                class="mb-2 search_input"
                :loading="searchLoading"
                v-model="search"
                ref="searchInput"
                @input="onSearch"
                :placeholder="$t('employee_full_name')" />
            <div class="popover_list">
                <div
                    v-for="work in workList"
                    :key="work.id"
                    :title="work.full_name"
                    :class="checkSelected(work)"
                    class="cursor-pointer project_item p-2 flex items-center truncate"
                    @click="selectWork(work)">
                    <div>
                        <a-avatar :size="20" icon="team" :src="work.avatar ? work.avatar.path : null" />
                    </div>
                    <div class="ml-2 truncate">
                        {{ work.full_name }}
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
.popover_list{
    max-height: 220px;
    overflow-y: auto;
    max-width: 280px;
    min-width: 280px;
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
</style>

<style lang="scss">
.support_user_mini_popover{
    z-index: 999999;
    .ant-popover-arrow{
        display: none;
    }
    &.ant-popover-placement-bottom,
    &.ant-popover-placement-bottomLeft,
    &.ant-popover-placement-bottomRight{
        padding-top: 0px;
    }
    &.ant-popover-placement-top,
    &.ant-popover-placement-topLeft,
    &.ant-popover-placement-topRight{
        padding-bottom: 0px;
    }
}
</style>
