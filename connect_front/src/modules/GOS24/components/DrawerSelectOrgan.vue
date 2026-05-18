<template>
    <div :class="[!buttonMode && !hide && 'user_draw_input ant-input flex items-center relative', inputClass, size, disabled && 'ant-input-disabled']">
        <template v-if="buttonMode && !hide">
            <a-button
                :type="buttonType"
                :size="buttonSize"
                @click="open()"
                :block="buttonBlock"
                :icon="buttonIcon"
                :disabled="buttonDisabled"
                :loading="buttonLoading">
                {{buttonText}}
            </a-button>
        </template>

        <template v-else-if="!hide">
            <template v-if="checkMultiple">
                <template v-if="multiple">
                    <template v-if="value && value.length">
                        <a-tag
                            color="blue"
                            class="tag_block"
                            @click="open()">
                            <div class="flex items-center">
                                {{ value[0].title }}
                            </div>
                        </a-tag>
                        <a-popover class="mr-2">
                            <template slot="content">
                                <div class="user_pop_scroll">
                                    <template v-for="(item, index) in value">
                                        <template v-if="index !== 0">
                                            <div
                                                :key="`o_${index}`"
                                                class="flex items-center user_popup_item">
                                                {{ item.title }}
                                            </div>
                                        </template>
                                    </template>
                                </div>
                            </template>
                            <a-tag v-if="value.length > 1" color="blue" class="tag_block" @click="open()">
                                + {{ value.length - 1 }}
                            </a-tag>
                        </a-popover>
                        <a-button
                            @click="clearList()"
                            type="link"
                            icon="close-circle"
                            class="px-0 text-current remove_users" />
                    </template>
                </template>
                <Profiler v-else :user="value" class="mr-2">
                    <a-tag color="blue" class="tag_block" @click="open()">
                        <div class="flex items-center">
                            {{ value.title }}
                        </div>
                    </a-tag>
                </Profiler>
            </template>
            <a-button
                @click="open()"
                type="link"
                class="px-0">
                {{ selectButtonText }}
            </a-button>
        </template>

        <DrawerTemplate
            :title="driwerTitle"
            :width="isMobile ? windowWidth : 380"
            :destroyOnClose="true"
            @close="visible = false"
            @afterVisibleChange="afterVisibleChange"
            v-model="visible">
            <template>
                <div :class="showAddEmployeeButton && 'show_add_button'">
                    <!-- Поиск по title / code (DRF SearchFilter -> ?search=) -->
                    <div class="px-3 py-2">
                        <a-input
                            v-model="search"
                            :placeholder="'Поиск по названию'"
                            allowClear
                            class="search-input"
                            @input="onSearch" />
                    </div>

                    <div class="drawer_scroll">
                        <ul class="bordered-items">
                            <li
                                v-for="element in listFilter"
                                :key="element.id"
                                class="cursor-pointer item py-3"
                                @click="selectUser(element)">
                                <div class="flex items-center justify-between px-3">
                                    {{ element.title }}
                                    <div v-if="showRadio && multiple">
                                        <a-radio :checked="checkSelected(element)" />
                                    </div>
                                </div>
                            </li>
                        </ul>

                        <infinite-loading
                            ref="infinite"
                            @infinite="scrollHandler"
                            :identifier="infiniteId"
                            v-bind:distance="10">
                            <div slot="spinner"><a-spin v-if="page !== 1" /></div>
                            <div slot="no-more"></div>
                            <div slot="no-results"></div>
                        </infinite-loading>
                    </div>
                </div>
            </template>

            <template #footer>
                <div class="w-full flex">
                    <a-button
                        v-if="showAddEmployeeButton"
                        type="primary"
                        size="large"
                        class="mr-2 w-full"
                        @click="addUsers">
                        {{ $t('Add') }}
                    </a-button>
                    <a-button
                        type="ui"
                        class="w-full"
                        ghost
                        size="large"
                        @click="visible = false">
                        {{ $t('Close') }}
                    </a-button>
                </div>
            </template>
        </DrawerTemplate>
    </div>
</template>

<script>
let timer;
import InfiniteLoading from 'vue-infinite-loading'
import eventBus from '@/utils/eventBus'
//import OldSelected from '@apps/DrawerSelect/OldSelected.vue'
import { mapActions } from 'vuex'

export default {
    components: {
        InfiniteLoading,
        DrawerTemplate: () => import('@/components/DrawerTemplate.vue')
        // OldSelected
    },
    props: {
        accessGroup: { type: Object, default: () => {} },
        value: { type: [Object, Array, String] },
        id: { type: [String, Number] },
        taskId: { type: [String, Number], default: () => null },
        multiple: { type: Boolean, default: false },
        title: { type: String, default: "" },
        buttonMode: { type: Boolean, default: false },
        buttonType: { type: String, default: 'primary' },
        buttonText: { type: String, default: '' },
        buttonBlock: { type: Boolean, default: false },
        buttonIcon: { type: String, default: '' },
        buttonSize: { type: String, default: 'default' },
        buttonDisabled: { type: Boolean, default: false },
        buttonLoading: { type: Boolean, default: false },
        hide: { type: Boolean, default: false },
        excludeUsers: { type: Array, default: () => [] },
        showRadio: { type: Boolean, default: true },
        inputClass: { type: String, default: '' },
        inputSize: { type: String, default: 'default' },
        filters: { type: Object, default: () => {} },
        disabled: { type: Boolean, default: false },
        oldSelected: { type: Boolean, default: true },
        parentId: { type: String, default: null },
        showAddEmployeeButton: { type: Boolean, default: false },
        isDepartment: { type: Boolean, default: false },
        isDirectorSelect: { type: Boolean, default: false },
        fromOrganization: { type: String, default: null },
        organizationId: { type: String, default: null },
    },
    data() {
        return {
            driwerTitle: this.title ? this.title : this.$t('task.select_user'),
            searchLoading: false,
            search: '',
            visible: false,
            userList: [],
            scrollStatus: true,
            page: 0,
            pageSize: 15,
            pageName: 'organ_select',
            infiniteId: 'organ_select',
            loading: false,
            isUserListLoading: false, // важно для защиты от двойной загрузки
        }
    },
    computed: {
        selectButtonText() {
            return Array.isArray(this.value) && this.value.length ? 'Изменить' : 'Выбрать'
        },
        size() {
            return this.inputSize === 'large' ? 'ant-input-lg' : 'default'
        },
        listFilter() {
            if(this.excludeUsers.length) {
                return this.userList.filter(u => !this.excludeUsers.includes(u.id))
            }
            return this.userList
        },
        windowWidth() {
            return this.$store.state.windowWidth
        },
        checkMultiple() {
            return this.multiple ? Array.isArray(this.value) && this.value.length : !!this.value
        },
        checkName() {
            return this.value?.full_name || `${this.value?.last_name || ''} ${this.value?.first_name || ''}`.trim()
        },
        isMobile() {
            return this.$store.state.isMobile
        },
    },
    watch: {
        filters() {
            this.page = 0
            this.userList = []
            this.scrollStatus = true
            this.resetInfinite()
        }
    },
    methods: {
        ...mapActions({
            addEmployees: 'organization/addEmployees'
        }),
        getPopupContainer() {
            return document.querySelector('.us_dr_bd')
        },
        afterVisibleChange(vis) {
            if(!vis) {
                this.page = 0
                this.userList = []
                this.scrollStatus = true
                this.search = ''
                this.resetInfinite()
            } else {
                if (!this.userList.length) this.resetInfinite()
            }
        },
        clearList() {
            this.$emit('input', Array.isArray(this.value) ? [] : '')
        },
        checkNameList(user) {
            return user?.full_name || `${user?.last_name || ''} ${user?.first_name || ''}`.trim()
        },
        checkSelected(user) {
            if(this.multiple) {
                return Array.isArray(this.value) && this.value.findIndex(u => u.id === user.id) !== -1
            }
            return this.value && user.id === this.value.id
        },
        open() {
            if(!this.disabled) this.visible = true
        },
        onSearch() {
            clearTimeout(timer)
            this.searchLoading = true
            timer = setTimeout(() => {
                this.page = 0
                this.userList = []
                this.scrollStatus = true
                this.resetInfinite()
                this.searchLoading = false
            }, 500)
        },
        resetInfinite() {
            this.infiniteId = `${this.pageName}_${Date.now()}`
        },
        async scrollHandler($state) {
            if (this.isUserListLoading) return
            const params = {
                page: this.page + 1,
                page_size: this.pageSize,
                page_name: this.pageName,
            }
            if (this.search && this.search.trim().length) {
                params.search = this.search.trim() // DRF SearchFilter -> OfficialClarificationOrganListView(search_fields=['title'])
            }
            if (this.filters && Object.keys(this.filters).length) {
                params.filters = this.filters
            }

            const url = `/content_item_gos24/organ/`

            this.isUserListLoading = true
            try {
                const { data } = await this.$http.get(url, { params })
                if (Array.isArray(data.results) && data.results.length) {
                    this.userList.push(...data.results)
                }
                if (data.next) {
                    this.page += 1
                    $state.loaded()
                } else {
                    $state.complete()
                }
            } catch (e) {
                console.error(e)
                $state.complete()
            } finally {
                this.isUserListLoading = false
            }
        },
        selectUser(element) {
            if (this.multiple) {
                const users = Array.isArray(this.value) ? [...this.value] : []
                const idx = users.findIndex(u => u.id === element.id)
                if (idx !== -1) users.splice(idx, 1)
                else users.push(element)
                this.$emit('input', users)
            } else {
                this.$emit('input', element)
                this.visible = false
            }
        },
        addUsers() {
            if (this.accessGroup?.id) {
                this.addUsersToAccessGroup()
            } else {
                this.addUsersToOrganization()
            }
        },
        addUsersToAccessGroup() {
            const url = `contractor_permissions/access_groups/${this.accessGroup.id}/members/add/`
            const payload = {
                contractor: this.fromOrganization,
                members: [ ...this.value.map(user => user.id) ]
            }
            this.$http.post(url, payload)
                .then(() => {
                    this.$emit('userAdded')
                    this.clearUserList()
                    this.closeDrawer()
                })
                .catch(error => {
                    this.$message.error('Не удалось добавить сотрудника')
                    console.error(error)
                })
        },
        async addUsersToOrganization() {
            const user = await this.addEmployees({
                newEmployeeList: this.value,
                parentId: this.parentId,
                key: this.organizationId,
                isDepartment: this.isDepartment,
                pageSize: this.pageSize
            })

            if(!user.created) {
                const message = `Пользователь ${user.full_name} уже состоит в ${this.isDepartment ? 'отделе' : 'организации'}`
                this.$message.warning(message)
            }
            this.clearUserList()
            this.closeDrawer()
        },
        closeDrawer() {
            this.visible = false
        }
    },
    mounted(){
        eventBus.$on('open_user_task_drawer', (id)=>{
            if(id === this.id) this.open()
        })
    },
    beforeDestroy(){
        eventBus.$off('open_user_task_drawer')
    }
}
</script>

<style lang="scss" scoped>
.user_popup_item{
    &:not(:last-child){ margin-bottom: 8px; }
}
.user_pop_scroll{
    max-height: 150px;
    overflow-y: auto;
    overflow-x: hidden;
}
.user_draw_input{
    .remove_users{
        right: 0;
        top: 50%;
        position: absolute;
        margin-top: -16px;
    }
}
.user_select_driwer{
    .ant-drawer-content,
    .ant-drawer-wrapper-body{
        overflow: hidden;
    }
    .ant-drawer-body{
        padding: 0px;
    }
    .search-input{
        border-radius: 0px;
        height: 39px;
        border: 0px;
    }
    .drawer_body{
        .drawer_scroll{
            height: 100%;
            overflow-y: auto;
            overflow-x: hidden;
            .item{
                &:not(:last-child){ border-bottom: 1px solid var(--borderColor); }
                &:hover{ background: var(--hoverBg); }
                .name{
                    display: -webkit-box;
                    -webkit-line-clamp: 2;
                    -webkit-box-orient: vertical;
                    overflow: hidden;
                    text-overflow: ellipsis;
                }
            }
        }
    }
}
</style>
