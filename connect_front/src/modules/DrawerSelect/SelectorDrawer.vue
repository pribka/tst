<template>
    <DrawerTemplate
        v-model="modalVisible"
        placement="bottom"
        :title="title"
        destroyOnClose
        :getContainer="getContainer"
        @afterVisibleChange="afterVisibleChange"
        @close="handlerClose"
        wrapClassName="selector">
        <div class="mobile">
            <a-tabs
                class="tabs-area"
                default-active-key="sidebar">
                <a-tab-pane key="sidebar">
                    <span slot="tab">
                        <div class="tab-label">
                            <i class="fi fi-rr-user mr-1" />
                            <div class="label">{{ $t('Users') }}</div>
                        </div>
                    </span>
                    <SelectorSidebar
                        ref="sidebar"
                        :pageName="pageName"
                        :model="model"
                        :oldSelected="oldSelected"
                        :oldSelectedVisible="oldSelectedVisible"
                        :multiple="multiple"
                        :candidates="candidates"
                        :checkSelected="checkSelected"
                        :selectUser="selectUser"
                        :deselectUser="deselectUser"
                        :selectedList="selectedList"
                        :singleSelected="singleSelected"
                        :databaseName="databaseName"
                        :dbId="dbId"
                        v-slot:content
                        class="sidebar">
                        <template v-if="$slots.content">
                            <transition name="slide-fade">
                                <slot name="content" />
                            </transition>
                        </template>
                    </SelectorSidebar>
                </a-tab-pane>
                <a-tab-pane key="selected">
                    <span slot="tab">
                        <div class="tab-label">
                            <i class="fi fi-rr-users mr-1" />
                            <div class="label">{{ $t('user_selected', { count: selectedList.length }) }}</div>
                        </div>
                    </span>
                    <SelectorSelected
                        :selectedList="selectedList"
                        :selectUser="selectUser"
                        :deselectUser="deselectUser"
                        :deselectAll="deselectAll"
                        :multiple="multiple" />
                </a-tab-pane>
            </a-tabs>
            <div class="buttons">
                <a-button type="primary" class="select-btn" @click="input">{{ $t('select') }}</a-button>
                <a-button type="ui" ghost class="cancel-btn" @click="modalVisible = false">{{ $t('btn_cancel') }}</a-button>
            </div>
        </div>
    </DrawerTemplate>
</template>

<script>
export default {
    name: 'DrawerSelector',
    components: {
        DrawerTemplate: () => import('@/components/DrawerTemplate.vue'),
        SelectorSelected: () => import('./SelectorSelected.vue'),
        SelectorSidebar: () => import('./SelectorSidebar.vue')
    },
    props: {
        visible: {
            type: Boolean,
            default: false
        },
        title: {
            type: String,
            default: ''
        },
        windowWidth: {
            type: Number,
            required: true
        },
        pageName: {
            type: String,
            default: 'user_select',
        },
        model: {
            type: String,
            default: "users.ProfileModel",
        },
        oldSelected: {
            type: Boolean,
            default: true,
        },
        oldSelectedVisible: {
            type: Boolean,
            default: false
        },
        multiple: {
            type: Boolean,
            default: false
        },
        checkSelected: {
            type: Function,
            default: () => {}
        },
        selectUser: {
            type: Function,
            default: () => {}
        },
        deselectUser: {
            type: Function,
            default: () => {}
        },
        deselectAll: {
            type: Function,
            default: () => {}
        },
        input: {
            type: Function,
            default: () => {}
        },
        databaseName: {
            type: String,
            default: 'old_select'
        },
        dbId: {
            type: String,
            default: 'user'
        },
        selectedList: {
            type: Array,
            default: () => []
        },
        singleSelected: {
            type: [String, null],
            default: null
        },
        getContainer: {
            type: Function,
            default: () => document.body
        },
        candidates: {
            type: Array,
            default: () => []
        }
    },
    computed: {
        modalWidth() {
            return this.windowWidth > 1050 ? 1044 : '100%';
        },
        modalVisible: {
            get() {
                return this.visible
            },
            set() {
                this.$emit('close')
            }
        }
    },
    methods: {
        afterVisibleChange(vis) {
            this.$emit('afterVisibleChange', vis)
        },
        handlerClose() {
            this.$emit('close')
        }
    }
}
</script>
<style lang="scss">
.selector {
    .mobile {
        height: 100%;
        display: flex;
        flex-direction: column;
        gap: 16px;
        .tabs-area {
            flex: 1;
            min-height: 0;
            display: flex;
            flex-direction: column;
            .ant-tabs-content {
                flex: 1;
                min-height: 0;
            }
            .tab-content-area {
                width: 100%;
                height: 100%;
            }
            .tab-label {
                display: flex;
                align-items: center;
            }
        }
    }
    .buttons {
        display: flex;
        gap: 4px;
        width: 100%;
        .select-btn, .cancel-btn {
            flex: 1;
        }
    }
}
</style>