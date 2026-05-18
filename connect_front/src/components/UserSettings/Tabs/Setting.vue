<template>
    <div>
        <div class="setting_block">
            <a-spin class="w-full" size="small" :spinning="loading1">
                <div class="setting_block__head">
                    <div class="setting_block__head--label">{{ $t('Can view my plans') }}:</div>
                </div>
                <div>
                    <a-form-model
                        ref="ruleForm1"
                        :model="form1">
                        <a-form-model-item ref="organizations" :label="$t('Organizations')" prop="organizations" class="mb-2">
                            <OrganizationsDrawer
                                v-model="form1.organizations"
                                :title="$t('Select organization')" />
                        </a-form-model-item>
                        <a-form-model-item ref="users" :label="$t('Users from the list')" prop="users" class="w-full mb-0">
                            <UserDrawer
                                key="form1"
                                v-model="form1.users"
                                :metadata="{ key: 'users', value: form1.metadata }"
                                :changeMetadata="changeMetadata(form1)"
                                id="empty_task"
                                class="users_select"
                                :oldSelected="false"
                                moreTag
                                multiple
                                :title="$t('Select users')" />
                        </a-form-model-item>
                    </a-form-model>
                    <a-button 
                        type="primary" 
                        :loading="form1Loading"
                        :disabled="form1Disabled"
                        class="mt-3 px-6"
                        :block="isMobile"
                        @click="form1Submit()">
                        {{ $t('Save') }}
                    </a-button>
                </div>
            </a-spin>
        </div>
        <div class="setting_block">
            <a-spin class="w-full" size="small" :spinning="loading2">
                <div class="setting_block__head">
                    <div class="setting_block__head--label">{{ $t('Can view my event calendar') }}:</div>
                </div>
                <div>
                    <a-form-model
                        ref="ruleForm2"
                        :model="form1">
                        <a-form-model-item ref="organizations" :label="$t('Organizations')" prop="organizations" class="mb-2">
                            <OrganizationsDrawer
                                v-model="form2.organizations"
                                :title="$t('Select organization')" />
                        </a-form-model-item>
                        <a-form-model-item ref="users" :label="$t('Users from the list')" prop="users" class="w-full mb-0">
                            <UserDrawer
                                key="form2"
                                v-model="form2.users"
                                :metadata="{ key: 'users', value: form2.metadata }"
                                :changeMetadata="changeMetadata(form2)"
                                id="empty_task"
                                class="users_select"
                                :oldSelected="false"
                                moreTag
                                multiple
                                :title="$t('Select users')" />
                        </a-form-model-item>
                    </a-form-model>
                    <a-button 
                        type="primary" 
                        :loading="form2Loading"
                        :disabled="form2Disabled"
                        class="mt-3 px-6"
                        :block="isMobile"
                        @click="form2Submit()">
                        {{ $t('Save') }}
                    </a-button>
                </div>
            </a-spin>
        </div>
    </div>
</template>

<script>
import Vue from 'vue'
export default {
    components: {
        OrganizationsDrawer: () => import('../components/OrganizationsDrawer.vue'),
        UserDrawer: () => import("@apps/DrawerSelect/index.vue")
    },
    computed: {
        isMobile() { 
            return this.$store.state.isMobile
        },
        form1Disabled() {
            return this.form1.organizations.length || this.form1.users.length ? false : true
        },
        form2Disabled() {
            return this.form2.organizations.length || this.form2.users.length ? false : true
        }
    },
    data() {
        return {
            form1Loading: false,
            form2Loading: false,
            loading1: false,
            loading2: false,
            form1: {
                organizations: [],
                users: [],
                metadata: {}
            },
            form2: {
                organizations: [],
                users: [],
                metadata: {}
            }
        }
    },
    created() {
        this.getPlans()
        this.getCalendar()
    },
    methods: {
        changeMetadata(form) {
            return ({ key, value }) => {
                Vue.set(form.metadata, key, value);
            }
        },

        async form1Submit() {
            try {
                this.form1Loading = true
                const queryData = {...this.form1}
                if(queryData.organizations.length)
                    queryData.organizations = queryData.organizations.map(item => item.id)
                if(queryData.users.length)
                    queryData.users = queryData.users.map(item => item.id)
                const { data } = await this.$http.put('/personal_planes/access/update/', queryData)
                if(data) {
                    this.$message.success(this.$t('Changes saved'))
                }
            } catch(e) {
                this.$message.error(this.$t('Error'))
                console.log(e)
            } finally {
                this.form1Loading = false
            }
        },
        async form2Submit() {
            try {
                this.form2Loading = true
                const queryData = {...this.form2}
                if(queryData.organizations.length)
                    queryData.organizations = queryData.organizations.map(item => item.id)
                if(queryData.users.length)
                    queryData.users = queryData.users.map(item => item.id)
                const { data } = await this.$http.put('/calendars/access/update/', queryData)
                if(data) {
                    this.$message.success(this.$t('Changes saved'))
                }
            } catch(e) {
                this.$message.error(this.$t('Error'))
                console.log(e)
            } finally {
                this.form2Loading = false
            }
        },
        async getPlans() {
            try {
                this.loading1 = true
                const { data } = await this.$http.get('/personal_planes/access/')
                if(data) {
                    this.form1 = data
                }
            } catch(e) {
                console.log(e)
            } finally {
                this.loading1 = false
            }
        },
        async getCalendar() {
            try {
                this.loading2 = true
                const { data } = await this.$http.get('/calendars/access/')
                if(data) {
                    this.form2 = data
                }
            } catch(e) {
                console.log(e)
            } finally {
                this.loading2 = false
            }
        }
    }
}
</script>

<style lang="scss" scoped>
.users_select{
    &::v-deep{
        .user_draw_input{
            min-height: 40px;
            height: auto;
        }
    }
}
.setting_block{
    border: 1px solid #D9D9D9;
    border-radius: 8px;
    padding: 20px;
    color: #000;
    margin-bottom: 20px;
    &__head{
        padding-bottom: 15px;
        display: flex;
        align-items: center;
        &--label{
            font-size: 16px;
        }
    }
}
</style>