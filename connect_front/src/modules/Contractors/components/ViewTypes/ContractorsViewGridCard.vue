<template>
    <div class="contractor_card">
        <a-card
            :ref="`contractor_card_${contractor.id}`"
            :size="isMobile ? 'small' : 'default'"
            class="h-full">
            <div class="mb-1 flex items-center justify-between">
                <a-tag :color="contractor.status.color">{{ contractor.status.value }}</a-tag>
                <component
                    :ref="`contractor_actions_${contractor.id}`"
                    :is="actionComponent"
                    :record="contractor"/>
            </div>
            <div class="mb-2 text-base font-bold">
                <div v-if=contractor.name>
                    {{ contractor.name }}
                </div>
                <div v-else class="text-gray-400">
                    Имя не указано
                </div>
            </div>

            <div class="ml-2">
                <!-- Phone -->
                <div class="flex items-center mb-2">
                    <a-icon class="mr-2" type="phone" />
                    <a 
                        v-if="contractor.phone"
                        :href="`tel:${contractor.phone}`">
                        {{ contractor.phone }}
                    </a>
                    <span
                        v-else 
                        class="text-gray-400">
                        Номер телефона не указан
                    </span>
                </div>
                <!-- Email -->
                <div class="flex items-center mb-2">
                    <a-icon class="mr-2" type="mail" />
                    <a  
                        v-if="contractor.email"
                        :href="'mailto:' + contractor.email">
                        {{ contractor.email }}
                    </a>
                    <span 
                        v-else
                        class="text-gray-400">
                        Адрес не указан
                    </span>
                </div>
                <template v-if="isLead">
                    <!-- Organization -->
                    <div class="mb-2 flex items-center justify-between item_row">
                        <div class="flex items-center text-clip overflow-hidden">
                            <a-icon class="mr-2" type="team" />
                            <span v-if="contractor.company_name">
                                {{ contractor.company_name }}
                            </span>
                            <span 
                                v-else 
                                class="text-gray-400">
                                Организация не указана
                            </span>
                        </div>
                    </div>
                </template>
                <template v-else>
                    <!-- INN -->
                    <div class="flex items-center mb-2">
                        <a-icon class="mr-2" type="info-circle" />
                        <span v-if="contractor.inn">
                            {{ contractor.inn }}
                        </span>
                        <span 
                            v-else 
                            class="text-gray-400">
                            Не указан
                        </span>
                    </div>
                    <!-- Address -->
                    <div class="flex items-center mb-2">
                        <a-icon class="mr-2" type="car" />
                        <span class="mr-2">
                            <span v-if="contractorDeliveryAddress">
                                {{ contractorDeliveryAddress }}
                            </span>
                            <span 
                                v-else
                                class="text-gray-400" >
                                Не указан
                            </span>
                        </span>
                        <a-icon
                            v-show="edit"
                            type="edit"
                            class="text-base text_hover"
                            @click="editDeliveryPoint()" />
                    </div>
                </template>
                

            </div>
            <!-- Contact person -->
            <template v-if="contractor.nearest_event">
                <!-- <div class="mb-2">
                    <span class="mr-2">
                        <i class="fi fi-rr-calendar-star"></i>
                    </span>
                    <span>
                        {{ eventStartTime }} - {{ contractor.nearest_event.name }}
                    </span>
                </div> -->
                <CardEvent :event="contractor.nearest_event"/>
            </template>
            <template v-if="!isLead">
                <div class="mt-2 mb-1 flex items-center justify-between item_row">
                    <template v-if=contractor.contact_person>     
                        <Profiler :user=contractor.contact_person />
                    </template>
                    <template v-else>
                        <div class="flex items-center">
                            <a-avatar icon="user" />
                            <span class="ml-2 text-gray-400">Не указан</span>
                        </div>
                    </template>
                </div>
            </template>
            
        </a-card>
        <component
            :is="addOrderDrawer"
            :contractorID="contractor.id"
            :contrsctorDeliveryPoint="contractor.delivery_point"
            :injectContractor="injectContractor"
            page_name="crm.order_create_page"
            ref="orderDrawer" />
    </div>
</template>

<script>
import eventBus from '@/utils/eventBus.js'
import { mapState } from 'vuex'
import CardEvent from '../CardParts/CardEvent'
import { onLongPress } from '@vueuse/core'

export default {
    name: 'ContractorCard',
    components: {
        CardEvent,
    },
    props: {
        contractor: {
            type: Object,
            default: () => {}
        },
        cart: {
            type: Boolean,
            default: false
        },
        edit: {
            type: Boolean,
            default: false
        },
        deliveryPointAddress: {
            type: String,
            default: ''
        },
        deliveryPointID: {
            type: String,
            default: ''
        }
    },
    data() {
        return {
            injectContractor: null
        }
    },
    computed: {
        ...mapState({
            contractorsType: state => state.contractors.contractorsType,
            isMobile: state => state.isMobile
        }),
        actionComponent() {
            if(this.isMobile)
                return () => import('../ActionsMobile.vue')
            return () => import('../Actions.vue')
        },
        eventStartTime() {
            if(this.contractor.nearest_event)
                return this.$moment(this.contractor.nearest_event.start).calendar()
            return null
        },
        addOrderDrawer() {
            return () => import('@apps/Orders/views/CreateOrder/OrderDrawer.vue')
        },
        contractorDeliveryAddress() {
            return this.deliveryPointAddress ? this.deliveryPointAddress : this.contractor.delivery_address
        },
        isLead() {
            return this.contractorsType === 'leads'
        }
    },
    mounted() {
        if(this.isMobile) {
            this.$nextTick(() => {
                onLongPress(this.$refs[`contractor_card_${this.contractor.id}`], event => {
                    if(!this.isScrolling) {
                        event.preventDefault()
                        event.stopPropagation()
                        event.stopImmediatePropagation()
                        this.$refs[`contractor_actions_${this.contractor.id}`].openDrawer()
                    }
                }, { modifiers: { prevent: true } })
            })
        }
    },
    methods: {
        createOrder() {
            this.injectContractor = {
                contractor: {
                    id: this.contractor.id,
                },
                delivery_point: {
                    id: this.getDeliveryPointID(),
                }
            }
            this.$nextTick(() => {
                if(this.$refs['orderDrawer']) {
                    this.$refs['orderDrawer'].toggleDrawer()
                }
            })
        },
        getDeliveryPointID() {
            if(this.deliveryPointID) {
                return this.deliveryPointID
            } else if(this.contractor.delivery_point) {
                return this.contractor.delivery_point
            } else {
                return null
            }
        },
        editContractor() {
            eventBus.$emit('edit_contractor', this.contractor.id)
        },
        editDeliveryPoint() {
            eventBus.$emit('open_delivery_points_drawer', this.contractor.id, 'contractorsWidget')
        }
    }
}
</script>

<style lang="scss" scoped>
.text_hover {
    transition: color 0.15s ease-in;
    &:hover {
        color: var(--blue);
    }
}
</style>