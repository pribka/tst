<template>
    <a-modal
        v-model="modalVisible"
        :title="title"
        :footer="false"
        :getContainer="getContainer"
        :width="modalWidth"
        destroyOnClose
        @afterVisibleChange="afterVisibleChange"
        wrapClassName="selector">
        <template v-if="$slots.content">
            <transition name="slide-fade">
                <div :class="$slots.content && 'mb-[16px]'">
                    <slot name="content" />
                </div>
            </transition>
        </template>
        <div v-if="windowWidth < 1000" class="tablet" ref="bodyRef">
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
                        :checkSelected="checkSelected"
                        :selectUser="selectUser"
                        :candidates="candidates"
                        :bodyContainer="bodyContainer"
                        :deselectUser="deselectUser"
                        :selectedList="selectedList"
                        :singleSelected="singleSelected"
                        :databaseName="databaseName"
                        :dbId="dbId"
                        v-slot:content
                        class="sidebar">
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
                        :deselectAll="deselectAll"
                        :selectUser="selectUser"
                        :deselectUser="deselectUser"
                        :multiple="multiple" />
                </a-tab-pane>
            </a-tabs>
            <div class="buttons ">
                <a-button type="primary" @click="input">{{ $t('select') }}</a-button>
                <a-button type="ui" ghost @click="modalVisible = false">{{ $t('btn_cancel') }}</a-button>
            </div>
        </div>
        <div v-else class="desktop" ref="bodyRef">
            <SelectorSidebar
                ref="sidebar"
                :pageName="pageName"
                :model="model"
                :oldSelected="oldSelected"
                :oldSelectedVisible="oldSelectedVisible"
                :multiple="multiple"
                :bodyContainer="bodyContainer"
                :checkSelected="checkSelected"
                :selectUser="selectUser"
                :deselectUser="deselectUser"
                :candidates="candidates"
                :selectedList="selectedList"
                :singleSelected="singleSelected"
                :databaseName="databaseName"
                :dbId="dbId"
                v-slot:content
                class="sidebar">
            </SelectorSidebar>
            <div class="right-side">
                <SelectorSelected
                    :selectedList="selectedList"
                    :deselectAll="deselectAll"
                    :selectUser="selectUser"
                    :deselectUser="deselectUser"
                    :multiple="multiple" />
                <div class="buttons">
                    <a-button type="primary" @click="input">{{ $t('select') }}</a-button>
                    <a-button type="ui" ghost @click="modalVisible = false">{{ $t('btn_cancel') }}</a-button>
                </div>
            </div>
        </div>
    </a-modal>
</template>

<script>
export default {
    components: {
        SelectorSidebar: () => import('./SelectorSidebar.vue'),
        SelectorSelected: () => import('./SelectorSelected.vue')
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
        bodyContainer() {
            return this.$refs.bodyRef
        },
        afterVisibleChange(vis) {
            this.$emit('afterVisibleChange', vis)
        }
    }
}
</script>
<style lang="scss">
.selector {
    .ant-modal > .ant-modal-content > .ant-modal-body {
        padding: 16px 20px 24px 20px;
    }
    .desktop {
        width: 100%;
        display: grid;
        grid-template-columns: 1fr 320px;
        column-gap: 16px;
        height: 530px;
        min-height: 0;
        .sidebar {         
            height: 100%;
        }
        .right-side {
            display: flex;
            flex-direction: column;
            gap: 16px;
            min-height: 0;
            height: 100%;
        }
    }
    .tablet {
        height: 530px;
        min-height: 0;
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
    }
}
</style>