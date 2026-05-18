<template>
    <DrawerTemplate
        :title="isSubdivision ? $t('team.invite_suborganization') : $t('team.invite_organization')"
        v-model="visible"
        class="org_invite_drawer"
        @close="visible = false"
        destroyOnClose
        :zIndex="zIndex"
        @afterVisibleChange="afterVisibleChange"
        :width="drawerWidth"
        placement="right">
        <div class="drawer_body">
            <component 
                v-if="visibleCheck" 
                :is="inviteWidget" 
                ref="inviteType"
                :setSelected="setSelected"
                :selected="selected" />
        </div>
        <template #footer>
            <div class="flex items-center">
                <template v-if="type === 1">
                    <a-button 
                        v-if="isSubdivision"
                        :disabled="selected.length ? false : true"
                        type="primary"
                        :block="isMobile ? true : false"
                        :loading="loading"
                        @click="inviteAsSubdivision">
                        {{ $t('team.invite') }}
                    </a-button>
                    <a-button 
                        v-else
                        :disabled="selected.length ? false : true"
                        type="primary"
                        :block="isMobile ? true : false"
                        :loading="loading"
                        @click="inviteSubmit()">
                        {{ $t('team.invite') }}
                    </a-button>
                    <!-- <a-button 
                        type="link" 
                        @click="type = 2">
                        {{ $t('team.get_link') }}
                    </a-button> -->
                </template>
                <template v-if="type === 2">
                    <a-button 
                        type="link" 
                        @click="type = 1">
                        {{ $t('team.search_organization') }}
                    </a-button>
                </template>
            </div>
        </template>
        <a-modal
            :title="$t('team.invited_organization_is')"
            :zIndex="1500"
            :footer="null"
            destroyOnClose
            :visible="visibleType"
            @cancel="visibleType = false">
            <div class="type_list mb-5">
                <div 
                    v-for="item in listType" 
                    :key="item.id" 
                    class="item select-none" 
                    :class="selectType && selectType === item.code && 'selected'" 
                    @click="selectedType(item.code)">
                    {{ item.name }}
                </div>
            </div>
            <a-button 
                size="large" 
                type="primary" 
                block 
                :disabled="selectType ? false : true"
                :loading="inviteLoading" 
                @click="sendOrgInvite()">
                {{ $t('team.send_invitation') }}
            </a-button>
        </a-modal>
    </DrawerTemplate>
</template>

<script>
import eventBus from '@/utils/eventBus'
let timer;
export default {
    name: "OrganizationInviteDrawer",
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
        isMobile() {
            return this.$store.state.isMobile
        },
        inviteWidget() {
            if(this.type === 1)
                return () => import('./Search.vue')
            if(this.type === 2)
                return () => import('./Link.vue')

            return () => import('./Search.vue')
        },
        windowWidth() {
            return this.$store.state.windowWidth
        },
        drawerWidth() {
            if(this.type === 1) {
                if(this.windowWidth > 600)
                    return 600
                else {
                    return '100%'
                }
            } else {
                if(this.windowWidth > 700)
                    return 700
                else {
                    return '100%'
                }
            }
        }
    },
    created() {
        eventBus.$on('invite_organization', ({ organization, isSubdivision = false})  => {
            this.visible = true
            this.visibleCheck = true
            this.org = organization,
            this.isSubdivision = isSubdivision
        })
    },
    data() {
        return {
            visible: false,
            type: 1,
            visibleCheck: true,
            selected: '',
            loading: false,
            visibleType: false,
            listType: [],
            selectType: null,
            inviteLoading: false,
            org: null,
            isSubdivision: false
        }
    },
    methods: {
        async sendOrgInvite() {
            try {
                this.inviteLoading = true
                const queryData = {
                    contractor_parent: this.org.id,
                    contractor: this.selected,
                    contractor_owner: this.org.id,
                    relation_type: this.selectType
                }
                const { data } = await this.$http.post('/contractor_invites/create/', queryData)
                if(data) {
                    this.visibleType = false
                    this.visible = false
                    this.$message.info(this.$t('team.invitation_sent_successfully'), 4)
                }
            } catch(e) {
                console.log(e)
                this.$message.error(this.$t('team.error'))
            } finally {
                this.inviteLoading = false
            }
        },
        selectedType(code) {
            this.selectType = code
        },
        async inviteSubmit() {
            try {
                this.loading = true
                const { data } = await this.$http.get('/catalogs/contractor_relation_types/', {
                    params: {
                        page_size: 'all'
                    }
                })
                if(data?.results?.length) {
                    this.listType = data.results
                    this.visibleType = true
                    this.selectType = data.results[0].code
                }
            } catch(e) {
                console.log(e)
            } finally {
                this.loading = false
            }
        },
        setSelected(value) {
            this.selected = value
        },
        afterVisibleChange(vis) {
            if(!vis) {
                this.selectType = null
                this.visibleCheck = false
                this.org = null,
                this.isSubdivision = false
            }
        },
        inviteAsSubdivision() {
            this.selectedType('structural_division')
            this.sendOrgInvite()               
        }
    },
    beforeDestroy() {
        eventBus.$off('invite_organization')
    }
}
</script>

<style lang="scss" scoped>
.type_list{
    .item{
        border: 1px solid #e8e8e8;
        cursor: pointer;
        border-radius: var(--borderRadius);
        padding: 15px;
        &.selected{
            background: var(--primaryHover);
            color: var(--blue);
        }
        &:not(:last-child){
            margin-bottom: 10px;
        }
    }
}
</style>