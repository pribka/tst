import eventBus from '@/utils/eventBus'
import { mapState } from 'vuex'
const loadingKey = 'ccounting_reports_deleting'
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
            default: 'accounting_reports_table'
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
        open() {
            eventBus.$emit('view_accounting_report', this.record.id)
        },
        deleteHandler() {
            console.log('this.record', this.record)
            this.$confirm({
                title: `Вы действительно хотите удалить отчет "${this.record.type.name} №${this.record.number}"?`,
                content: '',
                okText: 'Удалить',
                okType: 'danger',
                zIndex: 2000,
                closable: true,
                maskClosable: true,
                cancelText: 'Закрыть',
                onOk: () => {
                    return new Promise((resolve, reject) => {
                        this.$http.post(`/accounting_reports/${this.id}/delete/`)
                            .then(() => {
                                this.$message.success('Отчет удален')
                                eventBus.$emit(`table_row_${this.pageName}`, {
                                    action: 'delete',
                                    row: this.record
                                })
                                this.visible = false
                                resolve()
                            })
                            .catch(e => {
                                console.log(e)
                                this.$message.error({ content: e[0] ? e[0] : 'Ошибка удаления', key: loadingKey })
                                reject(e)
                            })
                    })
                }
            })
        },
        edit() {
            eventBus.$emit('edit_accounting_report', this.record.id)
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
                const { data } = await this.$http.get(`/accounting_reports/${this.id}/action_info/`)
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
            this.actionsList = []
        },
        async download() {
            // TODO Скачивание отчёта
            // this.loading = true
            // try {
            //     const { data } = await this.$http(this.record.consolidation_file.path, {
            //         responseType: 'blob'
            //     })
            //     if(data) {
            //         const url = window.URL.createObjectURL(new Blob([data]))
            //         const link = document.createElement('a')
            //         link.href = url
            //         link.setAttribute('download', `${this.record.consolidation_file.name}.${this.record.consolidation_file.extension}`)
            //         document.body.appendChild(link)
            //         link.click()
            //         link.remove()
            //     }
            // } catch(e) {
            //     console.log(e)
            //     this.$message.error('Ошибка')
            // } finally {
            //     this.loading = false
            // }
        },
        async exportTo1C() {
            if(!this.actionLoading) {
                this.actionLoading = true
                try {
                    const { data } = await this.$http.get(`/accounting_reports/${this.record.id}/get_upload_for_1C/`, {
                        responseType: 'blob'
                    })
                    if(data) {
                        const url = window.URL.createObjectURL(new Blob([data]))
                        const link = document.createElement('a')
                        link.href = url
                        link.setAttribute('download', `Заявка на изменение плана финансирования ${this.$moment().format("DD-MM-YYYY")}.xlsx`)
                        document.body.appendChild(link)
                        link.click()
                        link.remove()
                    }
                } catch(e) {
                    console.log(e)
                    this.$message.error('Не удалось сформировать выгрузку')
                } finally {
                    this.actionLoading = false
                }
            }
        }
    }
}