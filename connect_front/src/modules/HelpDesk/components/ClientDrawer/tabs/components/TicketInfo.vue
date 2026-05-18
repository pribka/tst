<template>
    <DrawerAside class="h-full ticket_info relative">
        <ListView v-if="ticket" inline labelDark>
            <ListViewItem>
                <span class="font-semibold">{{ ticket.name }}</span>
            </ListViewItem>
            <ListViewItem>
                <span>{{ ticket.description }}</span>
            </ListViewItem>
            <ListViewItem v-if="ticket.start_date && !ticket.end_date" :title="$t('helpdesk.start_date')">
                {{ $moment(ticket.start_date).format('DD.MM.YYYY') }}
            </ListViewItem>
            <ListViewItem v-if="ticket.end_date && ticket.end_date" :title="$t('helpdesk.deadlines')">
                {{ $moment(ticket.start_date).format('DD.MM.YYYY') }} - {{ $moment(ticket.end_date).format('DD.MM.YYYY') }}
            </ListViewItem>
            <ListViewItem v-if="ticket.status" :title="$t('helpdesk.status')">
                <a-tag :color="ticket.status.color" block size="large">
                    {{ ticket.status.name }}
                </a-tag>
            </ListViewItem>
            <ListViewItem v-if="checkField({ key: 'category' })" :title="$t('helpdesk.category')">
                {{ ticket.category.name }}   
            </ListViewItem>
            <ListViewItem :title="$t('helpdesk.priority')">
                <ProirityCard :priority="curPriority" />
            </ListViewItem>
            <ListViewItem v-if="checkField({ key: 'dead_line' })" :title="$t('helpdesk.deadline')">
                {{ $moment(ticket.dead_line).format('DD.MM.YYYY') }}
            </ListViewItem>
            <ListViewItem :title="$t('helpdesk.responsible')">
                <Profiler 
                    :avatarSize="22"
                    nameClass="text-sm"
                    :user="ticket.specialist" />
            </ListViewItem>
            <ListViewItem v-if="checkField({ key: 'visors', type: 'array' })" :title="$t('helpdesk.observers')">
                <Profiler 
                    v-for="visor in ticket.visors"
                    :key="visor.id"
                    :avatarSize="22"
                    nameClass="text-sm"
                    :user="visor" />
            </ListViewItem>
            <ListViewItem v-if="ticket.channel" :title="$t('helpdesk.communication_channel')">
                <div class="flex items-center justify-between pr-1">
                    <span class="pr-2">{{ ticket.channel.name }}</span>
                    <div v-if="ticket.channel.icon">
                        <img :data-src="ticket.channel.icon" class="lazyload mr-2 channel_icon" />    
                    </div>
                </div>
            </ListViewItem>
        </ListView>
        <div v-else class="empty_ticket">
            <div>
                <i class="fi fi-rr-info"></i>
                <div class="empty_ticket__message">{{ $t('helpdesk.select_appeal_to_view') }}</div>
            </div>
        </div>
    </DrawerAside>
</template>

<script>
import priorityMixin from '../../../../priorityMixin.js'
export default {
    mixins: [priorityMixin],
    components: {
        DrawerAside: () => import('@apps/UIModules/DrawerAside'),
        ProirityCard: () => import('../../../ProirityCard.vue')
    },
    props: {
        ticket: {
            type: Object,
            default: () => null
        }
    },
    computed: {
        curPriority() {
            if(this.ticket.priority) {
                const find = this.priorityList.find(f => Number(f.value) === Number(this.ticket.priority.code))
                if(find) {
                    return find
                }
            }
            return null
        }
    },
    methods: {
        checkField({key, type = 'object'}) {
            if(this.edit)
                return true
            else {
                if(type === 'array') {
                    if(this.ticket[key]?.length)
                        return true
                } else {
                    if(this.ticket[key])
                        return true
                }
            }
            return false
        },
    }
}
</script>

<style lang="scss" scoped>
.empty_ticket{
    height: 100%;
    width: 100%;
    display: flex;
    align-items: center;
    justify-content: center;
    position: absolute;
    top: 0;
    left: 0;
    text-align: center;
    color: #888888;
    &__message{
        margin-top: 10px;
        max-width: 250px;
    }
    i{
        font-size: 56px;
    }
}
.ticket_info{
    overflow-y: auto;
}
.execution_result{
    min-width: 400px;
}
.channel_icon{
    max-width: 16px;
}
.priority_icon{
    position: relative;
    overflow: hidden;
    width: 28px;
    height: 28px;
    border-radius: 8px;
    display: flex;
    align-items: center;
    justify-content: center;
    &__bg{
        position: absolute;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        opacity: 0.1;
    }
    i{
        position: relative;
        z-index: 5;
    }
}
</style>