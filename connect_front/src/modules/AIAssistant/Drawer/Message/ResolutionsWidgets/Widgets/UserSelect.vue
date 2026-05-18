<template>
    <div class="wdg_input">
        <UserDrawer
            v-if="isEdit"
            v-model="value"
            :id="defaultUserSelectId"
            class="w-full"
            :metadata="{ key: widgetKey, value: metadata }"
            inputType="ghost"
            :candidates="candidates"
            :changeMetadata="changeMetadata"
            :multiple="isMultiple"
            :inputPlaceholder="$t('ai_assistant.select_user')"
            :title="resolution.title || widgetKey"
            @change="changeUserField"
            @allClear="changeUserField"/>
        <div v-else>
            <div v-if="checkEmpty" class="field_empty">
                {{ $t('ai_assistant.not_specified') }}
            </div>
            <div v-else class="flex items-center flex-wrap gap-1">
                <template v-if="isMultiple">
                    <Profiler 
                        v-for="user in userData"
                        :avatarSize="22"
                        nameClass="text-sm"
                        :key="user.id"
                        hideSupportTag
                        :user="user" />
                </template>
                <Profiler 
                    v-else
                    :avatarSize="22"
                    nameClass="text-sm"
                    hideSupportTag
                    :user="userData" />
            </div>
        </div>
    </div>
</template>

<script>
import props from '../props.js'
import mixins from './mixins.js'
export default {
    props: {...props},
    mixins: [mixins],
    components: {
        UserDrawer: () => import("@apps/DrawerSelect/index.vue")
    },
    data() {
        return {
            value: this.isMultiple ? [] : null,
            defaultUserSelectId: 'ai_select',
            candidates: []
        }
    },
    computed: {
        resolutionValue() {
            return this.intents?.resolutions?.[this.widgetKey]?.value
        },
        checkEmpty() {
            if(this.isMultiple) {
                return this.value.length ? false : true
            } else {
                return this.value ? false : true
            }
        },
        userData() {
            if(this.isMultiple) {
                const users = this.intents?.resolutions?.[this.widgetKey]?.value || []
                return users
                    .map(user => this.mapUser(user))
                    .filter(user => user && typeof user === 'object')
            } else {
                const user = this.intents.resolutions[this.widgetKey].value
                return this.mapUser(user)
            }
        }
    },
    watch: {
        resolutionValue: {
            deep: true,
            handler() {
                this.syncValueFromResolution()
            }
        }
    },
    created() {
        if(this.intents.resolutions?.[this.widgetKey]?.metadata && Object.keys(this.intents.resolutions[this.widgetKey].metadata)?.length) {
            if(this.intents.resolutions[this.widgetKey].metadata?.[this.widgetKey] && Object.keys(this.intents.resolutions[this.widgetKey].metadata[this.widgetKey])?.length) {
                this.metadata = this.intents.resolutions[this.widgetKey].metadata
            } else {
                this.metadata[this.widgetKey] = this.isMultiple ? [] : null
            }
        } else {
            this.metadata[this.widgetKey] = this.isMultiple ? [] : null
        }
        if(this.intents.resolutions?.[this.widgetKey]?.candidates?.length) {
            this.candidates = this.intents.resolutions[this.widgetKey].candidates.map(user => {
                return {
                    ...user,
                    avatar: user.image,
                    full_name: user.repr
                }
            })
        }
        this.syncValueFromResolution()
    },
    methods: {
        mapUser(user) {
            if(!user || typeof user !== 'object')
                return null

            const fullName = user.repr
                || user.full_name
                || [user.last_name, user.first_name].filter(Boolean).join(' ')

            return {
                ...user,
                avatar: user.image || user.avatar,
                full_name: fullName
            }
        },
        changeUserField(data) {
            if(this.isMultiple) {
                const mappedUsers = data?.length ? data.map(user => this.mapUser(user)) : []
                const ids = mappedUsers.map(user => user.id)
                this.storeChangeValue({value: mappedUsers, useRepr: true})
                this.updateTimer(ids)
            } else {
                const mappedUser = data ? this.mapUser(data) : null
                const id = mappedUser ? mappedUser.id : null
                this.storeChangeValue({value: mappedUser, useRepr: true})
                this.updateTimer(id)
            }
        },
        syncValueFromResolution() {
            if(this.isMultiple) {
                if(this.intents.resolutions?.[this.widgetKey]?.value?.length) {
                    this.value = this.intents.resolutions[this.widgetKey].value
                        .map(user => this.mapUser(user))
                        .filter(user => user)
                } else {
                    this.value = []
                }
            } else {
                if(this.intents.resolutions?.[this.widgetKey]?.value) {
                    this.value = this.mapUser(this.intents.resolutions[this.widgetKey].value)
                } else {
                    this.value = null
                }
            }
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
            min-height: initial;
        }
    }
}
</style>
