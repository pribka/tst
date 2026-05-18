<template>
    <a-skeleton v-if="!formIsLoaded || !isAttrsLoaded"/>
    <a-form-model 
        v-else
        :model="form"
        ref="ticketForm"
        :rules="formInfo.rules">
        <a-form-model-item
            v-if="selectedConnectionOption"
            label="База:"
            :label-col="formInfo.config_1c['label-col'] || { span: 6 }"
            :wrapper-col="formInfo.config_1c['wrapper-col'] || { span: 12 }"
            labelAlign="left" 
            ref="config_1c"
            prop="config_1c">
            <a-select
                disabled
                size="large"
                :defaultValue="form.connection_option">
                <a-select-option 
                    :value="form.connection_option">
                    {{ selectedConnectionOption.name }}
                </a-select-option>
            </a-select>
        </a-form-model-item>
        <a-form-model-item
            v-if="formInfo.config_1c"
            :rules="formInfo.config_1c.rules || null"
            :label="formInfo.config_1c.title"
            :label-col="formInfo.config_1c['label-col'] || { span: 6 }"
            :wrapper-col="formInfo.config_1c['wrapper-col'] || { span: 12 }"
            labelAlign="left" 
            ref="config_1c"
            prop="config_1c">
            <a-select
                :disabled="readOnlyMode"
                v-model="form.config_1c"
                size="large"
                :placeholder="formInfo.config_1c.title">
                <a-select-option 
                    v-for="config in ticketConfigs"
                    :key="config.id"
                    :value="config.id">
                    {{ config.name }}
                </a-select-option>
            </a-select>
        </a-form-model-item>
        <a-form-model-item
            v-if="formInfo.tarif"
            :rules="formInfo.tarif.rules || null"
            :label="formInfo.tarif.title"
            :label-col="formInfo.tarif['label-col'] || { span: 6 }"
            :wrapper-col="formInfo.tarif['wrapper-col'] || { span: 12 }"
            labelAlign="left" 
            ref="tarif"
            prop="tarif">
            <a-select
                :disabled="readOnlyMode"
                v-model="form.tarif"
                size="large"
                :placeholder="formInfo.tarif.title">
                <a-select-option 
                    v-for="tariff in ticketTariffs"
                    :key="tariff.id"
                    :value="tariff.id">
                    {{ tariff.name }}
                </a-select-option>
            </a-select>
        </a-form-model-item>
        <a-form-model-item
            v-if="formInfo.user_count"
            :rules="formInfo.user_count.rules || null"
            :label="formInfo.user_count.title"
            :label-col="formInfo.user_count['label-col'] || { span: 6 }"
            :wrapper-col="formInfo.user_count['wrapper-col'] || { span: 12 }"
            labelAlign="left" 
            ref="user_count"
            prop="user_count">
            <a-input-number
                :parser="value => value.replace(/[^0-9.,]/g, '')"
                :disabled="readOnlyMode"
                :min="1" 
                v-model="form.user_count"
                size="large"
                class="w-full"
                :placeholder="formInfo.user_count.title"/>
        </a-form-model-item>
        <a-form-model-item
            v-if="formInfo.phone"
            :rules="formInfo.phone.rules || null"
            :label="formInfo.phone.title"
            :label-col="formInfo.phone['label-col'] || { span: 6 }"
            :wrapper-col="formInfo.phone['wrapper-col'] || { span: 12 }"
            labelAlign="left" 
            ref="phone"
            prop="phone">
            <a-input 
                :disabled="readOnlyMode"
                v-model="form.phone"
                @change="inputPhone"
                size="large"
                :placeholder="formInfo.phone.title"/>
        </a-form-model-item>
        <a-form-model-item
            v-if="formInfo.email"
            :rules="formInfo.email.rules || null"
            :label="formInfo.email.title"
            :label-col="formInfo.email['label-col'] || { span: 6 }"
            :wrapper-col="formInfo.email['wrapper-col'] || { span: 12 }"
            labelAlign="left" 
            ref="email"
            prop="email">
            <a-input 
                :disabled="readOnlyMode"
                v-model="form.email"
                size="large"
                :placeholder="formInfo.email.title"/>
        </a-form-model-item>
        <a-form-model-item
            v-if="formInfo.company"
            :rules="formInfo.company.rules || null"
            :label="formInfo.company.title"
            :label-col="formInfo.company['label-col'] || { span: 6 }"
            :wrapper-col="formInfo.company['wrapper-col'] || { span: 12 }"
            labelAlign="left" 
            ref="company"
            prop="company">
            <a-input 
                :disabled="readOnlyMode"
                v-model="form.company"
                size="large"
                :placeholder="formInfo.company.title"/>
        </a-form-model-item>
        <a-form-model-item
            v-if="formInfo.activity_type"
            :rules="formInfo.activity_type.rules || null"
            :label="formInfo.activity_type.title"
            :label-col="formInfo.activity_type['label-col'] || { span: 6 }"
            :wrapper-col="formInfo.activity_type['wrapper-col'] || { span: 12 }"
            labelAlign="left" 
            ref="activity_type"
            prop="activity_type">
            <a-input 
                :disabled="readOnlyMode"
                v-model="form.activity_type"
                size="large"
                :placeholder="formInfo.activity_type.title"/>
        </a-form-model-item>
        <a-form-model-item
            v-if="formInfo.rental_period"
            :rules="formInfo.rental_period.rules || null"
            :label="formInfo.rental_period.title"
            :label-col="formInfo.rental_period['label-col'] || { span: 6 }"
            :wrapper-col="formInfo.rental_period['wrapper-col'] || { span: 12 }"
            labelAlign="left" 
            ref="rental_period"
            prop="rental_period">
            <a-input 
                :disabled="readOnlyMode"
                v-model="form.rental_period"
                size="large"
                :placeholder="formInfo.rental_period.title"/>
        </a-form-model-item>
        <a-form-model-item
            v-if="formInfo.description"
            :rules="formInfo.description.rules || null"
            :label="formInfo.description.title"
            :label-col="formInfo.description['label-col'] || { span: 6 }"
            :wrapper-col="formInfo.description['wrapper-col'] || { span: 12 }"
            labelAlign="left" 
            ref="description"
            prop="description">
            <a-textarea 
                :disabled="readOnlyMode"
                v-model="form.description"
                class="text-base"
                :placeholder="formInfo.description.title"
                :auto-size="{ minRows: 3, maxRows: 5 }"/>
        </a-form-model-item>
    </a-form-model>
</template>

<script>

export default {
    props: {
        form: {
            type: Object,
            required: true
        },
        formInfo: {
            type: Object,
            required: true    
        },
        isAttrsLoaded: {
            type: Boolean,
            required: true
        },
        mode: {
            type: String,
            default: 'create'
        }
    },
    data() {
        return {
            formIsLoaded: false, 
            ticketConfigs: [],
            ticketTariffs: []
        }
    },
    computed: {
        connectionOptions() {
            return this.$store.state.mybases.connectionOptions
        },
        selectedConnectionOption() {
            return this.connectionOptions.find(option => this.form.connection_option === option.code)
        },
        readOnlyMode() {
            return this.mode === 'readonly'
        }
    },
    async created() {
        try {
            await this.getTicketConfigs()
            await this.getTicketTariff()
            this.formIsLoaded = true
        } catch(error) {
            console.error(error)
        }
        // /tickets/ticket_type_options/
        // tickets/list/
    },
    methods: {
        async getTicketConfigs() {
            await this.$http('tickets/configs_1c/')
                .then(({ data }) => {
                    this.ticketConfigs = data
                })
                .catch(error => console.error(error))
        },
        async getTicketTariff() {
            await this.$http('tickets/tariffs_1c/')
                .then(({ data }) => {
                    this.ticketTariffs = data
                })
                .catch(error => console.error(error))
        },
        // TODO: redo this function
        inputPhone(event) {
            const pattern = /^([+]?[0-9\s-\(\)]?)*$/i
            const value = event.target.value
            const newData = event.data
            if(newData && !newData.match(pattern))
                this.form.phone = value.replace(newData, '')
        }
        
    }
}
</script>