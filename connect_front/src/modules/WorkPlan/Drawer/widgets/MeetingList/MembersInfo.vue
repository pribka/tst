<template>
    <div class="members_aside" :class="isMobile && 'mb-4'">
        <div v-if="detail.members && detail.members.length" class="members_aside__block">
            <div class="aside_label"><i class="fi fi-rr-users mr-2" />{{ $t('workplan.attendees') }}</div>
            <div v-for="member in detail.members" :key="member.user.id" class="member_item">
                <Profiler 
                    :avatarSize="24"
                    hideSupportTag
                    :user="member.user" />
            </div>
        </div>
        <div v-if="detail.absent_members && detail.absent_members.length" class="members_aside__block">
            <div class="aside_label text-red-400"><i class="fi fi-rr-delete-user mr-2"/> {{ $t('workplan.absentees') }}</div>
            <div v-for="member in detail.absent_members" :key="member.id" class="member_item">
                <Profiler 
                    :avatarSize="24"
                    hideSupportTag
                    :user="member" />
            </div>
        </div>
        <div class="members_aside__block">
            <div class="aside_label justify-between">
                <div class="flex items-center">
                    <i class="fi fi-rr-eye mr-2" /> {{ $t('workplan.observers') }}
                </div>
                <UserDrawer 
                    v-if="actions && actions.update_visors && actions.update_visors.availability" 
                    id="visorsSelect"
                    multiple
                    :dialog-style="{ top: '15px' }"
                    :title="$t('workplan.observers')"
                    v-model="visors"
                    @change="changeUserSelected">
                    <template #openButton>
                        <a-button 
                            v-tippy 
                            :content="$t('workplan.select_observers')" 
                            size="small" 
                            type="link" 
                            flaticon 
                            icon="fi-rr-plus" 
                            shape="circle" />
                    </template>
                </UserDrawer>
            </div>
            <a-spin class="w-full" size="small" :spinning="loading">
                <a-alert v-if="!detail.visors.length" :message="$t('workplan.observers_missing')" banner type="info" />
                <div v-for="member in detail.visors" :key="member.id" class="member_item">
                    <Profiler 
                        :avatarSize="24"
                        hideSupportTag
                        :user="member" />
                </div>
            </a-spin>
        </div>
    </div>
</template>

<script>
import { errorHandler } from '@/utils/index.js'
export default {
    components: {
        UserDrawer: () => import('@apps/DrawerSelect/index.vue')
    },
    props: {
        detail: {
            type: Object,
            required: true
        },
        actions: {
            type: Object,
            default: () => null
        },
        changeDetailField: {
            type: Function,
            default: () => {}
        }
    },
    data() {
        return {
            visors: [],
            loading: false
        }
    },
    computed: {
        isMobile() { 
            return this.$store.state.isMobile
        }
    },
    methods: {
        async changeUserSelected(value) {
            try {
                this.loading = true
                const { data } = await this.$http.put(`/meetings/sections/${this.detail.id}/update_visors/`, {
                    visors: value.map(user => user.id)
                })
                if(data?.visors?.length) {
                    this.changeDetailField({
                        field: 'visors',
                        value: data.visors
                    })
                    this.visors = data.visors
                }
            } catch(error) {
                errorHandler({error})
            } finally {
                this.loading = false
            }
        }
    },
    created() {
        if(this.detail.visors?.length)
            this.visors = this.detail.visors
    }
}
</script>

<style lang="scss" scoped>
.members_aside{
    &__block{
        .aside_label{
            margin-bottom: 7px;
            opacity: 0.8;
            font-weight: 500;
            display: flex;
            align-items: center;
        }
        &:not(:last-child){
            margin-bottom: 15px;
        }
        .member_item{
            &:not(:last-child){
                margin-bottom: 10px;
            }
        }
    }
}
</style>
