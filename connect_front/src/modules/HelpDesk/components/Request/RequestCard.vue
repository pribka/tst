<template>
    <div
        class="request_card"
        v-touch:longtap="longtapHandler"
        @click="open()">
        <div class="request_card__name blue_color mb-2 truncate">
            #{{ item.number }} {{ item.name }}
        </div>
        <div v-if="item.category" class="mb-2" style="font-size: 13px;line-height: 15px;">
            <span class="mr-1" style="color: #656565;">{{ $t('helpdesk.category') }}:</span> {{ item.category.name }}
        </div>
        <div v-if="item.channel" class="mb-2 flex items-center" style="font-size: 13px;line-height: 15px;">
            <span class="mr-1" style="color: #656565;">{{ $t('helpdesk.communication_channel') }}:</span>
            <template v-if="item.channel?.icon">
                <img
                    v-if="isSVG"
                    :src="require(`@/assets/svg/${item.channel.icon}`)"
                    class="mr-2 channel_icon" />
                <i
                    v-else
                    class="mr-2 fi"
                    :class="item.channel.icon" />
            </template>
            {{ item.channel.name }}
        </div>
        <div v-if="item.related_tasks && item.related_tasks.length">
            <span class="mr-1" style="color: #656565;">{{ $t('table.related_tasks') }}:</span>
            <div class="flex flex-wrap gap-x-2 gap-y-1">
                <div 
                    v-for="(task, index) in item.related_tasks" 
                    class="blue_color cursor-pointer"
                    :key="task.id"
                    @click.stop="openTask(task.id)">
                    #{{ task.counter }}<span v-if="index !== item.related_tasks.length - 1">, </span>
                </div>
            </div>
        </div>
        <div class="flex items-center justify-between gap-2">
            <div class="truncate flex items-center" style="color: #656565;font-size: 13px;line-height: 15px;">
                <i class="fi fi-rr-calendar mr-2" />
                {{ $moment(item.created_at).format('DD.MM.YYYY') }}
            </div>
            <div class="flex items-center gap-2">
                <ViewRating :rating="item.rating" />
                <Profiler
                    v-if="item.specialist"
                    :avatarSize="20"
                    :showUserName="false"
                    :user="item.specialist" />
                <a-tag :color="item.status.color">
                    {{ item.status.name || item.status.code }}
                </a-tag>
            </div>
        </div>
        <ActionsList ref="actionList" :item="item" :open="open" />
    </div>
</template>

<script>
import eventBus from '@/utils/eventBus'
export default {
    components: {
        ViewRating: () => import('@apps/HelpDesk/components/Request/RequestDrawer/components/ViewRating.vue'),
        ActionsList: () => import('./ActionsList.vue')
    },
    props: {
        item: {
            type: Object,
            required: true
        },
        actionsEnabled: {
            type: Boolean,
            default: true
        },
        routerKey: {
            type: String,
            default: 'requestView'
        },
    },
    computed: {
        isSVG() {
            return this.item.channel?.icon?.endsWith('.svg')
        }
    },
    methods: {
        openTask(id) {
            const query = JSON.parse(JSON.stringify(this.$route.query))
            query.task = id
            this.$router.push({query})
        },
        longtapHandler() {
            if(this.actionsEnabled) {
                this.$refs['actionList'].openActionsDrawer()
            }
        },
        open() {
            const query = {...this.$route.query}
            if(!query[this.routerKey]) {
                query[this.routerKey] = this.item.id
                this.$router.push({query})
            } else {
                eventBus.$emit('ticket_request_drawer_close')
                setTimeout(() => {
                    query[this.routerKey] = this.item.id
                    this.$router.push({query})
                }, 500)
            }
        }
    }
}
</script>

<style lang="scss" scoped>
.channel_icon{
    max-width: 16px;
}
.request_card{
    padding: 12px;
    zoom: 1;
    font-size: 14px;
    font-variant: tabular-nums;
    line-height: 1.5;
    list-style: none;
    font-feature-settings: 'tnum';
    background: #ffffff;
    border-radius: var(--borderRadius);
    margin-bottom: 10px;
    -webkit-user-select: none;
    -khtml-user-select: none;
    -moz-user-select: none;
    -ms-user-select: none;
    user-select: none;
    transition: all 0.5s cubic-bezier(0.645, 0.045, 0.355, 1);
    cursor: pointer;
    &.is_mobile{
        background: #fff;
    }
    &.touch{
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.15);
        transform: scale(0.97);
    }
}
</style>