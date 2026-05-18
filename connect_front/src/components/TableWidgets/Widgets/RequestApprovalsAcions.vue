<template>
    <div class="request_approvals_actions">
        <a-dropdown
            :trigger="['click']"
            v-model="visible"
            @visibleChange="visibleChange"
            :getPopupContainer="getPopupContainer">
            <a-button
                type="ui"
                ghost
                flaticon
                shape="circle"
                :loading="loading"
                size="small"
                icon="fi-rr-menu-dots-vertical"
                :destroyPopupOnHide="false" />
            <a-menu slot="overlay">
                <a-menu-item key="open" class="flex items-center" @click="openHandler()">
                    <i class="fi fi-rr-link-alt mr-2" />
                    {{ $t('approvals.open') }}
                </a-menu-item>
                <template v-if="actions">
                    <a-menu-item v-if="actions.update" key="edit" class="flex items-center" @click="editHandler()">
                        <i class="fi fi-rr-edit mr-2" />
                        {{ $t('edit') }}
                    </a-menu-item>
                    <template v-if="actions.delete">
                        <a-menu-divider />
                        <a-menu-item key="delete" class="flex items-center" @click="deleteItem()">
                            <i class="fi fi-rr-trash mr-2" />
                            {{ $t('remove') }}
                        </a-menu-item>
                    </template>
                </template>
                <a-menu-item v-if="listLoading">
                    <div class="flex justify-center">
                        <a-spin size="small" />
                    </div>
                </a-menu-item>
            </a-menu>
        </a-dropdown>

        <a-button
            v-if="showNewCommentsButton"
            type="link"
            class="new_comments_button"
            :title="$t('workplan.new_comments')"
            @click.stop="openHandler()">
            <i class="fi fi-rr-comment-dots"></i>
        </a-button>
    </div>
</template>

<script>
import eventBus from '@/utils/eventBus'
import { mapState } from 'vuex'
import { errorHandler } from '@/utils/index.js'
export default {
    sockets: {
        notify({ data }) {
            if (
                data?.event_type === 'new_comment_from_object'
                && data?.obj === this.record?.id
            ) {
                if (this.isCurrentApprovalOpen) {
                    this.hasSocketNewComment = false
                    return
                }
                this.hasSocketNewComment = true
            }
        }
    },
    props: {
        main: { // Если вставляем этот компонент куда то помимо страницы задач, тут надо ставить false
            type: Boolean,
            default: false
        },
        record: {
            type: Object,
            required: true
        },
        text: {
            type: [Object, Number, String],
        },
        expandedRowKeys: {
            type: Array,
        },
        expanded: {
            type: Number,
        },
        extendDrawer: {
            type: Boolean,
            default: false
        },
        showChildren: { // Показывать или возможность раскрыть задачу с подзадачами
            type : Boolean,
            default: true
        },
        indent: {
            type: Object,
        },
        column: {
            type: Object,
            default: () => null
        },
        openTask: {
            type: Function,
            default: () => {}
        },
        reloadTask: {
            type: Function,
            default: () => {}
        },
        pageName: {
            type: String,
            default: ''
        },
        colParams: {
            type: Object,
            default: () => null
        }
    },
    computed: {
        ...mapState({
            user: state => state.user.user
        }),
        isCurrentApprovalOpen() {
            return this.$route.query?.approvals === this.record?.id
        },
        showNewCommentsButton() {
            return !this.isCurrentApprovalOpen
                && Boolean(this.record?.has_new_comments || this.hasSocketNewComment)
        }
    },
    watch: {
        'record.id'() {
            this.hasSocketNewComment = false
        },
        isCurrentApprovalOpen(value) {
            if(value) {
                this.hasSocketNewComment = false
            }
        }
    },
    data() {
        return {
            visible: false,
            loading: false,
            listLoading: false,
            actions: null,
            listModel: 'processes.WorkflowRequestModel',
            hasSocketNewComment: false
        }
    },
    created() {
        eventBus.$on('request_approvals_comments_seen', this.handleCommentsSeen)
    },
    beforeDestroy() {
        eventBus.$off('request_approvals_comments_seen', this.handleCommentsSeen)
    },
    methods: {
        handleCommentsSeen({ id, has_new_comments }) {
            if(id !== this.record?.id) return

            this.hasSocketNewComment = false
            this.$set(this.record, 'has_new_comments', has_new_comments)
        },
        editHandler() {
            this.visible = false
            eventBus.$emit(`edit_request_approvals`, this.record)
        },
        deleteItem() {
            this.visible = false
            this.$confirm({
                title: this.$t('approvals.delete_message'),
                closable: true,
                maskClosable: true,
                cancelText: this.$t('cancel'),
                okText: this.$t('remove'),
                okType: 'danger',
                zIndex: 999999,
                onOk: () => {
                    return new Promise((resolve, reject) => {
                        this.$http.post('/table_actions/update_is_active/', [{ id: this.record.id, is_active: false }])
                            .then(() => {
                                this.$message.success(this.$t('approvals.delete_success'))
                                eventBus.$emit(`update_filter_${this.listModel}_${this.pageName}`)
                                this.visible = false
                                resolve()
                            })
                            .catch((error) => {
                                errorHandler({error})
                                reject()
                            })
                    })
                }
            })
        },
        openHandler() {
            this.visible = false

            const query = JSON.parse(JSON.stringify(this.$route.query))
            if(!query.approvals) {
                query.approvals = this.record.id
                this.$router.push({query})
            } else {
                eventBus.$emit('approvals_drawer_close')
                setTimeout(() => {
                    query.approvals = this.record.id
                    this.$router.push({query})
                }, 500)
            }
        },
        async getActions() {
            if(!this.actions) {
                try {
                    this.loading = true
                    this.listLoading = true
                    const { data } = await this.$http.get(`/processes/workflow_requests/${this.record.id}/action_info/`)
                    if(data?.actions) {
                        this.actions = data.actions
                    }
                } catch(error) {
                    errorHandler({error, show: false})
                } finally {
                    this.loading = false
                    this.listLoading = false
                }
            }
        },
        visibleChange(visible) {
            if(visible)
                this.getActions()
        },
        getPopupContainer() {
            return this.colParams.getPopupContainer()
        }
    }
}
</script>

<style lang="scss" scoped>
.request_approvals_actions{
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 5px;
}
.new_comments_button{
    display: inline-flex;
    align-items: center;
    justify-content: center;
    width: 24px;
    height: 24px;
    padding: 0;
    color: #4777ff;
    i{
        font-size: 18px;
        line-height: 1;
    }
}
</style>
