<template>
    <DrawerTemplate
        class="objective-detail-wrapper"
        :title="title"
        :width="width"
        v-model="visible"
        destroyOnClose
        @afterVisibleChange="afterVisibleChange"
        @close="onClose">
        <template slot="title">
            <div class="drawer-title">
                <div class="title">
                    {{ title }}
                </div>
                <div v-if="isEditAvailable" class="edit-button">
                    <a-button
                        type="ui"
                        :loading="loading"
                        v-tippy="{ content: $t('okr.edit') }"
                        shape="circle"
                        ghost
                        icon="fi-rr-edit"
                        flaticon
                        @click="edit" />
                </div>
            </div>
        </template>
        <a-spin class="detail-spin" :spinning="loading">
            <div v-if="objective" class="wrapper">
                <TopInformer ref="top_informer" />
                <a-tabs
                    class="tabs-area"
                    :default-active-key="startTabKey">
                    <a-tab-pane key="keyResults" :tab="$t('okr.keyResults')">
                        <div class="key-results-tab">
                            <KeyResults
                                class="objective-key-results"
                                :keyResults="KRList"
                                :viewOnly="false"
                                :objectiveActions="objective.actions || {}"
                                @reloadData="reloadData" />
                            <Comment
                                class="objective-comments" />
                        </div>
                    </a-tab-pane>
                    <a-tab-pane key="retrospective" :tab="$t('okr.retrospective')">
                        <div class="tab-content-area">
                            <ObjectiveRetrospective
                                class="detail-left-side" />
                            <DrawerAside class="informer">
                                <informer />
                            </DrawerAside>
                        </div>
                    </a-tab-pane>
                    <a-tab-pane key="changeHistory" :tab="$t('okr.changeHistory')">
                        <div class="tab-content-area">
                            <ObjectiveHistory
                                class="detail-left-side" />
                            <DrawerAside class="informer">
                                <informer />
                            </DrawerAside>
                        </div>
                    </a-tab-pane>
                </a-tabs>
            </div>
            <a-empty v-else :description="false" />
        </a-spin>
    </DrawerTemplate>
</template>
<script>
import { mapState, mapActions, mapMutations } from 'vuex'
import eventBus from '@/utils/eventBus'
import Comment from './components/Comment.vue'
import DrawerAside from '@apps/UIModules/DrawerAside'
import DrawerTemplate from '@/components/DrawerTemplate.vue'
import Informer from './components/Informer.vue'
import KeyResults from '@apps/OKR/components/KeyResults'
import ObjectiveHistory from './components/ObjectiveHistory'
import ObjectiveRetrospective from './components/ObjectiveRetrospective'
import TopInformer from './components/TopInformer.vue'
 

export default {
    name: 'ObjectiveDetail',
    components: {
        Comment,
        DrawerAside,
        DrawerTemplate,
        Informer,
        KeyResults,
        ObjectiveHistory,
        ObjectiveRetrospective,
        TopInformer
    },
    data() {
        return {
            visible: false,
            startTabKey: 'keyResults'
        }
    },
    computed: {
        ...mapState({
            KRList: state => state.okr.objectiveKeyResults,
            loading: state => state.okr.objectiveDetailLoading,
            objective: state => state.okr.objectiveDetail,
            reminders: state => state.okr.reminders,
            valueEfforts: state => state.okr.valueEfforts
        }),
        title() {
            return this.objective ? this.objective.objective : ''
        },
        windowWidth() { 
            return this.$store.state.windowWidth
        },
        width() {
            return this.windowWidth < 1683 ? '100%' : '1683px'
        },
        isEditAvailable() {
            return this.objective ? this.objective.actions.edit : false
        }
    },
    created(){
        const query = Object.assign({}, this.$route.query)
        if ('objective' in query) {
            this.fetchData(query.objective)
                .then(() => {
                    this.visible = true
                })
        }
        eventBus.$on('open_objective_details', (objectiveID=null, startTabKey='keyResults') => {
            if (objectiveID) {
                this.fetchData(objectiveID)
                    .then(() => {
                        this.startTabKey = startTabKey
                        this.visible = true
                    })
            } else if (this.objective) {
                this.visible = true
            }
        })
        eventBus.$on('reload_objective_details', () => {
            this.reloadData()
        })
    },
    beforeDestroy(){
        eventBus.$off('open_objective_details')
        eventBus.$off('reload_objective_details')
    },
    methods: {
        ...mapActions({
            fetchDetails: 'okr/fetchObjectiveDetail',
            fetchReminders: 'okr/fetchReminders',
            fetchValueEfforts: 'okr/fetchValueEfforts'
        }),
        ...mapMutations({
            REMOVE_OBJECTIVE_DETAIL: 'okr/REMOVE_OBJECTIVE_DETAIL',
            SET_OBJECTIVE_DETAIL_LOADING: 'okr/SET_OBJECTIVE_DETAIL_LOADING',
            SET_OPEN_TO_EDIT: 'okr/SET_OPEN_TO_EDIT'
        }),
        edit() {
            eventBus.$emit('edit_objective', this.objective.id)
        },
        async fetchData(objectiveID) {
            this.SET_OBJECTIVE_DETAIL_LOADING(true)
            const promises = [this.fetchDetails(objectiveID)]
            if (!this.valueEfforts.length)
                promises.push(this.fetchValueEfforts())
            if (!this.reminders.length)
                promises.push(this.fetchReminders())
            return Promise.all(promises)
                .finally(() => {
                    this.SET_OBJECTIVE_DETAIL_LOADING(false)
                })
        },
        reloadData() {
            this.SET_OBJECTIVE_DETAIL_LOADING(true)
            this.fetchDetails(this.objective.id)
                .then(() => {
                    this.$refs.top_informer.fillForm()
                })
                .finally(() => {
                    this.SET_OBJECTIVE_DETAIL_LOADING(false)
                })
        },
        afterVisibleChange(vis) {
            const query = Object.assign({}, this.$route.query)
            if (vis && this.objective) {
                if (query.objective && query.objective === this.objective.id)
                    return
                this.$router.push({
                    query: {
                        ...query,
                        objective: this.objective.id
                    }
                })
            } else {
                delete query.objective
                this.$router.push({
                    query: query
                })
                this.REMOVE_OBJECTIVE_DETAIL()
            }
        },
        onClose() {
            this.visible = false
        }
    }
}
</script>
<style lang="scss" scoped>
.objective-detail-wrapper {
    overflow: auto;
    .detail-spin::v-deep {
        height: 100%;
        .ant-spin-container {
            height: 100%;
        }
    }
    .wrapper {
        height: 100%;
        display: flex;
        flex-direction: column;
        gap: 20px;
        .tabs-area {
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
                overflow: auto;
                display: flex;
                gap: 30px;
                .detail-left-side {
                    flex: 1;
                }
                .informer {
                    width: 515px;
                    height: min-content; 
                }
            }
            .key-results-tab {
                width: 100%;
                height: 100%;
                overflow: auto;

                .objective-key-results {
                    height: min-content;
                }
                .objective-comments {
                    background-color: #F8F9FD;
                    border-radius: 16px;
                    padding: 12px;
                    height: min-content;
                    margin-top: 24px;
                }
            }
        }
    }
    .drawer-title {
        display: flex;
        justify-content: space-between;
        align-items: center;
        width: 100%;
        gap: 20px;
        margin-right: 15px;
        .title {
            overflow: hidden;
            text-overflow: ellipsis;
            white-space: nowrap;
        }
    }
}
</style>