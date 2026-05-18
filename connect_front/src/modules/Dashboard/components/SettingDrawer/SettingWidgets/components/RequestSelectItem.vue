<template>
    <div class="request_card">
        <div class="request_card__name blue_color mb-2 truncate">
            #{{ item.number }} {{ item.name }}
        </div>
        <div
            v-if="item.category"
            class="mb-2 text_row">
            <span class="label_text mr-1">{{ $t('helpdesk.category') }}:</span> {{ item.category.name }}
        </div>
        <div
            v-if="item.channel"
            class="mb-2 flex items-center text_row">
            <span class="label_text mr-1">{{ $t('helpdesk.communication_channel') }}:</span>
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
        <div class="flex items-center justify-between gap-2">
            <div class="truncate flex items-center text_row label_text">
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
        <a-button
            type="primary"
            ghost
            size="small"
            class="mt-2"
            @click="selectFunction(item)">
            {{ $t('dashboard.select') }}
        </a-button>
    </div>
</template>

<script>
export default {
    components: {
        ViewRating: () => import('@apps/HelpDesk/components/Request/RequestDrawer/components/ViewRating.vue')
    },
    props: {
        item: {
            type: Object,
            required: true
        },
        selectFunction: {
            type: Function,
            required: true
        }
    },
    computed: {
        isSVG() {
            return this.item.channel?.icon?.endsWith('.svg')
        }
    }
}
</script>

<style lang="scss" scoped>
.channel_icon{
    max-width: 16px;
}
.text_row{
    font-size: 13px;
    line-height: 15px;
}
.label_text{
    color: #656565;
}
.request_card{
    padding: 12px;
    font-size: 14px;
    font-variant: tabular-nums;
    line-height: 1.5;
    list-style: none;
    font-feature-settings: 'tnum';
    background: #fff;
    border-radius: var(--borderRadius);
    margin-bottom: 10px;
    border: 1px solid var(--borderColor);
}
</style>
