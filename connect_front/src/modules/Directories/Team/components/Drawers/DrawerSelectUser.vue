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
                        <Profiler 
                            :user="value[0]" 
                            class="mr-2">
                            <a-tag 
                                color="blue" 
                                class="tag_block" 
                                @click="open()">
                                <div class="flex items-center">
                                    <div class="mr-1">
                                        <a-avatar 
                                            :key="value[0].id"
                                            :size="15" 
                                            icon="user"
                                            :src="value[0].avatar && value[0].avatar.path ? value[0].avatar.path : ''" />
                                    </div>
                                    {{checkNameList(value[0])}}
                                </div>
                            </a-tag>
                        </Profiler>
                        <a-popover class="mr-2">
                            <template slot="content">
                                <div class="user_pop_scroll">
                                    <template v-for="(item, index) in value">
                                        <template v-if="index !== 0">
                                            <div 
                                                :key="`o_${index}`" 
                                                class="flex items-center user_popup_item">
                                                <div class="mr-1">
                                                    <a-avatar 
                                                        v-if="item.avatar"
                                                        :size="15" 
                                                        :src="item.avatar.path" />
                                                    <a-avatar 
                                                        v-else
                                                        :size="15"
                                                        icon="user" />
                                                </div>
                                                {{checkNameList(item)}}
                                            </div>
                                        </template>
                                    </template>
                                </div>
                            </template>
                            <a-tag v-if="value.length > 1" color="blue" class="tag_block" @click="open()">
                                + {{value.length-1}}
                            </a-tag>
                        </a-popover>
                        <a-button
                            @click="clearList()"
                            type="link"
                            icon="close-circle"
                            class="px-0 text-current remove_users" />
                    </template>
                </template>
                <Profiler v-else :user="value" class="mr-2 truncate">
                    <a-tag color="blue" class="tag_block" @click="open()">
                        <div class="flex items-center">
                            <div class="mr-1">
                                <a-avatar 
                                    :key="value.id" 
                                    :size="15"  
                                    icon="user" 
                                    :src="value.avatar && value.avatar.path ? value.avatar.path : ''" />
                            </div>
                            <div class="truncate">
                                {{checkName}}
                            </div>
                        </div>
                    </a-tag>
                </Profiler>
            </template>
            <a-button
                @click="open()"
                type="link"
                size="small"
                class="px-0">
                {{ selectButtonText }}
            </a-button>
        </template>
        <DrawerTemplate
            :title="driwerTitle"
            :width="isMobile ? windowWidth : 480"
            :destroyOnClose="true"
            @close="visible = false"
            @afterVisibleChange="afterVisibleChange"
            v-model="visible">
            <template>
                <a-input-search
                    :loading="searchLoading"
                    v-model="search"
                    size="large"
                    class="mb-2 sticky"
                    @input="onSearch"
                    :placeholder="$t('task.user_name')" />
                <div 
                    :class="showAddEmployeeButton && 'show_add_button'">
                    <div class="drawer_scroll">
                        <ul class="bordered-items">
                            <li 
                                v-for="user in listFilter" 
                                :key="user.id"
                                class="cursor-pointer item py-3" 
                                @click="selectUser(user)">
                                <div class="flex items-center justify-between">
                                    <Profiler
                                        :user="user"
                                        initStatus
                                        :avatarSize="32" />
                                    <div v-if="showRadio && multiple" >
                                        <a-radio :checked="checkSelected(user)" />
                                    </div>
                                </div>
                            </li>
                        </ul>
                        <infinite-loading 
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
        <!-- <a-drawer
            :title="'driwerTitle'"
            class="user_select_driwer multiple_select"
            :width="isMobile ? windowWidth : 380"
            :destroyOnClose="true"
            @close="visible = false"
            :zIndex="1200"
            :afterVisibleChange="afterVisibleChange"
            :visible="visible">
        </a-drawer> -->
    </div>
</template>

<script>
let timer;
// import Loader from '../Loader.vue'
import eventBus from '@/utils/eventBus'
//import OldSelected from '@apps/DrawerSelect/OldSelected.vue'
import { mapActions } from 'vuex'
export default {
    components: {
        InfiniteLoading: () => import('vue-infinite-loading'),
        DrawerTemplate: () => import('@/components/DrawerTemplate.vue')
        // Loader,
        // OldSelected
    },
    props: {
        accessGroup: {
            type: Object,
            default: () => {} 
        },
        value: { // v-model значение, если multiple false то передаем Object, если true то Array
            type: [Object, Array, String]
        },
        id: {
            type: [String, Number]
        },
        taskId: {
            type: [String, Number],
            default: () => null
        },
        multiple: { // Включить множественный выбор юзеров
            type: Boolean,
            default: false
        },
        title: { // Заголовок Drawer окна
            type: String,
            default: ""
        },
        buttonMode: { // Включить вывод кнопки вместо поля, ниже все пропсы связанные с настройкой кнопки
            type: Boolean,
            default: false
        },
        buttonType: { // Тип кнопки
            type: String,
            default: 'primary'
        },
        buttonText: { // Текст кнопки ключем перевода
            type: String,
            default: ''
        },
        buttonBlock: { // Сделать кнопку по всю ширину
            type: Boolean,
            default: false
        },
        buttonIcon: { // Иконка кнопки
            type: String,
            default: ''
        },
        buttonSize: { // Размер кнопки
            type: String,
            default: 'default'
        },
        buttonDisabled: { // Отключить кнопку
            type: Boolean,
            default: false
        },
        buttonLoading: { // Загрущик в кнопке
            type: Boolean,
            default: false
        },
        hide: { // Скрыть визуально кнопку и поле
            type: Boolean,
            default: false
        },
        excludeUsers: { // Массив с id юзеров, которых нужно исключить из списка
            type: Array,
            default: () => []
        },
        showRadio: {
            type: Boolean,
            default: true
        },
        inputClass: {
            type: String,
            default: ''
        },
        inputSize: {
            type: String,
            default: 'default'
        },
        filters: {
            type: Object,
            default: ()=> {}
        },
        disabled: {
            type: Boolean,
            default: false
        },
        oldSelected: {
            type: Boolean,
            default: true
        },
        parentId: {
            type: String,
            default: null
        },
        showAddEmployeeButton: {
            type: Boolean,
            default: false
        },
        isDepartment: {
            type: Boolean,
            default: false
        },
        isDirectorSelect: {
            type: Boolean,
            default: false
        },
        fromOrganization: {
            type: String,
            default: null
        },
        organizationId: {
            type: String,
            default: null
        },
        endpoint: {
            type: String,
            default: ''
        }
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
            pageName: 'organization_select_user',
            infiniteId: 'organization_select_user',
            loading: false,
        }
    },
    computed: {
        selectButtonText() {
            return this.value?.length ? this.$t('team.edit') : this.$t('team.select_employee')
        },
        size() {
            if(this.inputSize === 'large')
                return 'ant-input-lg'
            else
                return 'default'
        },
        listFilter() {
            if(this.excludeUsers.length) {
                return this.userList.filter(u => {
                    const find = this.excludeUsers.find(f => f === u.id)
                    if(!find)
                        return u
                })
            } else
                return this.userList
        },
        windowWidth() {
            return this.$store.state.windowWidth
        },
        checkMultiple() {
            if(this.multiple) {
                if(this.value.length)
                    return true
                else
                    return false
            } else {
                if(this.value)
                    return true
                else
                    return false
            }
        },
        checkName() {
            if(this.value.full_name)
                return this.value.full_name
            else
                return this.value.last_name + ' ' + this.value.first_name
        },
        isMobile() {
            return this.$store.state.isMobile
        },
    },
    watch: {
        filters(){
            this.page = 0
            this.userList = []
            this.scrollStatus = true
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
            }
        },
        clearList() {
            this.$emit('input', [])
        },
        checkNameList(user) {
            if(user.full_name)
                return user.full_name
            else
                return user.last_name + ' ' + user.first_name
        },
        checkSelected(user) {
            if(this.multiple) {
                const index = this.value.findIndex(u => u.id === user.id)
                if(index !== -1)
                    return true
                else
                    return false
            } else {
                if(user.id === this.value.id)
                    return true
                else
                    return false
            }
        },
        open() {
            if(!this.disabled)
                this.visible = true
        },
        onSearch() {
            clearTimeout(timer)
            timer = setTimeout(() => {
                this.scrollStatus = true
                this.page = 0
                this.userList = []
                if(this.search.length && this.search.length > 2) {
                    this.getUserSearchList()
                } else {
                    this.getUserList()
                }
            }, 800)
        },
        async scrollHandler($state) {
            if(!this.isUserListLoading) {
                const params = {
                    page: this.page + 1,
                    page_size: this.pageSize,
                    page_name: this.pageName,
                    // exclude_department: this.organizationId 
                }
                let url = (this.isDepartment && this.isDirectorSelect) ? 
                    `users/my_organizations/${this.parentId}/users` : `user/list`
                if(this.fromOrganization) {
                    url = `users/my_organizations/${this.fromOrganization}/users`
                }
                if (this.endpoint) {
                    url = this.endpoint
                }
                
                this.isUserListLoading = true
                try {
                    const { data } = await this.$http.get(url, { params })
                    this.userList.push(...data.results)
                    if(data.next) {
                        this.page += 1 
                        $state.loaded()
                    } else {
                        $state.complete()
                    }
                } catch(error) {
                    console.error(error)
                } finally {
                    this.isUserListLoading = false
                }
            }
        },
        async getUserSearchList($state = null) {
            if(!this.loading && this.scrollStatus) {
                try {
                    this.loading = true
                    this.searchLoading = true
                  
                    this.page = this.page+1
                    const params = {
                        page_size: 15,
                        page: this.page,
                        search: this.search,
                        filters: this.filters
                    }

                    if(this.taskId) {
                        params.task = this.taskId
                    }
                    const url = this.endpoint || '/user/list/'
                    const {data} = await this.$http.get(url, {params})
                    if(data && data.results.length) {
                        this.userList = data.results
                    }
                    if(!data.next) {
                        if($state)
                            $state.complete()
                        this.scrollStatus = false
                    } else {
                        if($state)
                            $state.loaded()
                    }
                } catch(e) {

                } finally {
                    this.searchLoading = false
                    this.loading = false
                }
            }
        },
        async getUserList($state = null) {
            if(!this.loading && this.scrollStatus) {
                try {
                    this.loading = true
                    this.page = this.page+1
                    let params = {
                        page_size: 15,
                        page: this.page,
                        filters: this.filters
                    }

                    if(this.taskId) {
                        params.task = this.taskId
                    }

                    const {data} = await this.$http.get('/user/list_by_task/', {params})
                    if(data && data.results.length)
                        this.userList = this.userList.concat(data.results)
                    if(!data.next) {
                        if($state)
                            $state.complete()
                        this.scrollStatus = false
                    } else {
                        if($state)
                            $state.loaded()
                    }
                } catch(e) {

                } finally {
                    this.loading = false
                }
            }
        },
        selectUser(user) {
            if(this.multiple) {
                let users = this.value
                const index = users.findIndex(u => u.id === user.id)
                if(index !== -1)
                    users.splice(index, 1)
                else
                    users.push(user)
                this.$emit('input', users)
            } else {
                this.$emit('input', user)
                this.visible = false
            }

            // if(this.oldSelected)
            //     this.$refs.oldSelector.saveSelect(user)
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
                    this.$message.error(this.$t('team.failed_to_add_employee'))
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
                const message = this.$t('team.user_already_in_organization', { 
                    name: user.full_name, 
                    type: this.isDepartment ? this.$t('team.department') : this.$t('team.organization') 
                })
                this.$message.warning(message)
            }
            eventBus.$emit('update_filter_catalogs.ContractorModel')
            eventBus.$emit('update_filter_catalogs.ContractorModel_catalogs.ContractorModel_list')
            this.clearUserList()
            this.closeDrawer()
        },
        clearUserList() {
            if(Array.isArray(this.value)) {
                this.value.splice(0)
            } else {
                this.value = ''
            }
        },
        closeDrawer() {
            this.visible = false
        }
    },
    mounted(){
        eventBus.$on('open_user_task_drawer', (id)=>{  
            if(id === this.id)
                this.open()
        })
    },
    beforeDestroy(){
        eventBus.$off('open_user_task_drawer')
    }
}
</script>

<style lang="scss" scoped>
.user_popup_item{
    &:not(:last-child){
        margin-bottom: 8px;
    }
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
        // height: calc(100% - 40px);
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
                &:not(:last-child){
                    border-bottom: 1px solid var(--borderColor);
                }
                &:hover{
                    background: var(--hoverBg);
                }
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
