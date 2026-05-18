<template>
    <div>
        <div 
            class="card_row_label flex items-center cursor-pointer justify-between rounded-lg" 
            :class="intentsCollapse && 'active'"
            @click="intentsCollapse = !intentsCollapse">
            <div class="flex items-center">
                <img src="@/assets/svg/ai_icons.svg" class="mr-2" />
                {{ $t('workplan.intents_found_title') }} <template v-if="detail.intents.length">({{ detail.intents.length }})</template>
            </div>
            <div class="ml-2">
                <i class="fi fi-rr-angle-small-down inline-block" />
            </div>
        </div>
        <div v-if="intentsCollapse" class="intents_sw_list">
            <component 
                v-for="(intents, index) in detail.intents" 
                useInject
                :is="intentsSwitchComp"
                :key="intents.id"
                :injectDelete="intentDelete"
                :messageIndex="index"
                :injectCreated="createdHandler"
                :injectUpdate="handlerChangeField"
                :injectChangeField="intentsChangeField"
                :intents="intents"
                :intentIndex="index"
                :message="{name: 'message'}" />
        </div>
    </div>
</template>

<script>
const listType = 'meetingList'
export default {
    props: {
        detail: {
            type: Object,
            required: true
        },
        item: {
            type: Object,
            required: true
        },
        storeKey: {
            type: String,
            required: true
        },
        intentDelete: {
            type: Function,
            default: () => {}
        },
        handlerChangeField: {
            type: Function,
            default: () => {}
        },
        createdHandler: {
            type: Function,
            default: () => {}
        },
        intentsChangeField: {
            type: Function,
            default: () => {}
        },
        useLocalStore: {
            type: Boolean,
            default: false
        }
    },
    data() {
        return {
            collapseOpen: false
        }
    },
    computed: {
        intentsCollapse: {
            get() {
                if(this.useLocalStore)
                    return this.collapseOpen
                return this.item.intentsCollapse || false
            },
            set(value) {
                if(this.useLocalStore) {
                    this.collapseOpen = value
                } else {
                    this.$store.commit('workplan/CHANGE_INTENTS_COLLAPSE', {
                        storeKey: this.storeKey,
                        value,
                        item: this.item,
                        list: listType
                    })
                }
            }
        },
        intentsSwitchComp() {
            if(this.intentsCollapse)
                return () => import('@apps/AIAssistant/Drawer/Message/IntentsSwitch.vue')
            return null
        },
    }
}
</script>

<style lang="scss" scoped>
.card_row_label{
    font-weight: 600;
    color: #000;
    margin-bottom: 15px;
    background: rgb(223, 237, 255);
    padding: 10px 15px;
    img{
        max-width: 18px;
    }
    &.active{
        i{
            &.fi{
                transform: rotate(180deg);
            }
        }
    }
}
.intents_sw_list{
    &::v-deep{
        .intents_card{
            border-radius: 0px;
            &:not(:last-child){
                border-bottom: 1px solid #e8e8e8;
                padding-bottom: 15px;
                margin-bottom: 15px;
            }
        }
    }
}
</style>
