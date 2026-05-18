<template>
    <div :class="isMobile ? 'mobile_wrapper' : 'wrapper'">
        <component 
            :is="viewComponent"
            :model="model"
            :pageName="pageName">
            <template v-slot:connectButton>
                <a-button
                    @click="openConnectOptionSelection"
                    flaticon
                    :shape="isMobile ? 'circle' : null"
                    icon="fi-rr-plus"
                    type="primary"
                    size="large">   
                    {{ !isMobile ? 'Добавить базу 1С' : '' }}
                </a-button>
            </template>
            <template v-slot:pageFilter>
                <PageFilter 
                    :model="model"
                    :key="pageName"
                    size="large"
                    :page_name="pageName" />
            </template>
        </component>
        <a-modal
            v-model="connectOptionSelectionVisible"
            title="Добавить базу 1С">
            <a-spin
                v-if="!connectOptionsIsLoaded" />
            <a-form-model 
                v-else
                ref="connectionOptionSelect"
                :model="form">
                <a-form-model-item
                    :rules="connectOptionRules"
                    prop="connection_option">
                    <a-radio-group 
                        v-model="form.connection_option"
                        :defaultValue="connectOptions[0].code"
                        class="flex flex-col justify-center">
                        <a-radio 
                            v-for="connectOption in connectOptions"
                            :key="connectOption.id"
                            :value="connectOption.code"
                            class="mb-4 last:mb-0">
                            <span class="text-base">
                                {{ connectOption.name }}
                            </span> 
                        </a-radio>
                    </a-radio-group>
                    <!-- <a-select
                        v-model="form.connection_option"
                        size="large"
                        class="w-full"
                        placeholder="Выбор базы">
                        <a-select-option 
                            v-for="connectOption in connectOptions"
                            :key="connectOption.id"
                            :value="connectOption.code">
                            {{ connectOption.name }}
                        </a-select-option>
                    </a-select> -->
                </a-form-model-item>
            </a-form-model>
            <template slot="footer">
                <a-button
                    @click="confirmConnectOptionSelection"
                    type="primary">
                    Подтвердить
                </a-button>
            </template>
        </a-modal>

    </div>
</template>

<script>
import pageMeta from '@/mixins/pageMeta'
import eventBus from '@/utils/eventBus'

export default {
    mixins: [pageMeta],
    components: {
        PageFilter: () => import('@/components/PageFilter')
    },
    computed: {
        isMobile() {
            return this.$store.state.isMobile
        },
        viewComponent() {
            if(this.isMobile)
                return () => import('./components/ViewList.vue')
            return () => import('./components/ViewTable.vue')
        }
    },
    data() {
        return {
            connectOptionRules: [
                {
                    "required": true,
                    "message": "Обязательно для заполнения",
                    "trigger": "blur"
                }
            ],
            form: {
                connection_option: null
            },
            connectOptionsIsLoaded: false,
            connectOptions: [],
            selectedConnectOption: null,
            connectOptionSelectionVisible: false,
            model: 'tickets.TicketModel',            
            pageName: 'IncomingServiceTicketModel'
        }
    },
    async created() {
        await this.$http('tickets/ticket_type_options/')
            .then(({ data }) => {
                this.connectOptions = data
                this.$store.state.mybases.connectionOptions = data
                this.connectOptionsIsLoaded = true
                this.form.connection_option = this.connectOptions[0].code
            })
            .catch(error => console.log(error))
    },
    methods: {
        openConnectOptionSelection() {
            this.connectOptionSelectionVisible = true
        },
        closeConnectOptionSelection() {
            this.connectOptionSelectionVisible = false
        },
        confirmConnectOptionSelection() {
            this.$refs.connectionOptionSelect.validate(async valid => {
                if(valid) {
                    this.closeConnectOptionSelection()
                    this.openConnectDrawer()
                }
            })
        },
        openConnectDrawer() {
            eventBus.$emit('OPEN_MY_BASES_DRAWER', { form: this.form })
        }
    }
}
</script>

<style scoped>
.wrapper {
    padding: 20px 30px;
    display: flex;
    flex-grow: 1;
}

.mobile_wrapper {
    padding: 15px;
}
</style>
