<template>
    <div class="event_card rounded-lg select-none" :class="[collapse && 'card_open', useInject && 'bg_invert']">
        <div class="event_card__wrapper" :class="!isAttendingNull && 'cursor-pointer'" @click="collapseCard()">
            <div :class="!isMobile && 'flex gap-4'">
                <div v-if="!isMobile">
                    <div class="icon_wrap rounded-lg">
                        <div class="icon_wrap__bg" :style="`background: ${event.color};`" />
                        <i class="fi fi-rr-calendar-lines" :style="`color: ${event.color};`" />
                    </div>
                </div>
                <div 
                    class="truncate w-full" 
                    :class="!isMobile && 'flex items-center justify-between gap-5'">
                    <div class="truncate">
                        <div class="truncate" :class="isMobile && 'flex items-center justify-between gap-2'">
                            <div class="flex items-center mb-1 truncate" @click.stop="openEvent()">
                                <div class="truncate font-semibold card_name" :title="event.name">
                                    <a-badge v-if="isMobile" :color="event.color" />
                                    <span :class="isPastEvent && 'line-through'">{{ event.name }}</span>
                                </div>
                            </div>
                            <div v-if="isMobile">
                                <a-spin v-if="actionsLoading" size="small" />
                                <i v-else class="fi fi-rr-angle-small-down card_arrow block" style="opacity: 0.5;font-size: 16px;" />
                            </div>
                        </div>
                        <div class="flex items-center gap-5">
                            <component :is="relatedUsersComp" :relatedUsers="event.related_users" :storeKey="storeKey" />
                            <div class="flex items-center opacity-80" :title="$t('workplan.event_duration')">
                                <i class="fi fi-rr-clock mr-1" />{{ eventDateTime }}
                            </div>
                            <div class="flex items-center opacity-80">
                                <i class="fi fi-rr-marker mr-1" /> {{ $t('workplan.event_online') }}
                            </div>
                        </div>
                        <component 
                            v-if="event.related_object" 
                            :is="relatedObjectComp"
                            :related_object="event.related_object" />
                        <template v-if="!isActiveFilter && isMobile && !isPastEvent && !isAttendingNull">
                            <a-spin :spinning="loading" size="small" class="w-full">
                                <div class="flex items-center gap-2 mt-3">
                                    <a-button 
                                        :type="!isAttending ? event.is_attending ? 'primary' : 'flat_primary' : 'flat_primary'" 
                                        flaticon 
                                        block 
                                        icon="fi-rr-check-circle" 
                                        class="flex items-center justify-center" 
                                        @click.stop="isAttendingHandler(true)">
                                        {{ $t('workplan.event_go') }}
                                    </a-button>
                                    <a-button 
                                        :type="!isAttending ? !event.is_attending ? 'primary' : 'flat_danger' : 'flat_danger'" 
                                        flaticon 
                                        block 
                                        icon="fi-rr-cross-circle" 
                                        class="flex items-center justify-center" 
                                        @click.stop="isAttendingHandler(false)">
                                        {{ $t('workplan.event_not_go') }}
                                    </a-button>
                                </div>
                            </a-spin>
                        </template>
                    </div>
                    <div v-if="!isMobile" class="flex items-center gap-4">
                        <template v-if="!isActiveFilter && !isAttendingNull">
                            <a-spin v-if="!isPastEvent" :spinning="loading" size="small" class="mb-2">
                                <div class="flex items-center gap-2">
                                    <a-button 
                                        :type="!isAttending ? event.is_attending ? 'primary' : 'flat_primary' : 'flat_primary'" 
                                        flaticon 
                                        icon="fi-rr-check-circle" 
                                        class="flex items-center" 
                                        @click.stop="isAttendingHandler(true)">
                                        {{ $t('workplan.event_go') }}
                                    </a-button>
                                    <a-button 
                                        :type="!isAttending ? !event.is_attending ? 'primary' : 'flat_danger' : 'flat_danger'" 
                                        flaticon 
                                        icon="fi-rr-cross-circle" 
                                        class="flex items-center" 
                                        @click.stop="isAttendingHandler(false)">
                                        {{ $t('workplan.event_not_go') }}
                                    </a-button>
                                </div>
                            </a-spin>
                        </template>
                        <div>
                            <a-spin v-if="actionsLoading" size="small" />
                            <i v-else class="fi fi-rr-angle-small-down card_arrow block" style="opacity: 0.5;font-size: 16px;" />
                        </div>
                    </div>
                </div>
            </div>
        </div>
        <div v-if="collapse" class="collapse_wrapper">
            <div class="collapse_wrapper__divider" />
            <component :is="collapseBodyComp" :event="event" :storeKey="storeKey" />
        </div>
    </div>
</template>

<script>
import { errorHandler } from '@/utils/index.js'
const listType = 'eventList'
export default {
    props: {
        event: {
            type: Object,
            required: true
        },
        storeKey: {
            type: String,
            required: true
        },
        useInject: {
            type: Boolean,
            default: false
        }
    },
    computed: {
        collapseBodyComp() {
            if(this.collapse)
                return () => import('./CollapseBody.vue')
            return null
        },
        collapse: {
            get() {
                return this.event.collapse || false
            },
            set(value) {
                this.$store.commit('workplan/CHANGE_COLLAPSE', {
                    storeKey: this.storeKey,
                    value,
                    item: this.event,
                    list: listType
                })
            }
        },
        relatedObjectComp() {
            if(this.event.related_object)
                return () => import('../RelatedObject.vue')
            return false
        },
        relatedUsersComp() {
            if(this.event.related_users?.length)
                return () => import('../RelatedUsers.vue')
            return null
        },
        isAttendingNull() {
            if(typeof this.event.is_attending === 'undefined')
                return true
            return false
        },
        isAttending() {
            if(typeof this.event.is_attending === 'undefined')
                return false
            if(typeof this.event.is_attending === 'boolean')
                return false
            return true
        },
        isPastEvent() {
            if (!this.event) return false
            if (this.event.all_day) return false
            const now = this.$moment()
            const start = this.$moment(this.event.start_at)
            const end = this.$moment(this.event.end_at)
            return start.isBefore(now) && end.isBefore(now)
        },
        isMobile() { 
            return this.$store.state.isMobile
        },
        eventDateTime() {
            if (!this.event) return null

            const start = this.$moment(this.event.start_at)
            const end = this.$moment(this.event.end_at)

            if (start.isSame(end, 'day')) {
                if (this.event.all_day) return this.$t('calendar.all_day')
                return `${start.format('HH:mm')} - ${end.format('HH:mm')}`
            }

            if (this.event.all_day) {
                const startLabel = start.format('ddd, DD MMM')
                const endLabel = end.format('ddd, DD MMM')
                if (startLabel === endLabel) return this.$t('calendar.all_day')
                return `${startLabel} - ${endLabel}`
            }

            return `${start.format('DD.MM.YYYY HH:mm')} - ${end.format('DD.MM.YYYY HH:mm')}`
        },
        project() {
            return this.$store.state.workplan.project?.[this.storeKey] || null
        },
        workgroup() {
            return this.$store.state.workplan.workgroup?.[this.storeKey] || null
        },
        user() {
            return this.$store.state.workplan.user?.[this.storeKey] || null
        },
        isActiveFilter() {
            return this.project || this.workgroup || this.user?.length
        },
    },
    data() {
        return {
            loading: false,
            actionsLoading: false
        }
    },
    methods: {
        async getActions() {
            try {
                this.actionsLoading = true
                await this.$store.dispatch('workplan/getEventActions', {
                    storeKey: this.storeKey,
                    item: this.event,
                    list: listType
                })
            } catch(error) {
                errorHandler({error, show: false})
            } finally {
                this.actionsLoading = false
            }
        },
        async collapseCard() {
            if(!this.event.actions)
                await this.getActions()
            this.collapse = !this.collapse
        },
        isAttendingHandler(is_attending) {
            this.$confirm({
                title: is_attending ? this.$t('workplan.event_confirm_go') : this.$t('workplan.event_confirm_not_go'),
                content: '',
                okText: this.$t('workplan.confirm'),
                zIndex: 999999,
                closable: true,
                maskClosable: true,
                cancelText: this.$t('workplan.cancel'),
                onOk: async () => {
                    try {
                        this.loading = true
                        const { data } = await this.$http.post(`/calendars/events/${this.event.id}/attendance/`, {is_attending})
                        if(data) {
                            this.$store.commit('workplan/SET_IS_ATTENDING', {
                                list: listType,
                                storeKey: this.storeKey,
                                value: is_attending,
                                item: this.event
                            })
                        }
                    } catch(error) {
                        errorHandler({error})
                    } finally {
                        this.loading = false
                    }
                }
            })
        },
        openEvent() {
            if(!this.isAttendingNull) {
                const query = JSON.parse(JSON.stringify(this.$route.query))
                query.event = this.event.id
                this.$router.replace({query})
            }
        }
    }
}
</script>

<style lang="scss" scoped>
.collapse_wrapper{
    padding-left: 15px;
    padding-right: 15px;
    padding-bottom: 15px;
    @media (min-width: 768px) {
        padding-left: 20px;
        padding-right: 20px;
        padding-bottom: 20px;
    }
    &__divider{
        margin-bottom: 15px;
        height: 1px;
        background: #e8e8e8;
        @media (min-width: 768px) {
            margin-bottom: 20px;
        }
    }
}
.attending{
    background: #F8F9FD;
    border-radius: 20px;
    padding: 4px 8px;
    min-width: 85px;
}
.is_attending{
    color: rgb(22, 163, 74);
}
.is_no_attending{
    color: rgb(254, 92, 92);
}
.card_name{
    transition: all 0.3s cubic-bezier(0.645, 0.045, 0.355, 1);
    &:hover{
        color: var(--blue);
    }
}
.event_card{
    background: #fff;
    &.bg_invert{
        background: #f7f9fc;
    }
    &__wrapper{
        padding: 15px;
        @media (min-width: 768px) {
            padding: 20px;
        }
    }
    .card_arrow{
        transition: all 0.3s cubic-bezier(0.645, 0.045, 0.355, 1);
    }
    &.card_open{
        .card_arrow{
            transform: rotate(180deg);
        }
    }
    &:not(:last-child){
        margin-bottom: 10px;
        @media (min-width: 768px) {
            margin-bottom: 15px;
        }
    }
    .icon_wrap{
        width: 36px;
        height: 36px;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 18px;
        position: relative;
        overflow: hidden;
        i{
            position: relative;
            z-index: 5;
        }
        &__bg{
            opacity: 0.2;
            position: absolute;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
        }
    }
}
</style>
