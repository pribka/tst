<template>
    <div class="wrapper">
        <div v-if="showSocialStatuses" class="social-status">
            <a-form-model-item
                :label="$t('inquiries.social_status')"
                ref="social_status"
                prop="personal_reception.social_status">
                <a-select
                    v-model="form.personal_reception.social_status"
                    size="large"
                    :loading="loading">
                    <a-select-option v-for="option in socialStatuses" :key="option.id" :value="option.code">
                        {{ option.name }}
                    </a-select-option>
                </a-select>
            </a-form-model-item>
        </div>
        <div v-if="showPRStatuses" class="status">
            <a-form-model-item
                ref="status"
                prop="personal_reception.status">
                <a-radio-group
                    v-model="form.personal_reception.status"
                    size="large"
                    button-style="solid" >
                    <a-radio-button
                        v-for="status in PRStatuses"
                        :key="status.id"
                        :value="status.code">
                        {{ status.name }}
                    </a-radio-button>
                </a-radio-group>
            </a-form-model-item>
            
        </div>
    </div>
</template>
<script>
export default {
    name: 'PersonalReception',
    props: {
        categoryDetails: {
            type: Object,
            required: true
        },
        item: {
            type: Object,
            required: true
        },
        form: {
            type: Object,
            required: true
        }
    },
    data() {
        return {
            loading: false,
            socialStatuses: [],
            PRStatuses: []
        }
    },
    computed: {
        showSocialStatuses() {
            return this.socialStatuses.length > 0
        },
        showPRStatuses() {
            return this.PRStatuses.length > 0
        }
    },
    async mounted() {
        this.getSocialStatuses()
        this.getPersonalReceptionStatuses()
    },
    destroyed() {
        this.$emit('deleteExtraKeys', this.item.key)
    },
    methods: {
        async getSocialStatuses() {
            this.loading = true
            try {
                const { data } = await this.$http.get(`/risk_assessment/issue_categories/social_statuses/`)
                if(data) {
                    this.socialStatuses = data
                }
            } catch(e) {
                console.log(e)
            } finally {
                this.loading = false
            }
        },
        async getPersonalReceptionStatuses() {
            this.loading = true
            try {
                const { data } = await this.$http.get(`/risk_assessment/issue_categories/pr_statuses/`)
                if(data) {
                    this.PRStatuses = data
                }
            } catch(e) {
                console.log(e)
            } finally {
                this.loading = false
            }
        }
    }
}
</script>
<style lang="scss" scoped>
.wrapper {
    width: 100%;
    display: flex;
    justify-content: space-between;
    .social-status{
        width: 310px;
    }
    .status{
        margin-top: 26px;
    }
    @media (width < 80rem) {
        flex-direction: column;
        justify-content: unset;
        .social-status{
            width: 100%;
        }
        .status{
            margin-top: 0;
        }
    }
}
</style>