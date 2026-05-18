<template>
    <div class="wdg_input">
        <ProjectSelect 
            v-if="isEdit"
            inputType="input"
            :placeholder="$t('ai_assistant.select_project')"
            :candidates="candidates"
            v-model="value"
            @change="onProjectChange" />
        <div v-else>
            <div v-if="value" class="flex items-center truncate">
                <div class="mr-2">
                    <a-avatar 
                        :size="20" 
                        icon="team" 
                        :key="value.id"
                        :src="workgroupLogoPath(value)" />
                </div>
                <span class="truncate">{{value.name}}</span>
            </div>
            <div v-else class="field_empty">
                {{ $t('ai_assistant.project_not_specified') }}
            </div>
        </div>
        <ReplaceVisorsModal
            v-if="hasVisorsField"
            ref="replaceVisorsModalRef"
            v-model="replaceVisorsForm" />
    </div>
</template>

<script>
import props from '../props.js'
import mixins from './mixins.js'
import { errorHandler } from '@/utils/index.js'
export default {
    props: {...props},
    mixins: [mixins],
    components: {
        ProjectSelect: () => import("@apps/DrawerSelect/ProjectSelect.vue"),
        ReplaceVisorsModal: () => import('../../../../../vue2TaskComponent/components/ReplaceVisorsModal.vue')
    },
    data() {
        return {
            value: null,
            candidates: [],
            replaceVisorsForm: {
                visors: []
            },
            skipReplaceVisorsWatch: false
        }
    },
    computed: {
        hasVisorsField() {
            return Boolean(
                this.intents?.intent_type?.metadata?.fields?.visors &&
                this.intents?.resolutions?.visors
            )
        }
    },
    watch: {
        'replaceVisorsForm.visors': {
            deep: true,
            handler(value) {
                this.handleReplaceVisorsChange(value)
            }
        }
    },
    created() {
        if(this.intents.resolutions?.[this.widgetKey]?.candidates?.length) {
            this.candidates = this.intents.resolutions[this.widgetKey].candidates.map(item => {
                return {
                    ...item,
                    name: item.repr,
                    workgroup_logo: item.image
                }
            })
        }
        if(this.intents.resolutions?.[this.widgetKey]?.value) {
            const item = this.intents.resolutions[this.widgetKey].value
            this.value = {
                ...item,
                name: item.repr,
                workgroup_logo: item.image
            }
        }
    },
    methods: {
        async onProjectChange(data) {
            this.changeWorkGroup(data)
            await this.updateProjectVisors(data)
        },
        async updateProjectVisors(project) {
            if(!this.hasVisorsField || !project?.id) return
            try {
                const { data } = await this.$http.get(`work_groups/workgroups/${project.id}/default_visors/`)
                const defaultVisors = this.normalizeVisors(data)
                if(!defaultVisors.length) return
                const currentVisors = this.intents?.resolutions?.visors?.value || []
                if(this.haveSameIds(defaultVisors, currentVisors)) return
                this.openReplaceVisorsModal(currentVisors, defaultVisors)
            } catch(error) {
                if(error?.status === 404) return
                errorHandler({error})
            }
        },
        openReplaceVisorsModal(currentVisors, defaultVisors) {
            this.skipReplaceVisorsWatch = true
            this.replaceVisorsForm = {
                visors: this.normalizeVisors(currentVisors)
            }
            this.$nextTick(() => {
                this.skipReplaceVisorsWatch = false
                if(this.$refs.replaceVisorsModalRef) {
                    this.$refs.replaceVisorsModalRef.open({ reason: 'project', defaultVisors })
                }
            })
        },
        async handleReplaceVisorsChange(value) {
            if(this.skipReplaceVisorsWatch || !this.hasVisorsField) return
            const nextVisors = this.normalizeVisors(value)
            const currentVisors = this.intents?.resolutions?.visors?.value || []
            if(this.haveSameIds(nextVisors, currentVisors)) return
            this.storeVisors(nextVisors)
            await this.patchVisors(nextVisors)
        },
        normalizeVisors(list) {
            if(!Array.isArray(list)) return []
            return list
                .filter(item => item?.id)
                .map(item => ({
                    ...item,
                    repr: item.repr || item.full_name || item.short_name || item.name || '',
                    image: item.image || item.avatar || null
                }))
        },
        haveSameIds(list1 = [], list2 = []) {
            const ids1 = list1.map(i => i.id).filter(Boolean).sort()
            const ids2 = list2.map(i => i.id).filter(Boolean).sort()
            if(ids1.length !== ids2.length) return false
            return ids1.every((id, index) => id === ids2[index])
        },
        storeVisors(value) {
            if(this.useInject) {
                this.injectUpdate({
                    widgetKey: 'visors',
                    index: this.index,
                    intentIndex: this.intentIndex,
                    messageIndex: this.messageIndex,
                    value
                })
            } else {
                this.$store.commit('ai/SET_MESSAGE_FIELD_VALUE', {
                    widgetKey: 'visors',
                    index: this.index,
                    intentIndex: this.intentIndex,
                    messageIndex: this.messageIndex,
                    value,
                    chatId: this.activeChat.id
                })
            }
        },
        async patchVisors(value) {
            const valid = await this.formValidate('visors')
            if(!valid) return
            await this.$http.patch(`/chat_ai/intents/${this.intents.id}/update-value/`, {
                field_name: 'visors',
                value: value.map(item => item.id)
            })
        }
    }
}
</script>

<style lang="scss" scoped>
.wdg_input{
    &::v-deep{
        .ant-input{
            height: initial;
            padding: 0px;
        }
    }
}
</style>
