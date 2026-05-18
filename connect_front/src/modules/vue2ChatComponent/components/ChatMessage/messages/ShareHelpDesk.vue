<template>
    <div class="help_desk cursor-pointer" @click="openHelpDesk()">
        <div class="help_desk__item font-semibold" style="color:#4777FF;">
            {{$t('chat.help_desk2')}} #{{messageItem.share.number}}
        </div>
        <div v-if="messageItem.share.author" class="lg:flex items-center help_desk__item">
            <span class="label lg:mr-1 block lg:inline-block">{{$t('chat.owner')}}:</span>
            <Profiler
                :avatarSize="22"
                nameClass="text-sm"
                :showChatButton="false"
                :user="messageItem.share.author" />
        </div>
        <div v-if="messageItem.share.specialist" class="lg:flex items-center help_desk__item">
            <span class="label lg:mr-1 block lg:inline-block">{{$t('chat.operator')}}:</span>
            <Profiler
                :avatarSize="22"
                nameClass="text-sm"
                :showChatButton="false"
                :user="messageItem.share.specialist" />
        </div>
        <div v-if="messageItem.share.created_at" class="lg:flex items-center help_desk__item">
            <span class="label lg:mr-1 block lg:inline-block">{{$t('chat.created_2')}}:</span>
            {{$moment(messageItem.share.created_at).format('DD.MM.YYYY HH:mm')}}
        </div>
        <div class="lg:flex items-center help_desk__item">
            <span class="label lg:mr-1 block lg:inline-block">{{$t('chat.dead_line')}}:</span>
            <div v-if="messageItem.share.dead_line">
                {{$moment(messageItem.share.dead_line).format('DD.MM.YYYY HH:mm')}}
            </div>
            <div v-else>
                {{$t('Not specified')}}
            </div>
        </div>
        <div class="lg:flex items-center help_desk__item">
            <span class="label lg:mr-1 block lg:inline-block">{{$t('chat.category')}}:</span>
            <div v-if="messageItem.share.category">
                {{messageItem.share.category.name}}
            </div>
            <div v-else>
                {{$t('Not specified')}}
            </div>
        </div>
        <div class="lg:flex items-center help_desk__item">
            <span class="label lg:mr-1 block lg:inline-block">{{$t('chat.priority')}}:</span>
            <div v-if="messageItem.share.priority">
                {{messageItem.share.priority.name}}
            </div>
            <div v-else>
                {{$t('Not specified')}}
            </div>
        </div>
        <template v-if="messageItem.share.status">
            <div v-if="messageItem.share.status.code === 'new' && changeStatusInChat.statusCode !== 'in_work'">
                <a-button v-if="specialist" type="primary" @click="helpDeskChangeStatus('in_work')">
                    {{ $t('chat.take_into_work') }}
                </a-button>
            </div>
            <div class="flex gap-2" v-if="!specialist">
                <a-button v-if="messageItem.share.status.code !== 'completed' && changeStatusInChat.statusCode !== 'completed'" type="primary" @click="helpDeskChangeStatus('completed')">
                    <i class="fi fi-rr-check mr-2" />
                    Принять результат
                </a-button>
                <a-button v-if="messageItem.share.status.code !== 'on_rework' && messageItem.share.status.code !== 'completed' && changeStatusInChat.statusCode !== 'completed' && changeStatusInChat.statusCode !== 'on_rework'" type="danger" @click="helpDeskChangeStatus('on_rework')">
                    <i class="fi fi-rr-refresh mr-2"></i>
                    Нужна доработка
                </a-button>
            </div>
            <div v-if="messageItem.share.rating || send_rating" class="lg:flex items-center help_desk__item">
                <span class="label lg:mr-1 block lg:inline-block">Оценка:</span>
                <ViewRating v-if="send_rating" :rating="rewForm.rating" labelView />
                <ViewRating v-else :rating="messageItem.share.rating" labelView />
            </div>
            <div v-else>
                <div v-if="(messageItem.share.status.code === 'completed' && !specialist) || (changeStatusInChat.statusCode === 'completed' && !specialist)" class="pb-2">
                    <div class="rew_wrapper_info pt-0">
                        <h2>Оцените качество обслуживания</h2>
                        <SmileSelect v-model="rewForm.rating" class="mb-5" />
                        <a-textarea
                            v-model="rewForm.description"
                            size="large"
                            placeholder="Комментарий к оценке"
                            :auto-size="{ minRows: 3, maxRows: 12 }" />
                    </div>
                    <a-button
                        v-if="!send_rating"
                        type="primary"
                        size="large"
                        class="mt-2"
                        @click="completedTicket(false)">
                        Отправить
                    </a-button>
                </div>
            </div>
        </template>
    </div>
</template>

<script>
import {mapState} from "vuex"
import { errorHandler } from '@/utils/index.js'
export default {
    components: {
        ViewRating: () => import("@/modules/HelpDesk/components/Request/RequestDrawer/components/ViewRating.vue"),
        SmileSelect: () => import("@/modules/HelpDesk/components/Request/RequestDrawer/components/SmileSelect.vue")
    },
    props: {
        messageItem: {
            type: Object,
            required: true
        }
    },
    data(){
        return {
            priorityList: [
                {
                    name: this.$t('chat.priority_very_low'),
                    value: 1,
                    color: '#434647',
                    i18n: 'low'
                },
                {
                    name: this.$t('chat.priority_low'),
                    value: 2,
                    color: '#52c41a',
                    i18n: 'low'
                },
                {
                    name: this.$t('chat.priority_medium'),
                    value: 3,
                    color: '#f7e706',
                    i18n: 'middle'
                },
                {
                    name: this.$t('chat.priority_high'),
                    value: 4,
                    color: '#faad14',
                    i18n: 'tall'
                },
                {
                    name: this.$t('chat.priority_very_high'),
                    value: 5,
                    color: '#ff0000',
                    i18n: 'tall'
                }
            ],
            statusCopy:null,
            changeStatusInChat:{
                index: false,
                statusCode:null
            },
            rewForm: {
                description: "",
                rating: null
            },
            send_rating:false
        }
    },
    computed:{
        ...mapState({
            user: state => state.user.user,
        }),
        specialist() {
            return this.user?.id === this.messageItem.share.specialist?.id || false
        }
    },
    methods: {
        async helpDeskChangeStatus(status){
            try {
                const queryData = {status}
                await this.$http.put(`/help_desk/tickets/${this.messageItem.share.id}/status/`, queryData)
                this.changeStatusInChat.index = true
                this.changeStatusInChat.statusCode = status
            } catch(error) {
                errorHandler({error})
            }
        },
        async openHelpDesk(){
            const query = JSON.parse(JSON.stringify(this.$route.query))
            if (this.specialist){
                this.$router.replace({ query: { ...query, ticketView: this.messageItem.share.id }})
            }else{
                let urlActions =`/help_desk/tickets/${this.messageItem.share.id}/action_info/`
                let data_actions = await this.$http.get(urlActions)
                if (data_actions.data.actions?.edit?.availability){
                    this.$router.replace({ query: { ...query, ticketView: this.messageItem.share.id }})
                }else{
                    this.$router.replace({ query: { ...query, requestView: this.messageItem.share.id }})
                }
            }

        },
        async completedTicket(status = true) {
            try {
                this.completedLoading = true
                if(this.rewForm.rating) {
                    await this.$http.post('/vote/rating/', {
                        ...this.rewForm,
                        related_object: this.messageItem.share.id
                    })
                    this.send_rating = true
                }
            } catch(error) {
                errorHandler({error})
            } finally {
                this.completedLoading = false
            }
        },

    },

}
</script>

<style lang="scss" scoped>
.help_desk{
    background: rgba(115, 115, 115, 0.1);
    border-left: 5px solid #ff9900;
    border-radius: 5px 5px;
    padding: 5px;
    .help_desk__item{
        &:not(:last-child){
            margin-bottom: 5px;
        }
    }
    .label{
        color: #888888 !important;
        font-weight: 400;
    }
    .rew_wrapper_info{
        padding-top: 10px;
        h2{
            text-align: center;
            margin-bottom: 15px;
            font-size: 18px;
            font-weight: 600;
        }
    }
}

</style>