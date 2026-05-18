<template>
    <div class="list_item_wrapper">
        <a-card
            style="border-radius: var(--borderRadius);"
            size="small"
            v-touch:longtap="longtapHandler"
            :bordered="false"
            :ref="`task_card_${item.id}`"
            :class="isMobile ? 'mmb mobile_card' : 'mb-2'"
            class="list_item">
            <div class="consolidation_name mb-3 blue_color" @click="openConsolidation">{{item.name}}</div>
            <template v-if="item.is_scheduled">
                <div class="grid grid-cols-2 justify-between">
                    <div class="flex ">
                        <ConsolidationRepeatPeriodRow
                            class="repeat_period"
                            :record="item" />
                        <span class="auto_approve_icon">
                            <i v-if="item.auto_approve" class="fi fi-rr-bolt ml-2"></i>
                        </span>
                    </div>
                    <RepeatToRow
                        class="repeat_to"
                        :record="item"/>
                </div>
            </template>
            <template v-else>
                <div class="grid grid-cols-2 justify-between">
                    <div class="flex ">
                        <DeadLine
                            class="justify-self-start"
                            :status="item.status" 
                            :date="item.dead_line" />
                        <span class="auto_approve_icon"><i v-if="item.auto_approve" class="fi fi-rr-bolt ml-2"></i></span>
                    </div>
                    <a-tag :color="item.status.color" class="justify-self-end">{{ item.status.name }}</a-tag>
                </div>
            </template>
            <ListItemActions
                :ref="`consolidation_actions_${item.id}`"
                :item="item"
                :record="item"
                :id="item.id"
                :showButton="false"
                :showStatus="showStatus" />
        </a-card>
    </div>
</template>

<script>
export default {
    components: {
        ListItemActions: () => import('./ListItemActions.vue'),
        ConsolidationRepeatPeriodRow: () => import('@/components/TableWidgets/Widgets/ConsolidationRepeatPeriodRow.vue'),
        RepeatToRow: () => import('@/components/TableWidgets/Widgets/RepeatToRow.vue'),
        DeadLine: () => import('@apps/Consolidation/components/DeadLine')
    },
    props: {
        item: [Object],
        showStatus: {
            type: Boolean,
            default: false
        },
    },
    computed: {
        isMobile() {
            return this.$store.state.isMobile
        },
    },
    methods: {
        longtapHandler() {
            if(this.isMobile) {
                this.$refs[`consolidation_actions_${this.item.id}`].openDrawer()
            }
        },
        openConsolidation() {
            const query = Object.assign({}, this.$route.query)
            if(!query.consolidation) {
                query.consolidation = this.item.id
                this.$router.push({query})
            }
        },
    }
}
</script>

<style lang="scss" scoped>
.list_item_wrapper {

    .list_item{
        &.mobile_card{
            transition: all 0.5s cubic-bezier(0.645, 0.045, 0.355, 1);
            &.touch{
                box-shadow: 0 2px 8px rgba(0, 0, 0, 0.15);
                transform: scale(0.97);
            }
        }
        &.mmb{
            margin-bottom: 10px;
        }
        .consolidation_name {
            min-height: 45px;
        }
        .repeat_period {
            justify-self: start;
            min-width: 110px;
        }
        .repeat_to {
            justify-self: end;
        }
        .auto_approve_icon {
            min-width: 22px;
        }
        .template_icon {
            min-width: 22px;
        }
    }
}
</style>