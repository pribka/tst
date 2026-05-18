<template>
    <div 
        class="org_card" 
        :ref="`team_card_${item.id}`" 
        @click="openOrgDrawer(item)">
        <div class="flex justify-between">
            <div class="flex items-center mb-3">
                <div :key="item.logo" class="pr-2">
                    <a-avatar 
                        :size="35"
                        :src="item.logo"
                        icon="fi-rr-users-alt" 
                        flaticon />
                </div>
                <span class="font-semibold">{{ item.name }}</span>
            </div>
            <div class="pl-3">
                <a-tag color="purple" class="flex items-center">
                    <i class="fi fi-rr-users-alt mr-1"></i>
                    {{ item.members_count }}
                </a-tag>
            </div>
        </div>
        <div v-if="item.inn" class="org_card__row">
            <div class="org_card__row--label">
                {{ $t('team.bin_iin') }}:
            </div>
            <div class="org_card__row--value">
                {{ item.inn }}
            </div>
        </div>
        <div v-if="item.email" class="org_card__row">
            <div class="org_card__row--label">
                E-mail:
            </div>
            <div class="org_card__row--value">
                {{ item.email }}
            </div>
        </div>
        <div v-if="item.phone" class="org_card__row">
            <div class="org_card__row--label">
                {{ $t('team.phone') }}:
            </div>
            <div class="org_card__row--value">
                {{ item.phone }}
            </div>
        </div>
        <ActionDrawer
            ref="team_action"
            :id="item.id"
            :reloadMainList="reloadMainList"
            :record="item" />
    </div>
</template>

<script>
import { onLongPress } from '@vueuse/core'
export default {
    components: {
        ActionDrawer: () => import('./Actions/Drawer.vue')
    },
    props: {
        item: {
            type: Object,
            required: true
        },
        isScrolling: {
            type: Boolean,
            default: false
        },
        openOrgDrawer: {
            type: Function,
            default: () => {}
        },
        reloadMainList: {
            type: Function,
            default: () => {}
        }
    },
    mounted() {
        this.$nextTick(() => {
            onLongPress(this.$refs[`team_card_${this.item.id}`], event => {
                if(!this.isScrolling) {
                    event.preventDefault()
                    event.stopPropagation()
                    event.stopImmediatePropagation()
                    this.$refs.team_action.openActionDrawer()
                }
            }, { modifiers: { prevent: true } })
        })
    }
}
</script>

<style lang="scss" scoped>
.org_card{
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