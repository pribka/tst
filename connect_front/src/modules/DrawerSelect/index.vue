<template>
    <div>
        <template v-if="$slots.openButton">
            <div @click="open">
                <slot name="openButton"></slot>
            </div>
        </template>
        <template v-else-if="buttonNew">
            <a-button type="flat" @click="open" :title="buttonText">
                <template v-if="isEmpty">
                    <i 
                        v-if="buttonIcon" 
                        class="fi mr-2" 
                        :class="buttonIcon" />
                    {{ buttonText }}
                </template>
                <template v-else>
                    <template v-if="multiple">
                        <div v-if="value.length === 1" class="flex items-center gap-2 user_wrapper truncate">
                            <template v-if="selectedShowButtonText">{{ buttonText }}:</template>
                            <div>
                                <a-avatar
                                    :size="20" 
                                    :key="value[0].id"
                                    avResize
                                    :src="value[0].avatar && value[0].avatar.path ? value[0].avatar.path : ''"
                                    icon="user" />
                            </div>
                            <div v-if="showClear" class="ml-1" @click.stop="clearChange()">
                                <i class="fi fi-rr-cross-small" />
                            </div>
                        </div>
                        <div v-else class="flex items-center gap-2" :class="clearButtonRight && 'justify-between'">
                            <template v-if="selectedShowButtonText">{{ buttonText }}:</template>
                            <div class="flex items-center">
                                <template v-if="value && value.length <= 5">
                                    <Profiler 
                                        v-for="item in value" 
                                        :key="item.id" 
                                        :showUserName="false"
                                        class="selected_user_item"
                                        :avatarSize="20"
                                        :user="item" />
                                </template>
                                <template v-else>
                                    <Profiler 
                                        v-for="item in firstFiveUsers" 
                                        :key="item.id" 
                                        :showUserName="false"
                                        :avatarSize="20"
                                        class="selected_user_item"
                                        :user="item" />
                                    <a-popover>
                                        <template slot="content">
                                            <div class="user_pop_scroll truncate">
                                                <div 
                                                    v-for="user in restUsers" 
                                                    :key="`rest_${user.id}`" 
                                                    class="flex items-center user_popup_item truncate">
                                                    <div class="mr-1">
                                                        <a-avatar v-if="user.avatar" :size="20" :src="user.avatar.path" />
                                                        <a-avatar v-else :size="20" icon="user" />
                                                    </div>
                                                    {{ checkNameList(user) }}
                                                </div>
                                            </div>
                                        </template>
                                        <div class="count_tag ml-1">+{{ restCount }}</div>
                                    </a-popover>
                                </template>
                            </div>
                            <div v-if="showClear" @click.stop="clearChange()">
                                <i class="fi fi-rr-cross-small flex" />
                            </div>
                        </div>
                    </template>
                    <div v-else class="flex items-center gap-2 user_wrapper truncate">
                        <template v-if="selectedShowButtonText">{{ buttonText }}:</template>
                        <div>
                            <a-avatar
                                :size="20" 
                                :key="value.id"
                                avResize
                                :src="value.avatar && value.avatar.path ? value.avatar.path : ''"
                                icon="user" />
                        </div>
                    </div>
                </template>
            </a-button>
        </template>
        <template v-else>
            <div :class="[
                !buttonMode &&
                    !hide &&
                    'user_draw_input ant-input flex items-center relative gap-2',
                inputClass,
                size,
                moreTag && 'flex-wrap more_tag',
                disabled && 'ant-input-disabled',
                inputType !== 'default' ? `ant-input-${inputType}` : ''
            ]">
                <template v-if="useIco">
                    <i class="fi fi-rr-user mr-3" />
                </template>
                <template v-if="buttonMode && !hide">
                    <a-button :type="buttonType" :size="buttonSize" @click="open()" :block="buttonBlock"
                              :icon="buttonIcon" :disabled="buttonDisabled" :loading="buttonLoading">
                        {{ buttonText }}
                    </a-button>
                </template>
                <template v-else-if="!hide">
                    <template v-if="checkMultiple">
                        <template v-if="multiple">
                            <template v-if="value && value.length">
                                <template v-if="moreTag">
                                    <Profiler v-for="user in value" :key="user.id" :user="user">
                                        <div class="select_tag" @click="open()">
                                            <div class="flex items-center truncate">
                                                <div class="mr-1">
                                                    <a-avatar :key="user.id" :size="20" icon="user" :src="user.avatar && user.avatar.path
                                                        ? user.avatar.path
                                                        : ''
                                                    " />
                                                </div>
                                                {{ checkNameList(user) }}
                                            </div>
                                        </div>
                                    </Profiler>
                                </template>
                                <template v-else>
                                    <Profiler :user="value[0]">
                                        <div class="select_tag" @click="open()">
                                            <div class="flex items-center truncate">
                                                <div class="mr-1">
                                                    <a-avatar :key="value[0].id" :size="20" icon="user" :src="value[0].avatar && value[0].avatar.path
                                                        ? value[0].avatar.path
                                                        : ''
                                                    " />
                                                </div>
                                                {{ checkNameList(value[0]) }}
                                            </div>
                                        </div>
                                    </Profiler>
                                    <a-popover>
                                        <template slot="content">
                                            <div class="user_pop_scroll truncate">
                                                <template v-for="(item, index) in value">
                                                    <template v-if="index !== 0">
                                                        <div :key="`o_${index}`" class="flex items-center user_popup_item truncate">
                                                            <div class="mr-1">
                                                                <a-avatar v-if="item.avatar" :key="item.id" :size="20"
                                                                          :src="item.avatar.path" />
                                                                <a-avatar v-else :size="20" icon="user" />
                                                            </div>
                                                            {{ checkNameList(item) }}
                                                        </div>
                                                    </template>
                                                </template>
                                            </div>
                                        </template>
                                        <div v-if="value.length > 1" class="select_tag truncate" @click="open()">
                                            {{ $t('more_num', { value: value.length - 1 }) }}
                                        </div>
                                    </a-popover>
                                </template>
                                <div class="remove_users">
                                    <a-button @click="clearList()" type="ui" size="small" ghost shape="circle" icon="fi-rr-cross-small" flaticon class="px-0 text-current" />
                                </div>
                            </template>
                        </template>
                        <Profiler v-else :user="value" class="mr-2">
                            <div v-if="isGhost" class="flex items-center cursor-pointer" @click="open()">
                                <div class="mr-2">
                                    <a-avatar :key="value.id" :size="20" icon="user" :src="value.avatar && value.avatar.path ? value.avatar.path : ''
                                    " />
                                </div>
                                {{ checkName }}
                            </div>
                            <div v-else class="select_tag" @click="open()">
                                <div class="flex items-center truncate">
                                    <div class="mr-1">
                                        <a-avatar :key="value.id" :size="20" icon="user" :src="value.avatar && value.avatar.path ? value.avatar.path : ''
                                        " />
                                    </div>
                                    {{ checkName }}
                                </div>
                            </div>
                        </Profiler>
                    </template>
                    <a-button v-if="!disabled" @click="open()" size="small" type="link" class="px-0">
                        <template v-if="inputPlaceholder.length">
                            <template v-if="multiple">
                                <template v-if="candidates && candidates?.length">
                                    <template v-if="value.length">
                                        {{ value.length ? !isGhost ? $t('task.change') : "" : inputPlaceholder }}
                                    </template>
                                    <span v-else class="blue_color">
                                        {{ $t('specify_user') }} <i class="fi fi-rr-arrow-up-right ml-1" style="font-size: 10px;" />
                                    </span>
                                </template>
                                <template v-else>
                                    {{ value.length ? !isGhost ? $t('task.change') : "" : inputPlaceholder }}
                                </template>
                            </template>
                            <template v-else>
                                <template v-if="candidates && candidates?.length">
                                    <template v-if="value">
                                        {{ value ? !isGhost ? $t('task.change') : "" : inputPlaceholder }}
                                    </template>
                                    <span v-else class="blue_color">
                                        {{ $t('specify_user') }} <i class="fi fi-rr-arrow-up-right ml-1" style="font-size: 10px;" />
                                    </span>
                                </template>
                                <template v-else>
                                    {{ value ? !isGhost ? $t('task.change') : "" : inputPlaceholder }}
                                </template>
                            </template>
                        </template>
                        <template v-else>
                            <template v-if="multiple">
                                <template v-if="candidates && candidates?.length">
                                    <template v-if="value.length">
                                        {{ value.length ? $t('task.change') : $t('task.select') }}
                                    </template>
                                    <span v-else class="blue_color">
                                        {{ $t('specify_user') }} <i class="fi fi-rr-arrow-up-right ml-1" style="font-size: 10px;" />
                                    </span>
                                </template>
                                <template v-else>
                                    {{ value.length ? $t('task.change') : $t('task.select') }}
                                </template>
                            </template>
                            <template v-else>
                                <template v-if="candidates && candidates?.length">
                                    <template v-if="value">
                                        {{ value ? $t('task.change') : $t('task.select') }}
                                    </template>
                                    <span v-else class="blue_color">
                                        {{ $t('specify_user') }} <i class="fi fi-rr-arrow-up-right ml-1" style="font-size: 10px;" />
                                    </span>
                                </template>
                                <template v-else>
                                    {{ value ? $t('task.change') : $t('task.select') }}
                                </template>
                            </template>
                        </template>
                    </a-button>
                </template>
            </div>
        </template>
        <component
            :is="viewComponent"
            ref="viewComponent"
            :visible="visible"
            :title="selectorTitle"
            :selectedList="selectedList"
            :singleSelected="singleSelected"
            :windowWidth="windowWidth"
            :oldSelected="oldSelected"
            :oldSelectedVisible="oldSelectedVisibleComputed"
            :multiple="multiple"
            :checkSelected="checkSelected"
            :selectUser="selectUser"
            :deselectUser="deselectUser"
            :deselectAll="deselectAll"
            :databaseName="databaseName"
            :input="input"
            :candidates="candidates"
            :dbId="dbId"
            :getContainer="getContainer"
            v-slot:content
            @afterVisibleChange="afterVisibleChange"
            @close="visible = false">
            <template v-if="$slots.content">
                <transition name="slide-fade">
                    <slot name="content" />
                </transition>
            </template>
        </component>
    </div>
</template>

<script>
import eventBus from "@/utils/eventBus";
import { errorHandler } from '@/utils/index.js'
export default {
    props: {
        showClear: {
            type: Boolean,
            default: false
        },
        dialogStyle: {
            type: Object,
            default: () => {}
        },
        metadata: {
            type: Object,
            default: () => {}
        },
        inputType: {
            type: String,
            default: "default"
        },
        moreTag: {
            type: Boolean,
            default: false
        },
        changeMetadata: {
            type: Function,
            default: () => {}
        },
        submitHandler: {
            type: Function,
            default: null
        },
        submitButtonText: {
            type: String,
            default: null,
        },
        getContainer: {
            type: Function,
            default: () => document.body
        },
        value: {
            // v-model значение, если multiple false то передаем Object, если true то Array
            type: [Object, Array, String],
        },
        id: {
            type: [String, Number],
            required: true,
        },
        taskId: {
            type: [String, Number],
            default: () => null,
        },
        multiple: {
            // Включить множественный выбор юзеров
            type: Boolean,
            default: false,
        },
        title: {
            // Заголовок Drawer окна
            type: String,
            default: "",
        },
        buttonMode: {
            // Включить вывод кнопки вместо поля, ниже все пропсы связанные с настройкой кнопки
            type: Boolean,
            default: false,
        },
        buttonNew: {
            type: Boolean,
            default: false
        },
        buttonType: {
            // Тип кнопки
            type: String,
            default: "primary",
        },
        buttonText: {
            // Текст кнопки ключем перевода
            type: String,
            default: "",
        },
        buttonBlock: {
            // Сделать кнопку по всю ширину
            type: Boolean,
            default: false,
        },
        buttonIcon: {
            // Иконка кнопки
            type: String,
            default: "",
        },
        buttonSize: {
            // Размер кнопки
            type: String,
            default: "default",
        },
        buttonDisabled: {
            // Отключить кнопку
            type: Boolean,
            default: false,
        },
        buttonLoading: {
            // Загрущик в кнопке
            type: Boolean,
            default: false,
        },
        hide: {
            // Скрыть визуально кнопку и поле
            type: Boolean,
            default: false,
        },
        excludeUsers: {
            // Массив с id юзеров, которых нужно исключить из списка
            type: Array,
            default: () => [],
        },
        showRadio: {
            type: Boolean,
            default: true,
        },
        inputClass: {
            type: String,
            default: "",
        },
        inputSize: {
            type: String,
            default: "default",
        },
        disabled: {
            type: Boolean,
            default: false,
        },
        oldSelected: {
            type: Boolean,
            default: true,
        },
        model: {
            type: String,
            default: "users.ProfileModel",
        },
        pageName: {
            type: String,
            default: 'user_select',
        },
        inputPlaceholder: {
            type: String,
            default: ""
        },
        useIco: {
            type: Boolean,
            default: false
        },
        candidates: {
            type: Array,
            default: () => []
        },
        selectedShowButtonText: {
            type: Boolean,
            default: true
        },
        clearButtonRight: {
            type: Boolean,
            default: false
        }
    },
    data() {
        return {
            touchedSelectedIds: [],
            selected: {},
            zIndex: 1200,
            openedSelectedIds: [],

            infiniteId: new Date(),

            visible: false,
            oldSelectedUsers: [],
            foundUsers: {
                results: [],
            },
            dbId: "user",
            databaseName: "old_select",
            oldSelectedVisible: false,

            pageFilterRef: null,
            searchMode: false,
        };
    },
    computed: {
        oldSelectedVisibleComputed() {
            return this.$store.getters['recentUsers/hasAny']
        },
        firstFiveUsers() {
            return Array.isArray(this.value) ? this.value.slice(0, 5) : []
        },
        restUsers() {
            return Array.isArray(this.value) && this.value.length > 5 ? this.value.slice(5) : []
        },
        restCount() {
            return Array.isArray(this.value) && this.value.length > 5 ? this.value.length - 5 : 0
        },
        searchText() {
            return this.$store.state?.filter?.filtersSearch[this.pageName]
        },
        isGhost() {
            return this.inputType === 'ghost' ? true : false
        },
        user() {
            return this.$store.state.user.user;
        },
        selectorTitle() {
            return this.title || this.$t("task.select_user");
        },
        selectedList() {
            return Object.values(this.selected)
        },
        singleSelected() {
            if (this.multiple) {
                return null
            } else {
                const selectedIDs = Object.keys(this.selected)
                return selectedIDs.length ? selectedIDs[0] : null
            }
        },
        singleValue() {
            if (this.multiple) {
                return null
            } else {
                return Array.isArray(this.value) 
                    ? (this.value[0] ?? null) 
                    : (this.value ?? null)
            }
        },
        viewComponent() {
            if (this.isMobile) {
                return () => import(/* webpackMode: "lazy" */'./SelectorDrawer.vue')
            } else {
                return () => import(/* webpackMode: "lazy" */'./SelectorModal.vue')
            }
        },
        size() {
            if(this.inputSize === "small")
                return "ant-input-sm"
            return this.inputSize === "large" ? "ant-input-lg" : "default";
        },
        windowWidth() {
            return this.$store.state.windowWidth;
        },
        checkMultiple() {
            if (this.multiple) {
                return this.value.length;
            }
            return this.value;
        },
        checkName() {
            if(this.value.last_name || this.value.first_name)
                return this.value.last_name + " " + this.value.first_name
            return this.value.full_name
        },
        isMobile() {
            return this.$store.state.isMobile;
        },
        isEmpty() {
            if(this.multiple)
                return this.value.length ? false : true
            else
                return this.value ? false : true
        }
    },
    methods: {
        afterVisibleChange(vis) {
            this.selected = vis ? this.initSelected() : {}
            if (vis) {
                this.touchedSelectedIds = []
            } else {
                this.touchedSelectedIds = []
            }

            this.$emit('afterVisibleChange', vis)

            if(vis && this.$refs?.viewComponent?.$refs?.sidebar?.$refs?.pageFilter) {
                this.$nextTick(() => {
                    this.$refs.viewComponent.$refs.sidebar.$refs.pageFilter.searchFocus()
                })
            }
        },
        userName(user) {
            return `${user.last_name} ${user.first_name}` // ${this.user.middle_name}
        },
        afterClose() {
            this.zIndex = 1200
            this.reset()
            this.oldSelectedVisible = false
        },
        submit() {
            if (this.submitHandler) {
                this.submitHandler();
            }
            this.closeDrawer();
        },
        getUniqueUsers(arr1, arr2) {
            const combined = [...arr1, ...arr2];

            const uniqueUsers = combined.filter(
                (user, index, self) => index === self.findIndex((u) => u.id === user.id)
            );

            return uniqueUsers;
        },

        closeDrawer() {
            this.visible = false;
        },
        getPopupContainerFilter() {
            return this.$refs.drawer_header;
        },
        getPopupContainer() {
            return document.querySelector(".us_dr_bd");
        },
        clearChange() {
            this.$emit("input", [])
            this.$emit("allClear")
            this.oldSelectedUsers = []
            this.$emit("change", [])
        },
        clearList() {
            this.$emit("input", [])
            this.$emit("allClear")
            this.oldSelectedUsers = []
            this.changeMetadata({ key: this.metadata.key, value: [] })
        },
        clearStateTree() {
            const payload = {
                page_name: "xxx.xxx",
                key: "users.ProfileModel",
                others: {
                    state_tree: [],
                },
            };
            this.$http.post("app_info/chosen_filters/", payload).catch((error) => {
                errorHandler({error})
            });
        },
        checkNameList(user) {
            if (user.last_name && user.first_name) return user.last_name + " " + user.first_name;
            if (user.full_name) return user.full_name;
            return user.last_name + " " + user.first_name;
        },
        checkSelected(user) {
            return user && user?.id && this.selected.hasOwnProperty(user.id)
        },
        async open() {
            if (!this.disabled)  {
                if(this.$route.query?.sprint)
                    this.zIndex = 9999999
                this.visible = true
            }

            this.searchMode = !!this.searchText

            if (!this.$store.getters['recentUsers/isLoaded']) {
                try {
                    await this.$store.dispatch('recentUsers/fetchRecent')
                } catch (error) {
                    errorHandler({error, show: false})
                }
            }
        },
        removeUserFromOldSelected(userId) {
            const index = this.oldSelectedUsers.findIndex(
                (user) => user.id === userId
            );
            this.oldSelectedUsers.splice(index, 1);
        },
        initSelected() {
            if (!this.value) return {}
            if (this.multiple) {
                return this.value.reduce((obj, item) => {
                    obj[item.id] = item
                    return obj
                }, {})
            } else {
                if (Array.isArray(this.value)) {
                    return { [this.value[0].id]: this.value[0] }
                } else {
                    return { [this.value.id]: this.value }
                }
            }
        },
        deselectUser(user) {
            if (!user || user.id == null) return
            this.$delete(this.selected, user.id)
        },
        deselectAll() {
            this.selected = {}
        },
        selectUser(user, oldSelected = null) {
            if (!user || user.id == null) return

            const wasSelected = this.selected.hasOwnProperty(user.id)

            if (wasSelected) {
                this.$delete(this.selected, user.id)
                return
            }

            if (!this.multiple)
                this.selected = {}

            this.$set(this.selected, user.id, user)

            const exists = this.touchedSelectedIds.includes(user.id)
            if (!exists) this.touchedSelectedIds.push(user.id)
        },
        async input() {
            const touchedIds = (this.touchedSelectedIds || []).slice()
            const touchedSet = new Set(touchedIds)

            const map = new Map()
            this.selectedList
                .filter(u => u && u.id != null && touchedSet.has(u.id))
                .forEach(u => map.set(u.id, u))

            const usersForBackend = touchedIds
                .map(id => map.get(id))
                .filter(Boolean)

            const usersForUi = touchedIds
                .slice()
                .reverse()
                .map(id => map.get(id))
                .filter(Boolean)

            if (usersForBackend.length) {
                try {
                    await this.$store.dispatch('recentUsers/saveRecent', {
                        usersForBackend,
                        usersForUi
                    })
                } catch (error) {
                    errorHandler({error, show: false})
                }
            }

            this.$nextTick(() => {
                if (this.multiple) {
                    this.$emit("input", this.getUniqueUsers(this.selectedList, this.oldSelectedUsers))
                    this.$emit('change', this.selectedList)
                } else {
                    this.$emit("input", this.selectedList.length ? this.selectedList[0] : null)
                    this.$emit('change', this.selectedList.length ? this.selectedList[0] : null)
                }
            })
            this.visible = false
        },
        reset() {
            this.infiniteId = new Date()
            this.foundUsers = { results: [] }
            this.params.page = 1
            this.$refs?.userTreeRef?.reset()
        },
    },
    mounted() {
        eventBus.$on("open_user_task_drawer", (id) => {
            if (id === this.id) this.open();
        });
        eventBus.$on(`update_filter_${this.model}_${this.pageName}`, () => {
            this.searchMode = !!this.searchText
            this.reset()
        });
    },
    beforeDestroy() {
        eventBus.$off("open_user_task_drawer");
        eventBus.$off(`update_filter_${this.model}_${this.pageName}`);
    },
};
</script>

<style lang="scss" scoped>
.user-is-not-selected {
    transition: color .3s ease;
    color: #888888;
    cursor: pointer;
    &:hover{
        color: var(--primaryColor);
    }
}
.slide-fade-enter-active {
  transition: all .3s ease;
}
.slide-fade-leave-active {
  transition: all .3s cubic-bezier(1.0, 0.5, 0.8, 1.0);
}
.slide-fade-enter, .slide-fade-leave-to{
  transform: translateY(-10px);
  opacity: 0;
}
.user_filter{
    &::v-deep{
        .filter_clear{
            background: #f7f9fc;
            border-color: #f7f9fc!important;
        }
        .filter_input{
            border-radius: 8px;
            background: #f7f9fc;
            border-color: #f7f9fc!important;
            box-shadow: initial !important;
            color: var(--text);
            .ant-input{
                background: #f7f9fc;
                &::placeholder{
                    color: #888888;
                }
            }
        }
    }
}
.old_select_label{
    color: #888888;
    font-size: 14px;
    line-height: 14px;
}
.user_wrapper{
    max-width: 170px;
}
.selected_user_item{
    &:not(:first-child){
        margin-left: -3px;
    }
}
.select_tag{
    background: #E8EDFA;
    border-radius: 8px;
    height: 28px;
    line-height: 28px;
    padding-left: 10px;
    padding-right: 10px;
}
.ant-input-ghost{
    &.user_draw_input{
        &::v-deep{
            .ant-btn{
                &.ant-btn-link{
                    color: var(--placeholder);
                }
            }
        }
    }
}
.search_wrap {
    margin-bottom: 25px;
}

.user_tree {
    min-height: 0;
    max-height: 400px;
    overflow: auto;
    &.use_content{
        max-height: 250px;
    }
}

.user_popup_item {
    &:not(:last-child) {
        margin-bottom: 8px;
    }
}

.user_pop_scroll {
    max-height: 150px;
    overflow-y: auto;
    overflow-x: hidden;
}

.user_draw_input {
    .remove_users {
        right: 5px;
        top: 0;
        height: 100%;
        position: absolute;
        display: flex;
        margin-top: 0px;
        align-items: center;
    }
    &.more_tag{
        &.ant-input-lg{
            height: initial;
            min-height: 40px;
        }
    }
    &.ant-input-sm{
        min-height: 32px;
        .ant-btn{
            min-height: 32px;
        }
    }
}
.count_tag{
    background: #fff;
    widows: 20px;
    height: 20px;
    min-height: 20px;
    min-width: 20px;
    border-radius: 50%;
    font-size: 12px;
    display: flex;
    align-items: center;
    justify-content: center;
    color: var(--text)!important;
}
.user_select_drawer {
    &::v-deep {
        .filter_pop_wrapper {
            min-width: 100%;
            max-width: 100%;
        }
        .filter_input {
            border: 0px;
        }
    }
}
</style>
