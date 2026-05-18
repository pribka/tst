<template>
    <div class="form">
        <div class="revoked-without-routing">
            <div class="label ant-form-item-required">
                {{ $t('Revoked without routing') }}
            </div>
            <div class="input">
                <a-form-model-item
                    ref="revoked_without_routing"
                    prop="revoked_without_routing">
                    <a-input-number
                        v-model="form.revoked_without_routing"
                        :disabled="inputDisabled"
                        :formatter="value => `$ ${value}`.replace(/\D/g, '')" />
                </a-form-model-item>
            </div>
        </div>

        <div class="transferring-to-another-system">
            <div class="label ant-form-item-required">
                {{ $t('Transfer to another system') }}
            </div>
            <div class="input">
                <a-form-model-item
                    ref="transferring_to_another_system"
                    prop="transferring_to_another_system">
                    <a-input-number
                        v-model="form.transferring_to_another_system"
                        :disabled="inputDisabled"
                        :formatter="value => `$ ${value}`.replace(/\D/g, '')" />
                </a-form-model-item>
            </div>
        </div>
    </div>
</template>
<script>
export default {
    name: 'F2GOFile',
    props: {
        file: {
            type: Object,
            required: true
        },
        form: {
            type: Object,
            required: true
        },
        formSubmit: {
            type: Boolean,
            default: false
        },

    },
    computed: {
        inputDisabled() {
            return this.formSubmit 
        }
    }
}
</script>
<style lang="scss" scoped>
.form{
    .revoked-without-routing, .transferring-to-another-system{
        width: 90%;
        display: grid;
        grid-template-columns: auto 130px;
        column-gap: 30px;
        line-height: normal;
        &::v-deep{
            .ant-input-number .ant-input-number-handler-wrap {
                display: none;
            }
            .ant-input-number{
                width: 100%;
            }
            .ant-input-number-input {
                text-align: right;
            }
        }
    }
    .revoked-without-routing{
        padding-top: 32px;
    }
    @media (max-width: 600px) {
        .revoked-without-routing, .transferring-to-another-system{
            width: 100%;
        }
    }
}
</style>