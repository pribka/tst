<template>
    <WidgetWrapper :widget="widget" :class="isMobile && 'mobile_widget'">
        <div class="body_text">
            <p>{{ $t('dashboard.welcome.text1') }}</p>
            <p style="margin-bottom: 20px;">{{ $t('dashboard.welcome.text2') }}</p>

            <div class="text_block">
                <h2>{{ $t('dashboard.welcome.text3') }}</h2>
                <p>{{ $t('dashboard.welcome.text4') }}</p>
                <a-button type="flat_primary" @click="addTask()">
                    {{ $t('dashboard.welcome.text5') }}
                </a-button>
            </div>

            <div class="text_block">
                <h2>{{ $t('dashboard.welcome.text6') }}</h2>
                <p>{{ $t('dashboard.welcome.text7') }}</p>
                <a-button type="flat_primary" @click="addProject()">
                    {{ $t('dashboard.welcome.text8') }}
                </a-button>
            </div>

            <div v-if="!isMobile" class="text_block">
                <h2>{{ $t('dashboard.welcome.text9') }}</h2>
                <p>{{ $t('dashboard.welcome.text10') }}</p>
                <a-button type="flat_primary" @click="addSprint()">
                    {{ $t('dashboard.welcome.text11') }}
                </a-button>
            </div>

            <div v-if="!isMobile && user.current_contractor" class="text_block">
                <h2>{{ $t('dashboard.welcome.text12') }}</h2>
                <p>{{ $t('dashboard.welcome.text13') }}</p>
                <a-button type="flat_primary" @click="inviteUsers()">
                    {{ $t('dashboard.welcome.text14') }}
                </a-button>
            </div>

            <div class="text_block">
                <h2>{{ $t('dashboard.welcome.text15') }}</h2>
                <p>{{ $t('dashboard.welcome.text16') }}</p>

                <div class="mb-1">
                    <a-button type="flat_primary" @click="openChat()">
                        {{ $t('dashboard.welcome.text17') }}
                    </a-button>
                </div>

                <div class="mb-1">
                    <a-button type="flat_primary" @click="addGroup()">
                        {{ $t('dashboard.welcome.text18') }}
                    </a-button>
                </div>

                <div>
                    <a-button type="flat_primary" @click="addMeeting()">
                        {{ $t('dashboard.welcome.text19') }}
                    </a-button>
                </div>
            </div>

            <div class="text_block">
                <h2>{{ $t('dashboard.welcome.text20') }}</h2>
                <p>{{ $t('dashboard.welcome.text21') }}</p>
                <a-button type="flat_primary" @click="addEvent()">
                    {{ $t('dashboard.welcome.text22') }}
                </a-button>
            </div>

            <div v-if="!isMobile" class="text_block">
                <h2>{{ $t('dashboard.welcome.text23') }}</h2>
                <p>{{ $t('dashboard.welcome.text24') }}</p>
                <a-button type="flat_primary" @click="addOkr()">
                    {{ $t('dashboard.welcome.text25') }}
                </a-button>
            </div>
        </div>
    </WidgetWrapper>
</template>

<script>
import eventBus from '@/utils/eventBus'
import { mapState } from 'vuex'
export default {
    components: {
        WidgetWrapper: () => import('../WidgetWrapper.vue')
    },
    props: {
        widget: {
            type: Object,
            required: true
        }
    },
    computed: {
        ...mapState({
            user: state => state.user.user
        }),
        isMobile() { 
            return this.$store.state.isMobile
        }
    },
    methods: {
        inviteUsers() {
            const query = {...this.$route.query}
            query.organization_drawer = 'detail'
            query.organization_id = this.user.current_contractor.id
            this.$router.replace({query})
        },
        addOkr() {
            eventBus.$emit('add_objective')
        },
        openChat() {
            this.$router.push({ name: 'chat' })
        },
        addMeeting() {
            if(this.isMobile) {
                this.$store.commit('meeting/SET_EDIT_DRAWER', { show: true, model: 'main' })
            } else {
                this.$store.commit('meeting/SET_EDIT_MODAL', { show: true, model: 'main' })
            }
        },
        addEvent() {
            eventBus.$emit('open_event_form', null, null, null, null, 'default')
        },
        addGroup() {
            if(this.isMobile) {
                this.$router.replace({
                    query: { createGroup: true }
                })
            } else
                eventBus.$emit('add_workgroup_modal')
        },
        addSprint() {
            eventBus.$emit('add_sprint')
        },
        addProject() {
            if(this.isMobile) {
                this.$router.replace({
                    query: { create_project: true }
                })
            } else
                eventBus.$emit('add_proejct_modal')
        },
        addTask() {
            this.$store.commit('task/SET_PAGE_NAME', {
                pageName: 'page_list_task_task.TaskModel'
            })
            if(this.isMobile) {
                this.$store.dispatch('task/sidebarOpen', {
                    task_type: 'task'
                })
            } else {
                eventBus.$emit('add_task_modal', {
                    task_type: 'task'
                })
            }
        }
    }
}
</script>

<style lang="scss" scoped>
.body_text{
    overflow-y: auto;
    height: 100%;
    color: #888888;
    h2{
        font-weight: 400;
        font-size: 16px;
        line-height: 26px;
        margin-bottom: 10px;
        margin-top: 0px;
        color: var(--text);
    }
    p{
        font-size: 14px;
        line-height: 20px;
        &:not(:last-child){
            margin-bottom: 10px;
        }
    }
}
.text_block{
    &:not(:last-child){
        border-bottom: 1px solid var(--border2);
        padding-bottom: 15px;
        margin-bottom: 15px;
    }
}
</style>