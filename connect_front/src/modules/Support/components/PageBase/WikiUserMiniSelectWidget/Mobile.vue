<template>
    <div>
        <a-button type="flat_primary" :disabled="disabled" flaticon icon="fi-rr-plus" @click="openSelect">
            {{ $t('support.addEmployee') }}
        </a-button>

        <DrawerTemplate
            v-model="visible"
            :width="windowWidth"
            :wrapClassName="drawerWrapClass"
            :title="$t('support.addEmployee')"
            @close="visible = false">
            <div class="drawer_content">
                <a-input-search
                    v-if="showSearch"
                    class="mb-2 search_input"
                    :loading="searchLoading"
                    v-model="search"
                    ref="searchInput"
                    @input="onSearch"
                    :placeholder="$t('employee_full_name')" />

                <div class="drawer_list">
                    <div
                        v-for="work in workList"
                        :key="work.id"
                        :title="work.full_name"
                        :class="checkSelected(work)"
                        class="cursor-pointer project_item py-2 flex items-center truncate"
                        @click="selectWork(work)">
                        <div>
                            <a-avatar :size="28" icon="team" :src="work.avatar ? work.avatar.path : null" />
                        </div>
                        <div class="ml-2 truncate">
                            {{ work.full_name }}
                        </div>
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
            return `support_user_mini_select_mobile_drawer_${this._uid}`
        },
        infiniteWrapperSelector() {
            return `.${this.drawerWrapClass} .drawer_body`
        }
    }
}
</script>

<style lang="scss" scoped>
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
