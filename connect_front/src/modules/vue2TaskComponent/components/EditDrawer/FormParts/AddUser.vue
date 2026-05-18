<template>
    <div>
        <div class="tab_selects">
            <div class="flex items-center px-2">
                <a-button 
                    v-if="isMobile"
                    shape="circle"
                    flaticon
                    icon="fi-rr-angle-small-left"
                    @click="scrollLeft" />
                <div 
                    class="scroll-container md:grid md:gap-4 md:grid-cols-4 tab_selects__wrap"
                    ref="scrollable">
                    <div v-for="tab in userTypeTab" :key="tab.value" class="tab_selects__wrap--item">
                        <a-button
                            block
                            size="large"
                            class="mr-2.5 last:mr-0 button-gray"
                            :class="activeUserTab === tab.value && 'active'"
                            @click="selectUserTab(tab.value)">
                            {{ tab.label }}
                        </a-button>
                    </div>
                </div>
                <a-button 
                    v-if="isMobile"
                    shape="circle"
                    flaticon
                    icon="fi-rr-angle-small-right"
                    @click="scrollRight" />
            </div>            
        </div>
        <div v-show="activeUserTab === 'operator'">
            <div class="pt-5">
                <a-form-model-item
                    v-if="formInfo.operator"
                    :rules="formInfo.operator.rules"
                    :label="formInfo.operator.title"
                    prop="operator"
                    style="margin-bottom: 0px;"
                    class="mb-0">
                    <div>
                        <UserDrawer
                            v-model="value.operator"
                            :taskId="value.id ? value.id : null"
                            :id="value.id || defaultUserSelectId"
                            class="w-full"
                            :disabled="value.is_auction"
                            :filters="
                                formInfo.operator.filters
                                    ? formInfo.operator.filters
                                    : null
                            "
                            :oldSelected="checkOldSelect(formInfo.operator)"
                            :title="
                                formInfo.operator.drawerTitle ||
                                    $t('task.select_performer')
                            "/>
                    </div>
                    <a-checkbox
                        v-if="formInfo.operator.auction && isTask"
                        v-model="value.is_auction"
                        @click="selectAuction()">
                        {{ $t("Activate auction") }}
                    </a-checkbox>
                </a-form-model-item>
            </div>
        </div>

        <div v-show="activeUserTab === 'owner'">
            <div class="pt-5">
                <a-form-model-item
                    v-if="formInfo.owner"
                    :rules="formInfo.owner.rules"
                    :label="formInfo.owner.title"
                    class="mb-0"
                    style="margin-bottom: 0px;"
                    prop="owner">
                    <UserDrawer
                        :id="value.id || defaultUserSelectId"
                        v-model="value.owner"
                        :taskId="value.id ? value.id : null"
                        :title="
                            formInfo.owner.drawerTitle ||
                                $t('task.select_author')
                        "/>
                </a-form-model-item>
            </div>
        </div>

        <div v-show="activeUserTab === 'cooperators'">
            <div class="pt-5">
                <a-form-model-item
                    v-if="formInfo.cooperators"
                    :rules="formInfo.cooperators.rules"
                    :label="formInfo.cooperators.title"
                    class="mb-0"
                    style="margin-bottom: 0px;"
                    prop="visors">
                    <UserDrawer
                        :id="value.id || defaultUserSelectId"
                        :metadata="{ key: 'cooperators', value: value.metadata }"
                        :changeMetadata="changeMetadata"
                        v-model="value.cooperators"
                        :taskId="value.id ? value.id : null"
                        multiple
                        :title="
                            formInfo.cooperators.drawerTitle ||
                                $t('task.select_cooperators')
                        "/>
                </a-form-model-item>

            </div>
        </div>

        <div v-show="activeUserTab === 'visors'">
            <div class="pt-5">
                <a-form-model-item
                    v-if="formInfo.visors"
                    :rules="formInfo.visors.rules"
                    :label="formInfo.visors.title"
                    class="mb-0"
                    style="margin-bottom: 0px;"
                    prop="visors">
                    <UserDrawer
                        :id="value.id || defaultUserSelectId"
                        :metadata="{ key: 'visors', value: value.metadata }"
                        :changeMetadata="changeMetadata"
                        v-model="value.visors"
                        :taskId="value.id ? value.id : null"
                        multiple
                        :title="
                            formInfo.visors.drawerTitle ||
                                $t('task.select_observers')
                        "/>
                </a-form-model-item>
            </div>
        </div>
    </div>
</template>

<script>
export default {
    components: {
        UserDrawer: () => import("@apps/DrawerSelect/index.vue")
    },
    props: {
        value: { // form
            type: Object,
            required: true
        },
        formInfo: {
            type: Object,
            required: true
        },
        defaultUserSelectId: {
            type: String,
            default: 'empty_task'
        },
        edit: {
            type: Boolean,
            required: false
        },
        changeMetadata: {
            type: Function,
            required: true
        },
        checkOldSelect: {
            type: Function,
            required: true
        },
        isMilestone: {
            type: Boolean,
            default: false
        },
        isStage: {
            type: Boolean,
            default: false
        }
    },
    computed: {
        isMobile() {
            return this.$store.state.isMobile
        },
        isTask() {
            return this.isMilestone || this.isStage ? false : true
        },
        userTypeTab() {
            if(this.isTask) {
                return [
                    {
                        value: "operator",
                        label: this.$t("Operator")
                    },
                    {
                        value: "cooperators",
                        label: this.$t("Cooperator")
                    },
                    {
                        value: "owner",
                        label: this.$t("Owner")
                    },
                    {
                        value: "visors",
                        label: this.$t("Visors")
                    }
                ]
            }
            return [
                {
                    value: "operator",
                    label: this.$t("Operator")
                },
                {
                    value: "owner",
                    label: this.$t("Owner")
                }
            ]
        }
    },
    data() {
        return {
            activeUserTab: 'operator'
        }
    },
    methods: {
        scrollLeft() {
            this.$refs.scrollable.scrollBy({ left: -200, behavior: "smooth" });
        },
        scrollRight() {
            this.$refs.scrollable.scrollBy({ left: 200, behavior: "smooth" });
        },

        selectUserTab(value) {
            this.activeUserTab = value;
        },
        selectAuction() {
            const form = {
                ...this.value,
                operator: null,
                is_auction: !this.value.is_auction
            }
            this.$emit('input', form)
        },
    }
}
</script>

<style lang="scss" scoped>
.tab_selects{
    @media (max-width: 767.98px) {
        margin-left: -15px;
        margin-right: -15px;
        &__wrap{
            display: -webkit-box;
            margin-bottom: 0;
            overflow-x: scroll;
            padding-left: 15px;
            padding-right: 15px;
            scroll-behavior: smooth;
            scroll-snap-type: x mandatory;
            width: 100%;
            -ms-overflow-style: none;
            scrollbar-width: none;
            -webkit-overflow-scrolling: touch;
            &::-webkit-scrollbar {
                display: none;
            }
            &--item{
                margin-right: 10px;
            }
        }
    }
}
</style>