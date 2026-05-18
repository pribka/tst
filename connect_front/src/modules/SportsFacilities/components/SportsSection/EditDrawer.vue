<template>
    <a-drawer
        :title="$t('sports.sectionCount')"
        placement="right"
        :visible="visible"
        :width="drawerWidth"
        :after-visible-change="afterVisibleChange"
        @close="visible = false">
        <a-spin 
            :spinning="infoLoading" 
            size="small">
            <a-form-model
                ref="formRef"
                :model="form">
                <div class="grid gap-4 grid-cols-1 md:grid-cols-2">
                    <a-form-model-item 
                        v-for="item in fornInfo"
                        :key="item.sport_group_type.id"
                        :ref="item.sport_group_type.id" 
                        :rules="{ required: true, message: $t('sports.formError'), trigger: 'blur' }"
                        :label="item.sport_group_type.name" 
                        :prop="item.sport_group_type.id">
                        <a-input-number 
                            v-model="form[item.sport_group_type.id]" 
                            :min="0" 
                            :placeholder="item.sport_group_type.name" 
                            size="large"
                            :disabled="!checkEdit"
                            class="w-full"
                            @keypress="handleKeyPress" />
                    </a-form-model-item>
                    <a-form-model-item 
                        v-if="checkEdit" 
                        class="item_btn">
                        <a-button 
                            type="primary" 
                            size="large" 
                            :loading="formLoading"
                            block
                            @click="formSubmit()">
                            {{ $t('sports.save') }}
                        </a-button>
                    </a-form-model-item>
                </div>
            </a-form-model>
        </a-spin>
    </a-drawer>
</template>

<script>
import eventBus from '@/utils/eventBus'
import { mapState } from 'vuex'
import { handleKeyPress } from '../../utils.js'
export default {
    computed: {
        ...mapState({
            windowWidth: state => state.windowWidth,
            actions: state => state.facilities.projectActions
        }),
        isMobile() {
            return this.$store.state.isMobile
        },
        drawerWidth() {
            if(this.windowWidth > 844)
                return 844
            else {
                return '100%'
            }
        },
        checkEdit() {
            return this.actions?.sections_edit?.availability
        }
    },
    data() {
        return {
            visible: false,
            infoLoading: false,
            formLoading: false,
            fornInfo: [],
            form: {}
        }
    },
    methods: {
        handleKeyPress,
        formSubmit() {
            this.$refs.formRef.validate(async valid => {
                if (valid) {
                    try {
                        this.formLoading = true
                        const queryData = {
                            id: this.form.id,
                            sport_groups: []
                        }
                        for(const key in this.form) {
                            if(key !== 'id') {
                                queryData.sport_groups.push({
                                    sport_group_type: key,
                                    sections_quantity: this.form[key]
                                })
                            }
                        }
                        const { data } = await this.$http.post(`/sports_facilities/${this.$route.params.id}/section/groups/update/`, queryData)
                        if(data) {
                            this.visible = false
                            this.$message.success(this.$t('sports.sectionEditSuccess'))
                            eventBus.$emit('sectionListUpdate')
                        }
                    } catch(e) {
                        console.log(e)
                        this.$message.error(this.$t('sports.error'))
                    } finally {
                        this.formLoading = false
                    }
                } else
                    return false
            })
        },
        afterVisibleChange(vis) {
            if(!vis) {
                this.edit = false
                this.fornInfo = []
                this.form = {}
            }
        },
        async getInfo() {
            try {
                this.infoLoading = true
                const { data } = await this.$http.get(`/sports_facilities/${this.$route.params.id}/section/groups/`, {
                    params: {
                        id: this.form.id
                    }
                })
                if(data) {
                    this.fornInfo = data
                    data.forEach(item => {
                        this.$set(this.form, item.sport_group_type.id, item.sections_quantity || null)
                    })
                }
            } catch(e) {
                console.log(e)
            } finally {
                this.infoLoading = false
            }
        }
    },
    mounted() {
        eventBus.$on('openSectionInformationDrawer', ({id}) => {
            this.form = {
                id
            }
            this.visible = true
            this.getInfo()
        })
    },
    beforeDestroy() {
        eventBus.$off('openSectionInformationDrawer')
    }
}
</script>

<style lang="scss" scoped>
.item_btn{
    display: flex;
    width: 100%;
    align-items: flex-end;
    &::v-deep{
        .ant-col{
            width: 100%;
        }
    }
}
</style>