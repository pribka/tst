<template>
    <div>
        <a-modal
            :title="$t('cmd_btn.ask_question_to_tech_support')"
            :visible="issueVisible">
            <a-form-model
                :model="issueForm"
                ref="issueForm"
                :rules="rules">
                <!--<a-form-model-item-->
                <!--name="dealerName"-->
                <!--prop="dealer_name"-->
                <!--:label="$t('cmd_btn.dealer_name')">-->
                <!--<a-input-->
                <!--v-model="issueForm.dealer_name"-->
                <!--size="large"  />-->
                <!--</a-form-model-item>-->
                <!-- <a-form-model-item
                    name="issueName"
                    prop="issue_name"
                    :label="$t('cmd_btn.issue_description')">
                    <a-input
                        v-model="issueForm.issue_name"
                        size="large"  />
                </a-form-model-item> -->
                <a-form-model-item
                    name="userPhone"
                    prop="user_phone"
                    :label="$t('cmd_btn.your_phone')">
                    <a-input
                        v-model="issueForm.user_phone"
                        size="large" />
                </a-form-model-item>

                <a-form-model-item
                    name="issueDescription"
                    prop="issue_description"
                    :label="$t('cmd_btn.issue_description')">
                    <a-textarea
                        v-model="issueForm.issue_description"
                        :auto-size="{ minRows: 2, maxRows: 7 }" />
                </a-form-model-item>

            </a-form-model>
            <template #footer>
                <a-button 
                    key="back" 
                    @click="closeIssueModal">
                    {{$t('cmd_btn.cancel')}}
                </a-button>
                <a-button 
                    key="submit" 
                    type="primary" 
                    :loading="openIssueLoading" 
                    @click="openIssue">
                    {{$t('cmd_btn.create_appeal')}}
                </a-button>
            </template>
        </a-modal>
    </div>
</template>

<script>
import { mapState,mapActions } from 'vuex'

export default {
    data() {
        return {
            openIssueLoading: false,
            issueForm: {
                // issue_name: "",
                issue_description: "",
                dealer_name: "",
                user_phone: ""
            },
            rules: {
                //dealer_name: [
                //    { required: true, message: this.$t('cmd_btn.field_require'), trigger: 'blur' },
                //],
                // issue_name: [
                //     { required: true, message: this.$t('cmd_btn.field_require'), trigger: 'blur' },
                // ],
                issue_description: [
                    { required: true, message: this.$t('cmd_btn.field_require'), trigger: 'blur' },
                ],
                user_phone: [
                    {
                        required: false,
                        pattern: /^(\s*)?(\+)?([- _():=+]?\d[- _():=+]?){3,14}(\s*)?$/,
                        message: this.$t('cmd_btn.invalid_phone_number'),
                        trigger: 'blur'
                    }
                ]
            },
            issueVisible: false,
        }
    },

    computed: {
        ...mapState({
            user: state => state.user.user,
        }),
        userForm() {
            return {
                user_name: this.user.first_name,
                user_email: this.user.email,
                user_phone: this.user.phone || null
            }
        }
    },
    methods: {
        ...mapActions({
            getUserInfo: 'user/getUserInfo',
        }),
        openIssueModal() {
            this.issueForm.user_phone = this.user.phone
            this.issueVisible = true
        },
        closeIssueModal() {
            this.issueVisible = false
        },
        async openIssue() {
            this.$refs.issueForm.validate(async valid =>{
                if(valid){
                    try{
                        this.openIssueLoading = true
                        let res;
                        //this.userForm

                        const issueForm = {
                            ...this.userForm,
                            ...this.issueForm,
                            user_phone: this.issueForm.user_phone
                        }
                        //console.log(issueForm)

                        res = await this.$http.post('crm/bitrix_form/', issueForm)

                        this.$message.success('Ваша заявка отправлена техподдежрке')

                        this.$refs.issueForm.resetFields();
                        this.closeIssueModal()
                        this.getUserInfo()
                    }
                    catch(error){
                        this.$message.error(this.$t('cmd_btn.error'))
                        this.console.error(error)
                    }
                    finally{

                        this.issueForm.user_phone =''
                        this.issueForm.issue_description =''
                        this.openIssueLoading = false
                    }
                } else {
                    this.$message.error(this.$t('cmd_btn.fill_all_fields'))
                }
            })
        },
    },
}
</script>