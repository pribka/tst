<template>
    <DrawerTemplate
        :title="$t('team.invite_user')"
        v-model="visible"
        class="invite_drawer"
        @close="visible = false"
        destroyOnClose
        :zIndex="zIndex"
        :width="drawerWidth"
        @afterVisibleChange="afterVisibleChange"
        placement="right">
        <div class="drawer_body">
            <div>
                <component 
                    :is="inviteWidget" 
                    :orgId="orgId" 
                    :organizationId="orgId" 
                    :form="form"
                    ref="inviteComponent" />
            </div>
            <!-- <div v-if="isMobile" class="mt-3">
                <a-button v-if="inviteType === 3" type="ui" block class="mb-2" size="large" :loading="linkLoader" @click="updateLink()">
                    Обновить ссылку
                </a-button>
                <a-button v-if="inviteType !== 2" type="ui" block class="mb-2" size="large" @click="inviteType = 2">
                    Пригласить массово
                </a-button>
                <a-button v-if="inviteType !== 3" type="ui" block class="mb-2" size="large" @click="inviteType = 3">
                    Пригласить по ссылке
                </a-button>
            </div> -->
        </div>
        <template #footer>
            <div class="flex items-center">
                <a-button 
                    v-if="inviteType === 'email'"
                    :loading="loading" 
                    @click="formSubmit()"
                    type="primary">
                    {{ $t('team.send') }}
                </a-button>
                <a-button 
                    @click="visible = false"
                    ghost
                    class="ml-1"
                    type="ui">
                    {{ $t('team.cancel') }}
                </a-button>
            </div>
        </template>
    </DrawerTemplate>
</template> 

<script>
import eventBus from '@/utils/eventBus'
export default {
    name: "OrganizationAddUserDrawer",
    components: {
        DrawerTemplate: () => import('@/components/DrawerTemplate.vue')
    },
    props: {
        zIndex: {
            type: Number,
            default: 1010
        }
    },
    computed: {
        windowWidth() {
            return this.$store.state.windowWidth
        },
        isMobile() {
            return this.$store.state.isMobile
        },
        drawerWidth() {
            if(this.windowWidth > 900)
                return 900
            else {
                return '100%'
            }
        },
        inviteWidget() {
            if(this.inviteType === 'link')
                return () => import('./InvileLink.vue')
            // if(this.inviteType === 'email')
            return () => import('./InviteByEmail')
            // return () => import('./MassiveInvite.vue')
        },
        hasData() {
            return Boolean(this.form.massive || this.form.list?.[0]?.email)
        }
    },
    data() {
        return {
            visible: false,
            loading: false,
            orgId: null,
            inviteType: 'email',
            linkLoader: false,
            isDepartment: false,
            form: {
                list: [
                    {
                        key: Date.now(),
                        email: '',
                        workgroup: null
                    }
                ],
                massive: '',
                workgroup: null
            }
        }
    },
    created() {
        eventBus.$on('open_invite', ({ 
            organizationId, 
            inviteType='email',
            isDepartment=false 
        }) => {
            this.visible = true
            this.inviteType = inviteType
            this.orgId = organizationId
            this.isDepartment = isDepartment
        })
    },
    methods: {
        // async updateLink() {
        //     try {
        //         const deactivate_at = this.$refs['formCheck'].deactivate_at || null
        //         this.linkLoader = true
        //         const { data } = await this.$http.post(`/users/my_organizations/${this.orgId}/invite/`, {
        //             deactivate_at
        //         })
        //         if(data?.invite) {
        //             this.$nextTick(async () => {
        //                 this.$refs['formCheck'].updateLink(data)
        //             })
        //         }
        //     } catch(e) {
        //         console.log(e)
        //     } finally {
        //         this.linkLoader = false
        //     }
        // },
        addRow() {
            this.$nextTick(async () => {
                try {
                    this.$refs['formCheck'].addEmail()
                } catch(e) {
                    console.log(e)
                }
            })
        },
        afterVisibleChange(vis) {
            if(!vis) {
                this.inviteType = 1
                this.orgId = null
            }
        },
        formSubmit() {
            this.$nextTick(async () => {
                try {
                    const emailForm = this.$refs['inviteComponent']
                        .$refs['emailInvite']
                        .$refs['inviteForm']
                    const massiveInvite = this.$refs['inviteComponent']
                        .$refs['massiveInvite']
                    const emailValid = await emailForm.validate()
                    const massiveEmailValid = await massiveInvite.$refs['inviteForm'].validate()
                    if(emailValid && massiveEmailValid) {
                        this.loading = true
                        const formData = this.form
                        let emailArray = []

                        // массово
                        massiveInvite.setError(false)
                        if(this.form.massive) {
                            if(formData.massive.includes(',')) {
                                emailArray = formData.massive.split(',')
                            } else {
                                emailArray = formData.massive.split(' ')
                            }
                            if(emailArray.length) {
                                let error = []
                                const regex = /^([a-zA-Z0-9_\.\-])+\@(([a-zA-Z0-9\-])+\.)+([a-zA-Z0-9]{2,4})|([0-9]{10})+$/;
                                emailArray = emailArray.map((item, index) => {
                                    if(!regex.test(item.trim())) {
                                        error.push(index)
                                    }
                                    return {
                                        email: item.trim(),
                                        workgroup: formData.workgroup
                                    }
                                })
                                if(error.length) {
                                    massiveInvite.setError(true)
                                    console.log(error, massiveInvite.setError)
                                }
                            }
                        }
                        // не массово
                        if(formData.list?.[0]?.email) {
                            const emailList = formData.list.map(item => {
                                return {
                                    email: item.email.trim(),
                                    workgroup: item.workgroup ? item.workgroup.id : null
                                }
                            })
                            emailArray.push(...emailList)
                        }
                        const { data } = await this.$http.post(`/users/my_organizations/${this.orgId}/email_invite/`, emailArray)
                        if(data === 'ok') {
                            this.form = {
                                list: [
                                    {
                                        key: Date.now(),
                                        email: '',
                                        workgroup: null
                                    }
                                ],
                                massive: '',
                                workgroup: null
                            }
                            this.$message.info(this.$t('team.invitations_sent'))
                            massiveInvite.resetData()
                        }
                    }
                } catch(e) {
                    console.log(e)
                } finally {
                    this.loading = false
                }
            })
        },
        // async sendMassiveEmail() {
        //     const massiveInvite = this.$refs['inviteComponent']
        //         .$refs['massiveInvite']
        //     const massiveForm = massiveInvite.$refs['inviteForm']
        //     const valid = await emailForm.validate()
        //     if(valid) {

        //     }

        // }

    },
    beforeDestroy() {
        eventBus.$off('open_invite')
    }
}
</script>