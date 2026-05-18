<template>
    <div 
        v-if="orderForm.aside && orderForm.aside.offer && orderForm.aside.offer.show" 
        class="offer_block mt-5">
        <h2>
            {{ orderForm.aside.offer.label }}
        </h2>
        <a-button 
            block 
            :type="orderForm.aside.offer.type" 
            :ghost="orderForm.aside.offer.ghost"
            :loading="offerLoader"
            class="offer_btn"
            :size="orderForm.aside.offer.size"
            @click="visible = true">
            {{ orderForm.aside.offer.btnText }}
        </a-button>

        <a-modal
            title="Коммерческое предложение"
            :visible="visible"
            :width="360"
            :footer="false"
            :afterClose="afterClose"
            @cancel="visible = false">
            <template v-if="sendEmail">
                <a-form-model
                    ref="emailForm"
                    :model="formState"
                    :rules="rules">
                    <a-form-model-item 
                        label="Отправить на почту" 
                        prop="to_email">
                        <a-input 
                            v-model="formState.to_email"
                            size="large"
                            placeholder="Введите E-mail"
                            type="email" />
                    </a-form-model-item>
                    <a-button 
                        size="large"
                        type="primary"
                        class="uppercase font-light"
                        :loading="offerLoader"
                        @click="emailSend()">
                        Отправить
                    </a-button>
                </a-form-model>
            </template>
            <template v-else>
                <a-button 
                    ghost 
                    type="primary" 
                    block
                    class="mb-3 uppercase font-light"
                    size="large"
                    :loading="offerLoader"
                    @click="offerGenerated()">
                    Сохранить в PDF
                </a-button>
                <a-button 
                    ghost 
                    type="primary" 
                    block
                    class="uppercase font-light"
                    size="large"
                    @click="sendEmail = true">
                    Отправить на почту
                </a-button>
            </template>
        </a-modal>
    </div>
</template>

<script>
import { mapState } from 'vuex'
export default {
    props: {
        orderForm: {
            type: Object,
            required: true
        },
        form: {
            type: Object,
            required: true
        }
    },
    computed: {
        ...mapState({
            user: state => state.user.user
        })
    },
    data() {
        return {
            offerLoader: false,
            visible: false,
            sendEmail: false,
            formState: {
                to_email: ''
            },
            rules: {
                to_email: [
                    { required: true, message: 'Заполните E-mail адрес', type: 'email' },
                ]
            }
        }
    },
    watch: {
        visible(val) {
            if(val) {
                if(this.user?.email)
                    this.formState.to_email = JSON.parse(JSON.stringify(this.user.email))
            }
        }
    },
    methods: {
        afterClose() {
            this.close()
        },
        close() {
            this.sendEmail = false
            this.formState = {
                to_email: ''
            }
        },
        emailSend() {
            this.$refs.emailForm.validate(async valid => {
                if (valid) {
                    try {
                        this.offerLoader = true
                        const { data } = await this.$http.post('/crm/return/create_offer/', {
                            ...this.form,
                            ...this.formState
                        })
                        if(data && data === 'ok') {
                            this.$message.info('Коммерческое предложение отправлено на указанный вами E-mail')
                            this.visible = false
                        }
                    } catch(e) {
                        console.log(e)
                    } finally {
                        this.offerLoader = false
                    }
                } else {
                    console.log('error submit!!');
                    return false;
                }
            })
        },
        async offerGenerated() {
            try {
                this.offerLoader = true
                const { data } = await this.$http.post('/crm/returns/create_offer/', this.form)
                if(data) {
                    const blob=new Blob([data])
                    const link=document.createElement('a')
                    link.href=window.URL.createObjectURL(blob)
                    link.download=`Коммерческое предложение ${this.$moment().format('DD.MM.YYYY')}.pdf`
                    link.click()
                    this.visible = false
                }
            } catch(e) {
                console.log(e)
            } finally {
                this.offerLoader = false
            }
        },
    }
}
</script>

<style lang="scss" scoped>
.offer_block{
    h2{
        font-size: 17px;
        margin-bottom: 10px;
    }
    .offer_btn{
        font-weight: 300;
        text-transform: uppercase;
    }
}
</style>