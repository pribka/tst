import eventBus from '@/utils/eventBus'
import { mapState } from 'vuex'
const loadingKey = 'consolidation_deleting'
export default {
    props: {
        id: {
            type: [String, Number],
            required: true
        },
        record: {
            type: Object,
            required: true
        },
        dropTrigger: {
            type: Array,
            default: () => ['click']
        },
        pageName: {
            type: String,
            default: 'consolidations_table'
        }
    },
    computed: {
        ...mapState({
            user: state => state.user.user
        }),
    },
    data() {
        return {
            loading: false,
            actionLoading: false,
            actionsList: [],
            visible: false,
            listVisible: false
        }
    },
    methods: {
        openConsolidation() {
            const query = Object.assign({}, this.$route.query)
            if(!query.consolidation) {
                query.consolidation = this.record.id
                this.$router.push({query})
            }
        },
        deleteHanlder() {
            this.$confirm({
                title: this.$t('Do you really want to delete consolidation') + ` "${this.record.name}"?`,
                content: '',
                okText: this.$t('Delete'),
                okType: 'danger',
                zIndex: 2000,
                closable: true,
                maskClosable: true,
                cancelText: this.$t('Close'),
                onOk: () => {
                    return new Promise((resolve, reject) => {
                        this.$http.post(`/consolidation/${this.id}/delete/`)
                            .then(() => {
                                this.$message.success(this.$t('Consolidation deleted'))
                                eventBus.$emit('consolidationTableReload')

                                eventBus.$emit(`table_row_${this.pageName}`, {
                                    action: 'delete',
                                    row: this.record
                                })
                                this.visible = false
                                resolve()
                            })
                            .catch(e => {
                                console.log(e)
                                this.$message.error({ content: e[0] ? e[0] : this.$t('Error deleting'), key: loadingKey })
                                reject(e)
                            })
                    })
                }
            })
        },
        edit() {
            eventBus.$emit('edit_consolidation', this.record.id)
        },
        async visibleChange(visible) {
            if(visible) {
                await this.getActions()
                this.listVisible = true
            } else {
                this.listVisible = false
                this.clearActions()
            }
        },
        async getActions() {
            try {
                this.actionLoading = true
                const { data } = await this.$http.get(`/consolidation/${this.id}/action_info/`)
                if(data?.actions) {
                    this.actionsList = data.actions
                }
            } catch(e) {
                this.$message.error(this.$t('Error loading actions'))
            } finally {
                this.actionLoading = false
            }
        },
        clearActions() {
            this.actionsList = []
        },
        async documentDownload() {
            this.loading = true
            try {
                const { data } = await this.$http(this.record.consolidation_file.path, {
                    responseType: 'blob'
                })
                if(data) {
                    const url = window.URL.createObjectURL(new Blob([data]))
                    const link = document.createElement('a')
                    link.href = url
                    link.setAttribute('download', `${this.record.consolidation_file.name}.${this.record.consolidation_file.extension}`)
                    document.body.appendChild(link)
                    link.click()
                    link.remove()
                }
            } catch(e) {
                console.log(e)
                this.$message.error(this.$t('Error'))
            } finally {
                this.loading = false
            }
        }
    }
}