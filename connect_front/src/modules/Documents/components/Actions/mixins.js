import eventBus from '@/utils/eventBus'
import { mapState } from 'vuex'
const loadingKey = 'doc_loading'
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
        }
    },
    computed: {
        ...mapState({
            user: state => state.user.user
        }),
        isAuthor() {
            // return this.user && this.record?.director?.id === this.user.id
            return false
        }
    },
    data() {
        return {
            loading: false,
            actionLoading: false,
            actionsList: null,
            visible: false,
            listVisible: false
        }
    },
    methods: {
        async documentSign() {
            try {
                this.$message.loading({ content: 'Отправка документа', key: loadingKey })
                const { data } = await this.$http.post(`/contractor_docs/${this.id}/send/`)
                if(data) {
                    this.$message.success({ content: 'Документ успешно отправлен на подпись', key: loadingKey })
                    eventBus.$emit('update_doc_list', data)
                }
            } catch(e) {
                console.log(e)
                this.$message.error({ content: 'Ошибка отправки', key: loadingKey })
            }
        },
        openDocument() {
            const query = Object.assign({}, this.$route.query)
            if(query.document && Number(query.document) !== this.record.id || !query.document) {
                query.document = this.record.id
                this.$router.push({query})
            }
        },
        documentDownload() {
            window.open(this.record.doc_file.path, 'Download')
            /*this.$nextTick(() => {
                this.$refs.downloadModal.openModal(this.record)
            })*/
        },
        deleteHanlder() {
            this.$confirm({
                title: 'Вы действительно хотите удалить документ?',
                content: '',
                okText: 'Удалить',
                okType: 'danger',
                zIndex: 2000,
                closable: true,
                maskClosable: true,
                cancelText: 'Закрыть',
                onOk: () => {
                    return new Promise((resolve, reject) => {
                        this.$http.post('/table_actions/update_is_active/', {
                            id: this.id,
                            is_active: false
                        })
                            .then(() => {
                                this.$message.success('Документ удален')
                                eventBus.$emit('docTableReload')
                                this.visible = false
                                resolve()
                            })
                            .catch(e => {
                                console.log(e)
                                reject(e)
                            })
                    })
                }
            })
        },
        copyDocument() {
            eventBus.$emit('copy_document', this.record)
        },
        edit() {
            eventBus.$emit('edit_document', this.record)
        },
        openActionDrawer() {
            this.visible = true
            this.visibleChange(this.visible)
        },
        visibleChange(visible) {
            if(visible) {
                this.getActions()
                this.listVisible = true
            } else {
                this.clearActions()
                this.listVisible = false
            }
        },
        async getActions() {
            try {
                this.actionLoading = true
                const { data } = await this.$http.get(`/contractor_docs/${this.id}/action_info/`)
                if(data?.actions) {
                    this.actionsList = data.actions
                }
            } catch(e) {
                this.$message.error(this.$t('error'))
            } finally {
                this.actionLoading = false
            }
        },
        clearActions() {
            this.actionsList = null
        }
    }
}