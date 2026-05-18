<template>
    <div>
        <a-button v-if="inputType === 'button'" type="flat" class="sel_p_btn" :title="value ? `${$t('Organization')}: ${value.name}` : $t('Organization')" @click="openSelect">
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
            :title="value ? `${$t('project_label')}: ${value.name}` : placeholder"
            @click="openSelect">
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

        <DrawerTemplate
            v-model="visible"
            :width="windowWidth"
            :wrapClassName="drawerWrapClass"
            :title="$t('Organization')"
            @close="visible = false">
            <div class="drawer_content">
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

                <div v-if="recentList.length" class="pb-2 old_select">
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
                            <a-avatar :size="28" icon="team" :src="workgroupLogoPath(old)" />
                        </div>
                    </div>
                </div>

                <div class="drawer_list">
                    <div
                        v-for="(work, index) in workList"
                        :key="index"
                        :title="work.name"
                        :class="checkSelected(work)"
                        class="cursor-pointer project_item py-2 flex items-center truncate"
                        @click="selectWork(work)">
                        <div>
                            <a-avatar :size="28" icon="team" :src="workgroupLogoPath(work)" />
                        </div>
                        <div class="ml-2 truncate">{{ work.name }}</div>
                    </div>

                    <div v-if="page === 1 && loading" class="flex justify-center mt-2">
                        <a-spin size="small" />
                    </div>

                    <infinite-loading
                        ref="userInfinite"
                        :identifier="infiniteId"
                        :force-use-infinite-wrapper="infiniteWrapperSelector"
                        @infinite="getWorkList"
                        v-bind:distance="10">
                        <div slot="spinner"><a-spin v-if="page !== 1" size="small" /></div>
                        <div slot="no-more"></div>
                        <div slot="no-results"></div>
                    </infinite-loading>
                </div>
            </div>

            <template #footer>
                <a-button type="ui_ghost" size="large" block @click="visible = false">
                    {{ $t('close') }}
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
            return `org_select_mobile_drawer_${this._uid}`
        },
        infiniteWrapperSelector() {
            return `.${this.drawerWrapClass} .drawer_body`
        }
    }
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
.drawer_list{
    width: 100%;
}
.drawer_content{
    width: 100%;
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
