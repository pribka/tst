<template>
    <div class="sidebar-wrapper">
        <user-search
            :multiple="multiple"
            :singleSelected="singleSelected"
            :checkSelected="checkSelected"
            :itemSelect="selectUser" />
        <div class="old-selected" v-show="oldSelected && oldSelectedVisible">
            <h2 class="mb-2.5 old_select_label flex items-center">
                {{ $t("old_selected") }}
                <a-button 
                    v-if="oldSelectedVisible && $store.getters['recentUsers/hasAny']"
                    size="small"
                    class="ml-1"
                    v-tippy
                    :content="$t('remove_old_selected')"
                    shape="circle"
                    :loading="oldSelectedLoading"
                    flaticon
                    icon="fi-rr-trash"
                    type="ui_ghost"
                    @click="clearOldSelected()" />
            </h2>
            <OldSelected 
                ref="oldSelected"
                :showLabel="false"
                :multiple="multiple"
                :bodyContainer="bodyContainer"
                :checkSelected="checkSelected"
                :itemSelect="selectUser"
                :databaseName="databaseName"
                :dbId="dbId"
                :listMaxLength="20" />
        </div>
        <template v-if="isMobile">
            <div class="user-directory">
                <AllUsers
                    :multiple="multiple"
                    :model="model"
                    showCandidates
                    :candidates="candidates"
                    :pageName="pageName"
                    :selectedList="selectedList"
                    :singleSelected="singleSelected"
                    :checkSelected="checkSelected"
                    :itemSelect="selectUser" />
            </div>
        </template>
        <template v-else>
            <a-tabs
                class="user-directory"
                :defaultActiveKey="candidates && candidates.length ? 'candidates' : 'all'">
                <a-tab-pane v-if="candidates && candidates.length" key="candidates">
                    <span slot="tab">
                        <div class="tab-label">
                            <i class="fi fi-rr-comment-user mr-1" />
                            <div class="label">{{ $t('candidates') }}</div>
                        </div>
                    </span>
                    <component
                        :is="candidatesComp"
                        :multiple="multiple"
                        :model="model"
                        :candidates="candidates"
                        :pageName="pageName"
                        :selectedList="selectedList"
                        :singleSelected="singleSelected"
                        :checkSelected="checkSelected"
                        :itemSelect="selectUser" />
                </a-tab-pane>
                <a-tab-pane key="all">
                    <span slot="tab">
                        <div class="tab-label">
                            <i class="fi fi-rr-user mr-1" />
                            <div class="label">{{ $t('all_user') }}</div>
                        </div>
                    </span>
                    <AllUsers
                        :multiple="multiple"
                        :model="model"
                        :pageName="pageName"
                        :selectedList="selectedList"
                        :singleSelected="singleSelected"
                        :checkSelected="checkSelected"
                        :itemSelect="selectUser" />
                </a-tab-pane>
                <a-tab-pane key="orgaizations" >
                    <span slot="tab">
                        <div class="tab-label">
                            <i class="fi fi-rr-sitemap mr-1" />
                            <div class="label">{{ $t('Organizations') }}</div>
                        </div>
                    </span>
                    <Organizations
                        :multiple="multiple"
                        :model="model"
                        :pageName="pageName"
                        :selectedList="selectedList"
                        :singleSelected="singleSelected"
                        :checkSelected="checkSelected"
                        :itemSelect="selectUser"
                        :deselectUser="deselectUser" />
                </a-tab-pane>
                <a-tab-pane key="groups">
                    <span slot="tab">
                        <div class="tab-label">
                            <i class="fi fi-rr-users mr-1" />
                            <div class="label">{{ $t('teams') }}</div>
                        </div>
                    </span>
                    <Groups
                        :multiple="multiple"
                        :model="model"
                        :pageName="pageName"
                        :selectedList="selectedList"
                        :singleSelected="singleSelected"
                        :checkSelected="checkSelected"
                        :itemSelect="selectUser"
                        :deselectUser="deselectUser" />
                </a-tab-pane>
                <a-tab-pane key="projects">
                    <span slot="tab">
                        <div class="tab-label">
                            <i class="fi fi-rr-folder mr-1" />
                            <div class="label">{{ $t('Projects') }}</div>
                        </div>
                    </span>
                    <Projects
                        :multiple="multiple"
                        :model="model"
                        :pageName="pageName"
                        :selectedList="selectedList"
                        :singleSelected="singleSelected"
                        :checkSelected="checkSelected"
                        :itemSelect="selectUser"
                        :deselectUser="deselectUser" />
                </a-tab-pane>
                <a-tab-pane key="outside">
                    <span slot="tab">
                        <div class="tab-label">
                            <i class="fi fi-rr-chart-user mr-1" />
                            <div class="label">{{ $t('outside_users') }}</div>
                        </div>
                    </span>
                    <OutsideUsers
                        :multiple="multiple"
                        :model="model"
                        :pageName="pageName"
                        :selectedList="selectedList"
                        :singleSelected="singleSelected"
                        :checkSelected="checkSelected"
                        :itemSelect="selectUser" />
                </a-tab-pane>
            </a-tabs>
        </template>
    </div>
</template>

<script>
import { errorHandler } from '@/utils/index.js'
export default {
    name: 'Sidebar',
    components: {
        AllUsers: () => import("./UserSelectTabs/AllUsers"),
        Groups: () => import("./UserSelectTabs/Groups"),
        OldSelected: () => import("./OldSelected.vue"),
        Organizations: () => import("./UserSelectTabs/Organizations"),
        OutsideUsers: () => import("./UserSelectTabs/OutsideUsers"),
        Projects: () => import("./UserSelectTabs/Projects"),
        UserSearch: () => import('./UserSearch.vue'),
        Candidates: () => import("./UserSelectTabs/Candidates")
    },
    props: {
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
            default: false
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
        databaseName: {
            type: String,
            default: 'old_select'
        },
        dbId: {
            type: String,
            default: 'old_select'
        },
        selectedList: {
            type: Array,
            default: () => []
        },
        singleSelected: {
            type: [String, null],
            default: null
        },
        candidates: {
            type: Array,
            default: () => []
        },
        bodyContainer: {
            type: Function,
            default: () => document.body
        }
    },
    computed: {
        isMobile() {
            return this.$store.state.isMobile;
        },
        candidatesComp() {
            if(this.candidates?.length)
                return () => import("./UserSelectTabs/Candidates")
            return null
        }
    },
    data() {
        return {
            oldSelectedLoading: false
        }
    },
    methods: {
        async clearOldSelected() {
            try {
                this.oldSelectedLoading = true
                await this.$store.dispatch('recentUsers/clearAll')
            } catch (error) {
                errorHandler({error})
            } finally {
                this.oldSelectedLoading = false
            }
        }
    }
}
</script>

<style lang="scss" scoped>
.sidebar-wrapper {
    height: 100%;
    display: flex;
    flex-direction: column;
    gap: 16px;
    min-height: 0;
    min-width: 0;
    .old-selected {
        margin-bottom: 16px;
    }
    .user-directory {
        flex: 1;
        min-height: 0;
        display: flex;
        flex-direction: column;
        &::v-deep {
            .ant-tabs-content {
                flex: 1;
                min-height: 0;
            }
        }
        .tab-content-area {
            width: 100%;
            height: 100%;
        }
        .tab-label {
            display: flex;
            align-items: center;
            .label {}
        }
    }
}
.user_filter{
    &::v-deep{
        .filter_clear{
            background: rgba(240, 241, 247, 1);
            border-color: rgba(240, 241, 247, 1) !important;
        }
        .filter_input{
            border-radius: 8px;
            background: rgba(240, 241, 247, 1);
            border-color: rgba(240, 241, 247, 1) !important;
            box-shadow: initial !important;
            color: var(--text);
            .ant-input{
                background: rgba(240, 241, 247, 1);
                &::placeholder{
                    color: rgba(136, 136, 136, 1);
                }
            }
        }
    }
}
</style>