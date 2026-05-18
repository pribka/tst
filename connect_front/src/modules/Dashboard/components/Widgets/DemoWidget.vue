<template>
    <WidgetWrapper :widget="widget" :class="isMobile && 'mobile_widget'" cardColor="#fef8eb">
        <div class="widget_grid">
            <div class="widget_grid__item">
                <p>{{ $t('dashboard.demo.text1') }}</p>
                <div class="mt-4">
                    <a-button type="primary" class="wid_btn" @click="visible = true">
                        {{ $t('dashboard.demo.text2') }}
                    </a-button>
                </div>
            </div>
            <div class="widget_grid__item last_item">
                <div class="img_wrapper">
                    <img :data-src="'/img/banner_img.jpg'" class="lazyload" />
                </div>
            </div>
        </div>

        <a-modal
            v-model="visible"
            :title="$t('dashboard.demo.text2')"
            :footer="false"
            @afterVisibleChange="afterVisibleChange"
            @cancel="closeModal()"
            destroyOnClose>
            
            <p>{{ $t('dashboard.demo.text3') }}</p>

            <a-form-model ref="ruleForm" :model="form" :rules="rules">
                
                <a-form-model-item ref="name" :label="$t('dashboard.demo.text4')" prop="name">
                    <a-input
                        v-model="form.name"
                        size="large"
                        :placeholder="$t('dashboard.demo.text5')"
                        @pressEnter="formSubmit()" />
                </a-form-model-item>

                <a-form-model-item ref="email" :label="$t('dashboard.demo.text6')" prop="email">
                    <a-input
                        v-model="form.email"
                        size="large"
                        :placeholder="$t('dashboard.demo.text7')"
                        @pressEnter="formSubmit()" />
                </a-form-model-item>

                <a-form-model-item ref="phone" :label="$t('dashboard.demo.text8')" prop="phone">
                    <a-input
                        v-model="form.phone"
                        v-imask="'+{7} (000) 000-00-00'"
                        size="large"
                        :maxLength="18"
                        class="phone_mask"
                        :placeholder="$t('dashboard.demo.text9')"
                        @pressEnter="formSubmit()" />
                </a-form-model-item>

                <a-button
                    type="primary"
                    class="mb-3"
                    style="height: 40px;"
                    block
                    size="large"
                    :loading="loading"
                    @click="formSubmit()">
                    {{ $t('dashboard.demo.text10') }}
                </a-button>
            </a-form-model>
        </a-modal>
    </WidgetWrapper>
</template>

<script>
import { mapState } from 'vuex'
import IMask from 'imask'
import { errorHandler } from '@/utils/index.js'
export default {
    components: { 
        WidgetWrapper: () => import('../WidgetWrapper.vue')
    },
    directives: {
        imask: {
            inserted(el, binding, vnode) {
                const root = el.nodeType === 1 ? el : vnode.elm
                const input = root && (root.tagName === 'INPUT' ? root : root.querySelector('input'))
                if (!input) return
                const options = typeof binding.value === 'string' ? { mask: binding.value } : binding.value || {}
                const instance = IMask(input, Object.assign({ overwrite: true }, options))
                instance.on('accept', () => {
                    input.value = instance.value
                    const evt = new Event('input', { bubbles: true })
                    input.dispatchEvent(evt)
                })
                root._imask = instance
            },
            componentUpdated(el, binding, vnode) {
                const root = el.nodeType === 1 ? el : vnode.elm
                const instance = root && root._imask
                if (!instance) return
                const options = typeof binding.value === 'string' ? { mask: binding.value } : binding.value || {}
                instance.updateOptions(Object.assign({ overwrite: true }, options))
                const input = root.querySelector('input') || root
                if (input && input.value !== instance.value) instance.value = input.value
            },
            unbind(el, binding, vnode) {
                const root = el.nodeType === 1 ? el : vnode.elm
                if (root && root._imask) {
                    root._imask.destroy()
                    root._imask = null
                }
            }
        }
    },
    props: {
        widget: { type: Object, required: true }
    },
    computed: {
        ...mapState({ user: state => state.user.user }),
        isMobile() { return this.$store.state.isMobile }
    },
    data() {
        return {
            visible: false,
            loading: false,
            rules: {
                name: [{ required: true, message: this.$t('field_required'), trigger: 'blur' }],
                email: [
                    { required: true, message: this.$t('field_required'), trigger: 'blur' },
                    { type: 'email', message: this.$t('auth.email_reg_error'), trigger: 'blur' }
                ]
            },
            form: {
                name: '',
                email: '',
                phone: '',
                request_type: 'request_demonstration'
            }
        }
    },
    methods: {
        afterVisibleChange(vis) {
            if (vis) {
                if (this.user) {
                    if (this.user.email) this.form.email = this.user.email
                    const fio = [this.user.last_name, this.user.first_name].filter(Boolean).join(' ')
                    if (fio) this.form.name = fio
                    if (this.user.phone) this.form.phone = this.user.phone
                }
            } else
                this.form = { name: '', email: '', phone: '', request_type: 'request_demonstration' }
        },
        closeModal() {
            this.visible = false
        },
        formSubmit() {
            this.$refs.ruleForm.validate(async valid => {
                if (!valid) return false
                try {
                    this.loading = true
                    const queryData = { ...this.form }
                    if (!queryData.phone) delete queryData.phone
                    const { data } = await this.$http.post('/users/leave_request/', queryData)
                    if (data) {
                        this.visible = false
                        this.$message.info(this.$t('dashboard.demo.text11'))
                    }
                } catch (error) {
                    errorHandler({error})
                } finally {
                    this.loading = false
                }
            })
        }
    }
}
</script>

<style lang="scss" scoped>
p{
  font-size: 14px;
  line-height: 20px;
  &:not(:last-child){ margin-bottom: 10px; }
}
.last_item{
  display: none;
  @media (min-width: 1600px) { display: block; }
}
.widget_grid{
  overflow-y: auto;
  height: 100%;
  color: #888888;
  display: grid;
  grid-template-columns: 1fr;
  @media (min-width: 1600px) {
    gap: 50px;
    grid-template-columns: 1fr 86px;
    padding-top: 20px;
  }
  .img_wrapper{
    width: 86px;
    height: 86px;
    border-radius: 50%;
    overflow: hidden;
    display: none;
    @media (min-width: 1600px) { display: block; }
    img{ object-fit: cover; }
  }
  .wid_btn{
    background: #ff9a01!important;
    border-color: #ff9a01!important;
    color: #2D2D2D!important;
    &:hover{ opacity: 0.7; }
  }
}
</style>