<template>
    <div class="o_card">
        <div class="flex items-center mb-3">
            <div :key="currentOrg.logo" class="pr-2">
                <a-avatar 
                    :size="35"
                    :src="currentOrg.logo"
                    icon="fi-rr-users-alt" 
                    flaticon />
            </div>
            <span>{{ currentOrg.name }}</span>
        </div>
        <div class="o_card__row">
            <div class="o_card__row--label">
                {{ $t('team.connection_type') }}
            </div>
            <div class="o_card__row--value">
                <RelationType :record="item" :org="org" />
            </div>
        </div>
    </div>
</template>

<script>
import RelationType from './RelationType.vue'
export default {
    components: {
        RelationType
    },
    props: {
        item: {
            type: Object,
            required: true
        },
        org: {
            type: Object,
            required: true
        }
    },
    computed: {
        currentOrg() {
            if(this.item.contractor.id === this.org.id)
                return this.item.contractor_parent
            else
                return this.item.contractor
        }
    }
}
</script>

<style lang="scss" scoped>
.o_card{
    padding: 12px;
    zoom: 1;
    color: #505050;
    font-size: 14px;
    font-variant: tabular-nums;
    line-height: 1.5;
    list-style: none;
    font-feature-settings: "tnum";
    background: #fff;
    border-radius: var(--borderRadius);
    border: 1px solid var(--border1);
    margin-bottom: 10px;
    -webkit-user-select: none;
    -moz-user-select: none;
    user-select: none;
    &__row{
        display: flex;
        align-items: center;
        &:not(:last-child){
            margin-bottom: 5px;
        }
        &--label{
            margin-right: 5px;
            color: var(--gray);
        }
    }
}
</style>