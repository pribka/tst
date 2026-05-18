<template>
    <div class="meeting_card rounded-lg" :class="[collapse && 'card_open', useInject && 'bg_invert']">
        <div class="meeting_card__wrapper cursor-pointer select-none">
            <div class="flex justify-between gap-2" @click="collapseCard()">
                <div :class="!isMobile && 'flex gap-4'" class="truncate">
                    <div v-if="!isMobile">
                        <div class="icon_wrap bg-purple-100 rounded-lg">
                            <div v-if="useIndex">#{{ indexValue }}</div>
                            <i v-else class="fi fi-rr-video-camera text-purple-600" />
                        </div>
                    </div>
                    <div class="truncate">
                        <div 
                            v-if="meeting.name" 
                            class="font-semibold mb-2 flex items-center truncate" 
                            :title="meeting.name" 
                            @click.stop="openMeeting()">
                            <div 
                                v-if="meeting.status === 'online'" 
                                class="online flex items-center mr-2">
                                <div class="blob" />
                            </div>
                            <span class="truncate card_name flex items-center">
                                <a-button 
                                    v-if="meeting && meeting.actions && meeting.actions.update && meeting.actions.update.availability"
                                    type="ui" 
                                    ghost
                                    class="mr-1"
                                    size="small" 
                                    v-tippy
                                    :content="$t('workplan.edit_name')"
                                    icon="fi-rr-edit" 
                                    flaticon 
                                    shape="circle"
                                    @click.stop="openChangeName()" />
                                <div class="truncate name_wrap">{{ meeting.name }}</div>
                            </span>
                        </div>
                        <div class="md:flex items-center flex-wrap gap-2">
                            <div v-if="meeting.date_start" class="flex items-center opacity-80" :title="$t('workplan.meeting_start_date')">
                                <i class="fi fi-rr-clock mr-1" /> {{ dateReadable }} <a-tag v-if="meeting.duration" class="time_tag ml-2">{{ durationReadable }}</a-tag>
                            </div>
                            <div v-if="meetingProject" class="flex items-center mt-2 md:mt-0">
                                <a-avatar
                                    :size="16"
                                    icon="team"
                                    :src="meetingProject.logo"
                                    class="flex-shrink-0" />
                                <span class="truncate project_link ml-1" @click.stop="openProject(meetingProject.id)">{{ meetingProject.string_view }}</span>
                            </div>
                            <div v-else class="flex items-center mt-2 md:mt-0" style="color: var(--red);">
                                {{ $t('workplan.no_project') }}
                            </div>
                        </div>
                        <div v-if="noEmpty" class="flex items-center mt-2">
                            <i class="fi fi-rr-users opacity-80 mr-2" /> 
                            <div class="flex items-center gap-1">
                                <component :is="relatedUsersComp" :relatedUsers="meeting.related_users" :storeKey="storeKey" />
                            </div>
                        </div>
                        <template v-else>
                            <div v-if="meeting.members && meeting.members.length" class="flex items-center mt-2">
                                <i class="fi fi-rr-users opacity-80 mr-2" /> 
                                <div class="flex items-center gap-1">
                                    <Profiler 
                                        v-for="member in meeting.members"
                                        :key="member.user.id"
                                        :avatarSize="22"
                                        :showUserName="false"
                                        hideSupportTag
                                        :user="member.user" />
                                </div>
                            </div>
                        </template>
                        <component 
                            v-if="meeting.meeting && meeting.meeting.related_object" 
                            :is="relatedObjectComp"
                            :related_object="meeting.meeting.related_object" />
                        <template v-if="meeting.intents && meeting.intents.total">
                            <div 
                                v-if="showAIIntents" 
                                class="mt-2 flex items-center" 
                                v-tippy
                                :content="$t('workplan.show_all_intents')"
                                style="color: rgb(121, 76, 216);" 
                                @click.stop="openAiIntents()">
                                <div class="mr-2">
                                    <i class="fi fi-ai-rr-sparkles" />
                                </div>
                                <div style="word-break: break-word;white-space: normal;">{{ intentsTotal }}</div>
                            </div>
                            <div 
                                v-else
                                class="mt-2 flex items-center" 
                                style="color: rgb(121, 76, 216);" >
                                <div class="mr-2">
                                    <i class="fi fi-ai-rr-sparkles" />
                                </div>
                                <div style="word-break: break-word;white-space: normal;">{{ intentsTotal }}</div>
                            </div>
                        </template>
                    </div>
                </div>
                <div>
                    <a-spin v-if="actionsLoading" size="small" />
                    <i v-else class="fi fi-rr-angle-small-down card_arrow block" style="opacity: 0.5;font-size: 16px;" />
                </div>
            </div>
        </div>
        <div v-if="collapse" class="collapse_wrapper">
            <div class="collapse_wrapper__divider" :class="detail && detail.transcribe && 'sm_mb'" />
            <component
                :is="collapseBodyComp"
                :item="meeting"
                :useLocalStore="useLocalStore"
                :intentDelete="intentDelete"
                :handlerChangeField="handlerChangeField"
                :storeKey="storeKey"
                :intentsChangeField="intentsChangeField"
                :createdHandler="createdHandler"
                :detail="detail"
                :changeDetailField="changeDetailField"
                :onProjectReassigned="setMeetingProject" />
        </div>

        <a-modal
            :title="$t('workplan.edit_name')"
            :visible="nameVisible"
            @afterVisibleChange="afterVisibleChange"
            @cancel="hideNameVisible()">
            <a-form-model
                ref="ruleForm"
                :model="form">
                <a-form-model-item 
                    :rules="{
                        required: true,
                        message: $t('field_required'),
                        trigger: ['change', 'blur']
                    }"
                    class="mb-2"
                    ref="name" 
                    prop="name">
                    <a-input v-model="form.name" ref="editName" size="large" :placeholder="$t('workplan.print_edit_name')" />
                </a-form-model-item>
            </a-form-model>
            <template #footer>
                <a-button type="primary" :loading="nameLoading" size="large" block @click="onSubmit">
                    {{ $t('save') }}
                </a-button>
            </template>
        </a-modal>
    </div>
</template>

<script>
const listType = 'meetingList'
import { declOfNum } from '@/utils/utils.js'
import eventBus from "@/utils/eventBus"
import { errorHandler } from '@/utils/index.js'
export default {
    props: {
        meeting: {
            type: Object,
            required: true
        },
        storeKey: {
            type: String,
            required: true
        },
        useInject: {
            type: Boolean,
            default: false
        },
        useLocalStore: {
            type: Boolean,
            default: false
        },
        getInjectActions: {
            type: Function,
            default: () => {}
        },
        useOpen: {
            type: Boolean,
            default: true
        },
        useIndex: {
            type: Boolean,
            default: false
        },
        indexValue: {
            type: Number,
            default: 1
        },
        showAIIntents: {
            type: Boolean,
            default: false
        },
        changeListItem: {
            type: Function,
            default: () => {}
        }
    },
    computed: {
        meetingProject() {
            if(this.meeting.execution_time_project) {
                /*if(this.meeting.meeting?.project?.workgroup_logo) {
                    return {
                        ...this.meeting.meeting?.project,
                        string_view: this.meeting.meeting?.project.name,
                        logo: this.meeting.meeting?.project?.workgroup_logo?.path || null
                    }
                } */
                return this.meeting.execution_time_project
            }
            return null
        },
        collapseBodyComp() {
            if(this.collapse)
                return () => import('./CollapseBody.vue')
            return null
        },
        collapse: {
            get() {
                if(this.useLocalStore)
                    return this.localCollapse
                return this.meeting.collapse || false
            },
            set(value) {
                if(this.useLocalStore)
                    this.localCollapse = value
                else {
                    this.$store.commit('workplan/CHANGE_COLLAPSE', {
                        storeKey: this.storeKey,
                        value,
                        item: this.meeting,
                        list: listType
                    })
                }
            }
        },
        relatedObjectComp() {
            if(this.meeting.related_object)
                return () => import('../RelatedObject.vue')
            return false
        },
        relatedUsersComp() {
            if(this.meeting.related_users?.length)
                return () => import('../RelatedUsers.vue')
            return null
        },
        user: {
            get() {
                return this.$store.state.workplan.user?.[this.storeKey] || null
            },
            set(value) {
                this.$store.commit('workplan/CHANGE_FIELD', {
                    value,
                    field: 'user',
                    storeKey: this.storeKey
                })
            }
        },
        noEmpty() {
            return this.meeting.related_users?.length && this.user.length || false
        },
        isMobile() { 
            return this.$store.state.isMobile
        },
        durationReadable() {
            if(!this.meeting.duration) return null

            const [h, m, sRaw] = this.meeting.duration.split(':')
            const s = Math.floor(parseFloat(sRaw))

            const hh = parseInt(h)
            const mm = parseInt(m)
            const ss = s

            let out = ''

            if(hh > 0) out += `${hh} ${this.$t('workplan.hour_short')} `
            if(mm > 0) out += `${mm} ${this.$t('workplan.minute_short')} `
            if(ss > 0) out += `${ss} ${this.$t('workplan.second_short')}`

            return out.trim()
        },
        dateReadable() {
            const d = this.$moment(this.meeting.date_start)
            const today = this.$moment().startOf('day')

            if(d.isSame(today, 'day'))
                return this.$t('workplan.meeting_today_at', { time: d.format('HH:mm') })

            return d.format('DD.MM.YYYY HH:mm')
        },
        intentsTotal() {
            const parts = []
            const totalNum = Number(this.meeting.intents?.accepted || 0) + Number(this.meeting.intents?.deleted || 0)

            if(totalNum === this.meeting.intents?.total) {
                parts.push(this.$t('workplan.intents_processed', { count: `${this.meeting.intents.total} ${declOfNum(this.meeting.intents.total, [this.$t('workplan.intent_one'), this.$t('workplan.intent_few'), this.$t('workplan.intent_many')])}` }))
                if (this.meeting.intents.deleted) {
                    parts.push(
                        this.$t('workplan.intents_deleted', { count: this.meeting.intents.deleted })
                    )
                }
            } else {
                parts.push(this.$t('workplan.intents_found', { count: `${this.meeting.intents.total} ${declOfNum(this.meeting.intents.total, [this.$t('workplan.intent_one'), this.$t('workplan.intent_few'), this.$t('workplan.intent_many')])}` }))
                if (this.meeting.intents.unprocessed) {
                    parts.push(
                        this.$t('workplan.intents_unprocessed', { count: this.meeting.intents.unprocessed })
                    )
                }
                if (this.meeting.intents.deleted) {
                    parts.push(
                        this.$t('workplan.intents_deleted', { count: this.meeting.intents.deleted })
                    )
                }
            }
            
            return parts.join(', ')
        }
    },
    data() {
        return {
            actionsLoading: false,
            detail: null,
            localCollapse: false,
            nameVisible: false,
            nameLoading: false,
            form: {
                name: ""
            }
        }
    },
    methods: {
        afterVisibleChange(vis) {
            if(vis) {
                if(this.meeting.name)
                    this.form.name = this.meeting.name
                this.$nextTick(() => {
                    if(this.$refs.editName)
                        this.$refs.editName.focus()
                })
            }
        },
        onSubmit() {
            this.$refs.ruleForm.validate(async valid => {
                if (valid) {
                    try {
                        this.nameLoading = true
                        const { data } = await this.$http.put(`/meetings/sections/${this.meeting.id}/update_name/`, {
                            name: this.form.name
                        })
                        if(data) {
                            if(this.useLocalStore) {
                                this.changeListItem({
                                    field: 'name', 
                                    value: data.name, 
                                    item: this.meeting.id
                                })
                            }
                            this.$store.commit('workplan/CHANGE_MEETING_NAME', {
                                value: data.name,
                                storeKey: this.storeKey, 
                                list: listType,
                                item: this.meeting.id
                            })
                            this.nameVisible = false
                        }
                    } catch(error) {
                        errorHandler({error})
                    } finally {
                        this.nameLoading = false
                    }
                }
            })
        },
        hideNameVisible() {
            this.form.name = ""
            this.nameVisible = false
        },
        openChangeName() {
            this.nameVisible = true
        },
        intentsChangeField({ intentId, value, field }) {
            const index = this.detail.intents.findIndex(f => f.id === intentId)
            if(index !== -1) {
                if(this.detail.intents?.[index])
                    this.$set(this.detail.intents[index], field, value)
            }
        },
        intentsStatReload() {
            this.$store.dispatch('workplan/getAIIntents', { storeKey: this.storeKey }) 
        },
        changeDetailField({field, value}) {
            this.$set(this.detail, field, value)
        },
        openAiIntents() {
            eventBus.$emit('open_ai_intents', this.meeting.id)
        },
        handlerChangeField({ widgetKey, index, intentIndex, messageIndex, value, useRepr }) {
            if(this.detail.intents?.[intentIndex]?.resolutions?.[widgetKey])
                this.$set(this.detail.intents[intentIndex].resolutions[widgetKey], 'value', value)
        },
        createdHandler() {
            this.intentsStatReload()
            this.meetingReload()
        },
        intentDelete({ intentId }) {
            const index = this.detail.intents.findIndex(f => f.id === intentId)
            if(index !== -1)
                this.$set(this.detail.intents[index], 'is_active', false)

            this.intentsStatReload()
            this.meetingReload()
        },
        meetingReload() {
            if(this.meeting.meeting) {
                this.$store.dispatch('workplan/updateItem', {
                    item: this.meeting.meeting,
                    list: 'meetingList'
                })
            }
        },
        async getSessionDetail() {
            try {
                const { data } = await this.$http.get(`/meetings/sections/${this.meeting.id}/`)
                if(data) {
                    this.detail = data
                    if(data.intents?.length <= 3) {
                        this.$store.commit('workplan/CHANGE_INTENTS_COLLAPSE', {
                            storeKey: this.storeKey,
                            value: true,
                            item: this.meeting,
                            list: listType
                        })
                    }
                }
            } catch(error) {
                errorHandler({error, show: false})
            }
        },
        async getActions() {
            try {
                if(this.useLocalStore) {
                    await this.getInjectActions(this.meeting)
                } else {
                    await this.$store.dispatch('workplan/getMeetingsActions', {
                        storeKey: this.storeKey,
                        item: this.meeting,
                        list: listType
                    })
                }
            } catch(error) {
                errorHandler({error, show: false})
            } 
        },
        async collapseCard() {
            try {
                this.actionsLoading = true
                if(!this.collapse)
                    await this.getActions()
                if(!this.collapse)
                    await this.getSessionDetail()
            } finally {
                this.actionsLoading = false
            }
            this.collapse = !this.collapse
        },
        openProject(id) {
            const query = Object.assign({}, this.$route.query)
            query.viewProject = id
            this.$router.push({ query })
        },
        setMeetingProject(project) {
            const normalized = {
                ...project,
                string_view: project.name,
                logo: project.workgroup_logo?.path || null
            }
            this.$set(this.meeting, 'execution_time_project', normalized)
            this.changeListItem({ item: this.meeting.id, field: 'execution_time_project', value: normalized })
        },
        openMeeting() {
            if(this.useOpen) {
                const query = JSON.parse(JSON.stringify(this.$route.query))
                query.meeting = this.meeting.meeting.id
                this.$router.replace({query})
            } else
                this.collapseCard()
        }
    }
}
</script>

<style lang="scss" scoped>
.card_name{
    .name_wrap{
        transition: all 0.3s cubic-bezier(0.645, 0.045, 0.355, 1);
        &:hover{
            color: var(--blue);
        }
    }
}
.collapse_wrapper{
    padding-left: 15px;
    padding-right: 15px;
    padding-bottom: 15px;
    @media (min-width: 768px) {
        padding-left: 20px;
        padding-right: 20px;
        padding-bottom: 20px;
    }
    &__divider{
        margin-bottom: 15px;
        height: 1px;
        background: #e8e8e8;
        @media (min-width: 768px) {
            margin-bottom: 20px;
        }
        &.sm_mb{
            @media (min-width: 768px) {
                margin-bottom: 10px;
            }
        }
    }
}
.online{
    color: rgba(255, 82, 82, 1);
    .blob{
        border-radius: 50%;
        height: 8px;
        width: 8px;
        transform: scale(1);
        background: rgba(255, 82, 82, 1);
        box-shadow: 0 0 0 0 rgba(255, 82, 82, 1);
    }
}
.project_link{
    cursor: pointer;
    transition: color 0.3s cubic-bezier(0.645, 0.045, 0.355, 1);
    &:hover{
        color: var(--blue);
    }
}
.time_tag{
    line-height: 20px;
    font-size: 13px;
    padding-left: 8px;
    padding-right: 8px;
}
.meeting_card{
    background: #fff;
    overflow: hidden;
    &.bg_invert{
        background: #f7f9fc;
    }
    &__wrapper{
        padding: 15px;
        @media (min-width: 768px) {
            padding: 20px;
        }
    }
    .card_arrow{
        transition: all 0.3s cubic-bezier(0.645, 0.045, 0.355, 1);
    }
    &.card_open{
        .card_arrow{
            transform: rotate(180deg);
        }
    }
    &:not(:last-child){
        margin-bottom: 10px;
        @media (min-width: 768px) {
            margin-bottom: 15px;
        }
    }
    .icon_wrap{
        width: 36px;
        height: 36px;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 18px;
    }
}
</style>
