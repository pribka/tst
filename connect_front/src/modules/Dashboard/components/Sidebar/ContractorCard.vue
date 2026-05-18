<template>
    <div class="contractor_card">
        <a-card>
            <div class="flex items-stretch justify-between flex-row">
                <div class="title basis-3/4 self-center text-base font-bold" v-show="contractor.name">
                    {{ contractor.name }}
                    <a-icon
                        v-show="edit"
                        type="edit"
                        class="inline-block align-middle ml-1"
                        @click="editContractor()" />
                </div>
                <div class="basis-1/4 self-center text-3xl font-bold">
                    <a-popover>
                        <template slot="content">
                            <p class="text-center">{{ $t('dashboard.order.create') }}</p>
                        </template>
                        <a-icon
                            v-show="cart"
                            class="cart inline-block align-top"
                            shape="circle"
                            type="shopping-cart"
                            @click="createOrder()" />
                    </a-popover>
                </div>
            </div>
            <div class="flex items-stretch justify-between flex-row">
                <div class="basis-3/4 pr-2">
                    <div class="contact">
                        <a-icon class="inline-block align-middle mr-1 ml-3 my-1" type="phone" />
                        <div class="contact_text" v-if="contractor.phone"><a :href="'tel:' + contractor.phone">{{ contractor.phone }}</a></div>
                        <div class="contact_text text-gray-300" v-else>{{ $t('dashboard.contractor.not_provided') }}</div>
                    </div>
                    <div class="contact">
                        <a-icon class="inline-block align-middle mr-1 ml-3 my-1" type="mail" />
                        <div class="contact_text" v-if="contractor.email"><a :href="'mailto:' + contractor.email">{{ contractor.email }}</a></div>
                        <div class="contact_text text-gray-300" v-else>{{ $t('dashboard.contractor.not_provided') }}</div>
                    </div>
                    <div class="contact">
                        <a-icon class="inline-block align-middle mr-1 ml-3 my-1" type="info-circle" />
                        <div class="contact_text" v-if="contractor.inn">{{ contractor.inn }}</div>
                        <div class="contact_text text-gray-300" v-else>{{ $t('dashboard.contractor.not_provided') }}</div>
                    </div>
                    <div class="contact">
                        <a-icon class="inline-block align-middle mr-1 ml-3 my-1" type="car" />
                        <div class="contact_text" v-if="contractorDeliveryAddress">{{ contractorDeliveryAddress }}
                            <a-icon
                                v-show="edit"
                                type="edit"
                                class="inline-block align-middle ml-1"
                                @click="editDeliveryPoint()" />
                        </div>
                        <div class="contact_text text-gray-300" v-else>{{ $t('dashboard.contractor.not_provided') }}
                            <a-icon
                                v-show="edit"
                                type="edit"
                                class="inline-block align-middle ml-1 text-black"
                                @click="editDeliveryPoint()" />
                        </div>
                    </div>
                    <a-popover>
                        <template slot="content">
                            <p>{{ $t('dashboard.order.previous_date') }}</p>
                        </template>
                        <div class="contact">
                            <a-icon class="inline-block align-middle mr-1 ml-3 my-1" type="clock-circle" />
                            <div class="contact_text" v-if="contractor.last_order_date">{{ contractor.last_order_date }}</div>
                            <div class="contact_text text-gray-300" v-else>{{ $t('dashboard.order.no_orders') }}</div>
                        </div>
                    </a-popover>
                </div>
                <div class="basis-1/4 flex flex-col">
                    <a-popover>
                        <template slot="content">
                            <p class="text-center">{{ $t('dashboard.order.completed') }}</p>
                        </template>
                        <a-tag color="green" class="info_tag mt-1 text-sm">
                            <a-icon class="info_tag inline-block align-middle mr-1" type="check" />{{ contractor.total_orders }}
                        </a-tag>
                    </a-popover>
                    <a-popover>
                        <template slot="content">
                            <p class="text-center">{{ $t('dashboard.order.in_progress') }}</p>
                        </template>
                        <a-tag color="purple" class="info_tag mt-1 text-sm">
                            <a-icon class="inline-block align-middle mr-1" type="tool" />{{ contractor.orders_in_progress }}
                        </a-tag>
                    </a-popover>
                </div>
            </div>
            <div class="contact contact_person" v-if="contractor.contact_person">
                <!-- <Profiler :user=contractor.curator /> -->
                <Profiler :user="contractor.contact_person" />
            </div>
            <div class="flex items-center gap-x-2 text-gray-300" v-else>
                <a-avatar src="" icon="user" />
                <div>{{ $t('dashboard.contractor.not_provided') }}</div>
            </div>
        </a-card>
        <component
            :is="addOrderDrawer"
            :contractorID="contractor.id"
            :contractorDeliveryPoint="contractor.delivery_point"
            :injectContractor="injectContractor"
            page_name="crm.order_create_page"
            ref="orderDrawer" />
    </div>
</template>

<script>
import eventBus from '@/utils/eventBus.js'

export default {
    name: 'ContractorCard',
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
        addOrderDrawer() {
            return () => import('@apps/Orders/views/CreateOrder/OrderDrawer.vue')
        },
        contractorDeliveryAddress() {
            return this.deliveryPointAddress ? this.deliveryPointAddress : this.contractor.delivery_address
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
.contractor_card{
    margin-bottom: 5px;
    .contact {
        display: flex;
        align-items: center;
    }
    .contact_text {
        align-self: flex-end;
        margin-left: 5px;
    }
    .contact_person {
        margin-left: 3px;
        margin-top: 5px;
    }
}
</style>