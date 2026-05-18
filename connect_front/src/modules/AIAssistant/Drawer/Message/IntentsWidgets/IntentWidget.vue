<template>
    <div class="intents_wrapper">
        <a-form-model
            ref="ruleForm"
            :model="form">
            <div class="intents_form">
                <div class="intents_form__item">
                    <div class="item_label">
                        {{ $t('ai_assistant.intent_type') }}
                    </div>
                    <div class="item_value">
                        {{ intents.intent_type.name }}
                    </div>
                </div>
                <ResolutionsWidgets 
                    v-for="(resolution, key, index) in intents.intent_type.metadata.fields" 
                    :resolution="resolution"
                    :widgetKey="key"
                    :index="index"
                    :injectUpdate="injectUpdate"
                    :formValidate="formValidate"
                    :injectChangeField="injectChangeField"
                    :intentIndex="intentIndex"
                    :messageIndex="messageIndex"
                    :intents="intents"
                    :useInject="useInject"
                    :isEdit="isEdit"
                    :message="message"
                    :key="key" />
            </div>
            <div class="flex items-center gap-2 mt-4" :class="isMobile && 'flex-col'">
                <template v-if="intents.related_object && metadata && metadata.get_parameter">
                    <a-button 
                        type="flat_primary" 
                        block
                        @click="openIntent()">
                        {{ intents.intent_type.btn_title_open }}
                    </a-button>
                </template>
                <template v-else>
                    <a-button 
                        type="flat_primary" 
                        size="large" 
                        flaticon
                        :loading="loading"
                        icon="fi-rr-plus-small"
                        block
                        @click="createHandler()">
                        {{ intents.intent_type.btn_title_create }}
                    </a-button>
                    <a-button 
                        type="flat_danger" 
                        size="large" 
                        :loading="deleteLoading"
                        block 
                        @click="deleteIntents">
                        {{ $t('ai_assistant.delete') }}
                    </a-button>
                </template>
            </div>
        </a-form-model>
    </div>
</template>

<script>
import props from './props.js'
import { mapState } from 'vuex'
import eventBus from '@/utils/eventBus'
import { errorHandler } from '@/utils/index.js'
export default {
    components: {
        ResolutionsWidgets: () => import('../ResolutionsWidgets/index.vue')
    },
    props: {...props},
    computed: {
        ...mapState({
            activeChat: state => state.ai.activeChat,
            chatLoading: state => state.ai.chatLoading,
            chatMessages: state => state.ai.chatMessages,
            isMobile: state => state.isMobile
        }),
        isEdit() {
            return this.intents?.related_object ? false : true
        },
        activeResolutions() {
            if (this.activeChat && this.chatMessages?.[this.activeChat.id]?.results?.[this.messageIndex]?.intents?.[this.intentIndex]?.resolutions) {
                return this.chatMessages[this.activeChat.id].results[this.messageIndex].intents[this.intentIndex].resolutions
            }
            return null
        },
        metadata() {
            return this.intents.intent_type.metadata
        },
        form() {
            return this.buildFormData()
        }
    },
    data() {
        return {
            loading: false,
            deleteLoading: false
        }
    },
    methods: {
        normalizeResolutionValue(value) {
            if (Array.isArray(value)) {
                return value?.length ? value.map(item => item.id ? item.id : item) : []
            }

            if (value && typeof value === 'object') {
                return value.id ? value.id : null
            }

            return value
        },
        buildFormData() {
            const formObject = {}
            const resolutions = this.activeResolutions || this.intents.resolutions || {}
            const fieldKeys = Object.keys(this.metadata?.fields || {})

            fieldKeys.forEach(key => {
                if (Object.prototype.hasOwnProperty.call(resolutions, key)) {
                    formObject[key] = this.normalizeResolutionValue(resolutions[key]?.value)
                }
            })

            Object.keys(resolutions).forEach(key => {
                if (!Object.prototype.hasOwnProperty.call(formObject, key)) {
                    formObject[key] = this.normalizeResolutionValue(resolutions[key]?.value)
                }
            })

            return formObject
        },
        isReportIntent() {
            return Boolean(
                this.intents?.intent_type?.code?.startsWith('report_') ||
                this.metadata?.backend_base_url === '/reports/report_settings/run_from_chat/'
            )
        },
        getDownloadFileName(headers = {}) {
            const disposition = headers['content-disposition'] || headers['Content-Disposition']
            if (!disposition) {
                return `report_${this.$moment().format('DD-MM-YYYY_HH-mm')}.xlsx`
            }

            const utfMatch = disposition.match(/filename\*=UTF-8''([^;]+)/i)
            if (utfMatch?.[1]) {
                return decodeURIComponent(utfMatch[1])
            }

            const asciiMatch = disposition.match(/filename="?([^"]+)"?/i)
            if (asciiMatch?.[1]) {
                return asciiMatch[1]
            }

            return `report_${this.$moment().format('DD-MM-YYYY_HH-mm')}.xlsx`
        },
        downloadBlobFile(data, headers = {}) {
            const fileName = this.getDownloadFileName(headers)
            const blob = data instanceof Blob ? data : new Blob([data])
            const url = window.URL.createObjectURL(blob)
            const link = document.createElement('a')
            link.href = url
            link.setAttribute('download', fileName)
            document.body.appendChild(link)
            link.click()
            link.remove()
            window.URL.revokeObjectURL(url)
        },
        async deleteIntents() {
            try {
                this.deleteLoading = true
                await this.$http.delete(`/chat_ai/intents/${this.intents.id}/`)
                this.$message.success(this.$t('ai_assistant.intent_deleted'))
                if(this.useInject) {
                    this.injectDelete({
                        messageIndex: this.messageIndex,
                        intentIndex: this.intentIndex,
                        intentId: this.intents.id
                    })
                } else {
                    this.$store.commit('ai/DELETE_INTENTS', {
                        messageIndex: this.messageIndex,
                        intentIndex: this.intentIndex
                    })
                }
            } catch(error) {
                errorHandler({error})
            } finally {
                this.deleteLoading = false
            }
        },
        openIntent() {
            const query = JSON.parse(JSON.stringify(this.$route.query))
            query[this.metadata.get_parameter] = this.intents.related_object
            this.$router.push({query})
        },
        formValidate(prop) {
            return new Promise(resolve => {
                const frm = this.$refs.ruleForm
                if (!frm) return resolve(false)
                if (prop) {
                    frm.validateField(prop, err => resolve(!err))
                } else {
                    frm.validate(valid => resolve(valid))
                }
            })
        },
        async saveRelatedObject(object) {
            try {
                const { data } = await this.$http.patch(`/chat_ai/intents/${this.intents.id}/`, {
                    related_object: object.id
                })
                if(data?.resolutions) {
                    if(this.useInject) {

                    } else {
                        this.$store.commit('ai/SET_MESSAGE_RESOLUTION', {
                            value: data.resolutions,
                            messageIndex: this.messageIndex,
                            intentIndex: this.intentIndex
                        })
                    }
                }
            } catch(error) {
                errorHandler({error})
            }
        },
        async createHandler() {
            const valid = await this.formValidate()
            if(valid) {
                try {
                    this.loading = true
                    let queryData = this.buildFormData()
                    if(this.metadata.fixed_values) {
                        queryData = {
                            ...queryData,
                            ...this.metadata.fixed_values
                        }
                    }
                    if (this.isReportIntent()) {
                        const response = await this.$http.post(
                            this.metadata.backend_base_url,
                            queryData,
                            { responseType: 'blob' }
                        )
                        if (response?.data) {
                            this.downloadBlobFile(response.data, response.headers)
                            this.$message.success(this.intents.intent_type.success_message || 'Отчет успешно создан')
                        }
                        return
                    }

                    const { data } = await this.$http.post(this.metadata.backend_base_url, queryData)
                    if(data) {
                        await this.saveRelatedObject(data)
                        if(this.useInject) {
                            this.injectChangeField({
                                value: data.id,
                                field: 'related_object',
                                intentId: this.intents.id
                            })
                        } else {
                            this.$store.commit('ai/SET_MESSAGE_RELATED', {
                                value: data.id,
                                messageIndex: this.messageIndex,
                                intentIndex: this.intentIndex
                            })
                        }
                        if(this.intents.intent_type?.code) {
                            const query = JSON.parse(JSON.stringify(this.$route.query))
                            if(this.intents.intent_type.code === 'create_task') {
                                if(this.useInject) {
                                    this.injectCreated({
                                        data,
                                        code: 'task'
                                    })
                                }
                                eventBus.$emit('page_list_task_task.TaskModel')
                                eventBus.$emit("UPDATE_LIST")
                                eventBus.$emit('update_filter_tasks.TaskModel_page_list_task_task.TaskModel')
                                this.$message.info(
                                    this.$createElement("span", {}, [
                                        `${this.$t('task.task_created')}.`,
                                        this.$createElement(
                                            "span",
                                            {
                                                class: "link cursor-pointer blue_color",
                                                on: {
                                                    click: () => {
                                                        if(!query.task) {
                                                            this.$message.destroy()
                                                            query.task = data.id;
                                                            this.$router.push({ query });
                                                        }
                                                    },
                                                },
                                            },
                                        ` ${this.$t('task.open_task')}`
                                        ),
                                    ]), 5)

                            }
                            if(this.intents.intent_type.code === 'create_meet') {
                                eventBus.$emit('update_filter_meetings.PlannedMeetingModel_page_list_meetings.PlannedMeetingModel')
                                if(this.useInject) {
                                    this.injectCreated({
                                        data,
                                        code: 'meeting'
                                    })
                                }
                                this.$message.info(
                                    this.$createElement("span", {}, [
                                        `${this.$t('meeting.conferenceCreated')}.`,
                                        this.$createElement(
                                            "span",
                                            {
                                                class: "link cursor-pointer blue_color",
                                                on: {
                                                    click: () => {
                                                        if(!query.meeting) {
                                                            this.$message.destroy()
                                                            query.meeting = data.id;
                                                            this.$router.push({ query });
                                                        }
                                                    },
                                                },
                                            },
                                        ` ${this.$t('ai_assistant.open_conference')}`
                                        ),
                                    ]), 5)
                            }
                            if(this.intents.intent_type.code === 'create_event') {
                                eventBus.$emit('events_reload')
                                eventBus.$emit('header_event_update')
                                if(this.useInject) {
                                    this.injectCreated({
                                        data,
                                        code: 'event'
                                    })
                                }
                                this.$message.info(
                                    this.$createElement("span", {}, [
                                        `${this.$t('calendar.event_created')}.`,
                                        this.$createElement(
                                            "span",
                                            {
                                                class: "link cursor-pointer blue_color",
                                                on: {
                                                    click: () => {
                                                        if(!query.event) {
                                                            this.$message.destroy()
                                                            query.event = data.id;
                                                            this.$router.push({ query });
                                                        }
                                                    },
                                                },
                                            },
                                        ` ${this.$t('ai_assistant.open_event')}`
                                        ),
                                    ]), 5)
                            }
                        }
                    }
                } catch(error) {
                    errorHandler({error})
                } finally {
                    this.loading = false
                }
            } else {
                return 
            }
        }
    }
}
</script>

<style lang="scss" scoped>
.intents_form{
    &__item{
        @media (min-width: 768px) {
            display: flex;
            align-items: flex-start;
        }
        &:not(:last-child){
            margin-bottom: 10px;
        }
        .item_label{
            @media (max-width: 767.98px) {
                margin-bottom: 5px;
            }
            @media (min-width: 768px) {
                min-width: 150px;
                padding-right: 20px;
                max-width: 150px;
            }
            color: #888888;
        }
        .item_value{
            word-break: break-word;
            min-width: 0;
            width: 100%;
            @media (min-width: 768px) {
                flex: 1 1 0%;
            }
        }
    }
}
</style>
