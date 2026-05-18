<template>
    <div style="min-height: 90vh;">
        <MobileInfiniteList
            ref="callsMobileList"
            :url="listUrl"
            :reloadKey="ticket.id"
            :identifier="page_name"
            :emptyDescription="$t('helpdesk.no_data')">
            <template #item="{ item }">
                <CallCard :key="item.id" :item="item" />
            </template>
        </MobileInfiniteList>
    </div>
</template>

<script>
export default {
    components: {
        MobileInfiniteList: () => import('@/modules/HelpDesk/components/MobileInfiniteList.vue'),
        CallCard: () => import('./CallCard.vue')
    },
    props: {
        ticket: {
            type: Object,
            required: true
        },
        page_name: {
            type: String,
            required: true
        }
    },
    computed: {
        listUrl() {
            return `/meetings/calls/?ticket=${this.ticket.id}`
        }
    },
    methods: {
        updateData() {
            this.$refs.callsMobileList?.reset?.()
        }
    }
}
</script>
