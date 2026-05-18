import { mapState } from 'vuex'
import { errorHandler } from '@/utils/index.js'
let updateTimer;
export default {
    computed: {
        ...mapState({
            activeChat: state => state.ai.activeChat
        }),
        isMultiple() {
            return this.intents.intent_type.metadata.fields[this.widgetKey].type === 'ManyToManyField' ? true : false
        }
    },
    data() {
        return {
            metadata: {}
        }
    },
    methods: {
        ckeditorChange(value) {
            this.storeChangeValue({value})
            this.updateTimer(value)
        },
        changeMetadata({ value }) {
            this.$set(this.metadata, this.widgetKey, value)
            if(this.useInject) {

            } else {
                this.$store.commit('ai/SET_MESSAGE_METADATA', {
                    widgetKey: this.widgetKey,
                    index: this.index,
                    intentIndex: this.intentIndex,
                    messageIndex: this.messageIndex,
                    value: this.metadata,
                    chatId: this.activeChat.id
                })
            }
        },
        changeUserField(data) {
            if(this.isMultiple) {
                const value = data?.length ? data.map(user => user.id) : []
                this.storeChangeValue({value})
                this.updateTimer(value)
            } else {
                const value = data ? data.id : null
                this.storeChangeValue({value})
                this.updateTimer(value)
            }
        },
        workgroupLogoPath(workgroup) {
            return workgroup && workgroup.workgroup_logo && workgroup.workgroup_logo.path ? workgroup.workgroup_logo.path : ''
        },
        changeWorkGroup(data) {
            const value = data ? data.id : null
            this.storeChangeValue({value})
            this.updateTimer(value)
        },
        selectChange(uid) {
            if(this.isMultiple) {
                const value = []
                uid.forEach(item => {
                    const find = this.resolution.candidates.find(f => f.id === item)
                    if(find) {
                        value.push(find)
                    }
                })
                this.storeChangeValue({value, useRepr: true})
                this.updateTimer(uid)
            } else {
                const value = this.resolution.candidates.find(f => f.id === uid)
                if(value) {
                    this.storeChangeValue({value, useRepr: true})
                    this.updateTimer(value.id)
                }
            }
            const value = this.resolution.candidates.find(f => f.id === uid)
            if(value) {
                this.storeChangeValue({value, useRepr: true})
                if(this.isMultiple) {
                    this.updateTimer(value.map(item => item.id))
                } else {
                    this.updateTimer(value.id)
                }
            }
        },
        dateChange(date) {
            const value = date ? this.$moment(date).format() : null
            this.storeChangeValue({value})
            this.updateTimer(value)
        },
        fieldContainer(trigger) {
            return trigger.parentNode
        },
        inputChange(e) {
            const value = e.target.value
            this.storeChangeValue({value})
            this.updateTimer(value)
        },
        storeChangeValue({value, useRepr = false}) {
            if(this.useInject) {
                this.injectUpdate({
                    widgetKey: this.widgetKey,
                    index: this.index,
                    intentIndex: this.intentIndex,
                    messageIndex: this.messageIndex,
                    value,
                    useRepr,
                })
            } else {
                this.$store.commit('ai/SET_MESSAGE_FIELD_VALUE', {
                    widgetKey: this.widgetKey,
                    index: this.index,
                    intentIndex: this.intentIndex,
                    messageIndex: this.messageIndex,
                    value,
                    useRepr,
                    chatId: this.activeChat.id
                })
            }
        },
        updateTimer(value) {
            clearTimeout(updateTimer)
            updateTimer = setTimeout(() => {
                this.updateField(value)
            }, 800)
        },
        async updateField(value) {
            const valid = await this.formValidate(this.widgetKey)
            if (!valid) return
            try {
                const queryData = {
                    field_name: this.widgetKey,
                    value
                }
                if(Object.keys(this.metadata)?.length)
                    queryData.metadata = this.metadata
                await this.$http.patch(`/chat_ai/intents/${this.intents.id}/update-value/`, queryData)
            } catch (error) {
                errorHandler({error})
            }
        }

    }
}