<template>
    <a-popover
        :placement="placement"
        trigger="click"
        v-model="visible"
        transitionName=""
        :autoAdjustOverflow="autoAdjustOverflow"
        :destroyTooltipOnHide="true"
        overlayClassName="project_popover"
        :getPopupContainer="getPopupContainer"
        @visibleChange="visibleChange">
        <a-button v-if="inputType === 'button'" type="flat" class="sel_p_btn" :title="value ? `${$t('Organization')}: ${value.name}` : $t('Organization')">
            <div v-if="value" class="flex items-center gap-2 truncate">
                {{ $t('Organization') }}:
                <div class="flex items-center truncate">
                    <div class="mr-2">
                        <a-avatar :size="20" icon="team" :key="value.id" :src="workgroupLogoPath(value)" />
                    </div>
                    <span class="truncate">{{ value.name }}</span>
                </div>
            </div>
            <div v-else class="flex items-center">
                <i class="fi fi-rr-folder mr-2" />
                {{ $t('Organization') }}
            </div>
        </a-button>
        <div
            v-else-if="inputType === 'defaultInput'"
            class="popover_input ant-input flex items-center relative ant-input-lg truncate"
            :title="value ? `${$t('project_label')}: ${value.name}` : placeholder">
            <a-tag
                v-if="value"
                :title="value.name"
                color="blue"
                class="tag_block truncate mr-2">
                <div class="flex items-center truncate">
                    <div class="mr-1">
                        <a-avatar :size="15" icon="team" :key="value.id" :src="workgroupLogoPath(value)" />
                    </div>
                    {{value.name}}
                </div>
            </a-tag>
            <a-button type="link" :icon="!value && 'plus'" class="px-0">
                {{value ? $t('task.change') : $t('task.select')}}
            </a-button>
            <a-button v-if="value" @click.stop="clear()" type="link" icon="close-circle" class="px-0 text-current remove_brn" />
        </div>
        <template #content>
            <div class="mb-2 flex items-center gap-2">
                <a-input-search
                    class="search_input"
                    :loading="searchLoading"
                    v-model="search"
                    ref="searchInput"
                    @input="onSearch"
                    :placeholder="$t('org_name')" />
                <div
                    v-if="showDefaultOrganizationSwitcher && user && user.current_contractor"
                    class="cursor-pointer select-none"
                    v-tippy
                    :content="$t('change_default_organization')"
                    @click="openUserSetting()">
                    <a-avatar :size="34" icon="team" :src="workgroupLogoPath(user.current_contractor)" />
                </div>
            </div>

            <div v-if="recentList.length" class="pb-2 px-2 old_select">
                <div class="old_select__label">{{ $t('old_selected') }}</div>
                <div class="flex items-center gap-1">
                    <div
                        v-for="old in recentList"
                        :key="old.id"
                        :title="old.name"
                        class="cursor-pointer old_card"
                        :class="checkSelected(old)"
                        @click="selectWork(old)">
                        <div v-if="checkSelected(old) === 'active'" class="old_active">
                            <i class="fi fi-rr-check" />
                        </div>
                        <a-avatar :size="20" icon="team" :src="workgroupLogoPath(old)" />
                    </div>
                </div>
            </div>

            <div class="popover_list">
                <div
                    v-for="(work, index) in workList"
                    :key="index"
                    :title="work.name"
                    :class="checkSelected(work)"
                    class="cursor-pointer project_item p-2 flex items-center truncate"
                    @click="selectWork(work)">
                    <div>
                        <a-avatar :size="20" icon="team" :src="workgroupLogoPath(work)" />
                    </div>
                    <div class="ml-2 truncate">
                        {{ work.name }}
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
.old_active{
    position: absolute;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 10px;
    z-index: 10;
    color: #fff;
    background: rgba(0, 0, 0, 0.5)
}
.old_card{
    position: relative;
    overflow: hidden;
    border-radius: 50%;
    user-select: none
}
.old_select{
    &__label{
        color: #888888;
        font-size: 12px;
        line-height: 12px;
        margin-bottom: 5px
    }
}
.popover_list{
    max-height: 160px;
    overflow-y: auto;
    max-width: 250px;
    min-width: 250px
}
.project_item{
    transition: all 0.3s cubic-bezier(0.645, 0.045, 0.355, 1);
    border-radius: 8px;
    margin-bottom: 3px;
    &:hover,
    &.active{
        background: #f7f9fc
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
                color: #888888
            }
            .ant-input-suffix{
                color: var(--text)
            }
        }
    }
}
.sel_p_btn{
    max-width: 300px
}
</style>

<style lang="scss">
.project_popover{
    .ant-popover-arrow{
        display: none
    }
    &.ant-popover-placement-bottom,
    &.ant-popover-placement-bottomLeft,
    &.ant-popover-placement-bottomRight{
        padding-top: 10px
    }
}
</style>
