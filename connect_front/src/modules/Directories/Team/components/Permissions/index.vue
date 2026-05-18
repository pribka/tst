<template>
    <component 
        :is="widget"
        :organization="organization"/>
    
</template>

<script>
import "ag-grid-community/styles/ag-grid.css";
import "ag-grid-community/styles/ag-theme-balham.css";
import "ag-grid-community/styles/ag-theme-alpine.css";
import { AgGridVue } from "ag-grid-vue";
import { mapState } from 'vuex';
export default {
    name: 'ThePermissions',
    components: {
        AgGridVue,
        RoleDetailDrawer: () => import("./RoleDetailDrawer"),
        // CreateRoleDrawer,
        /* eslint-disable */ 
        TableActions: () => import('./TableActions'),
        Members: () => import('./Members')
         /* eslint-enable */ 

    },
    props: {
        organization: {
            type: Object,
            required: true
        },
    },
    data() {
        return { 
            page: 1,
            pageSize: 15,
            pageSizeOptions: ['15', '30', '50'],
            sort: '',
            count: 0,
            pageName: 'role_list',
            
            columnDefs: [
                {
                    resizable: true,
                    headerName: this.$t('team.column_name'),
                    field: 'name',
                    cellStyle: {
                        height: '100%',
                        display: 'flex',
                        alignItems: 'center'
                    },

                },
                {
                    resizable: true,
                    headerName: this.$t('team.column_rights'),
                    width: 200,

                    autoHeight: true,
                    wrapText: true,
                    cellStyle: {
                        wordBreak: 'normal',
                        padding: '5px 0',
                        lineHeight: '1.4rem',
                        height: '100%',
                        display: 'flex',
                        alignItems: 'center'
                    },
                    field: 'permission_types',
                    cellRenderer: params => { 
                        const permissions = params.value
                        for(let i = 1; i < permissions.length; i++) {
                            permissions[i] = permissions[i].toLowerCase()
                        }
                        return permissions.join(', ') 
                    }
                },
                {
                    resizable: true,
                    headerName: this.$t('team.column_users'),
                    field: 'users',
                    cellRenderer: 'Members',
                },
                {
                    resizable: true,
                    cellStyle: {
                        height: '100%',
                        display: 'flex',
                        alignItems: 'center'
                    },
                    headerName: '',
                    field: 'actions',
                    cellRenderer: 'TableActions',
                    cellRendererParams: {
                        openEditRoleDrawer: this.openEditRoleDrawer,
                        confirmDeleteRole: this.confirmDeleteRole,
                    },
                    width: 100
                },
                
            ],
            rowData: [],

            columns: [
                {
                    dataIndex: 'name',
                    title: this.$t('team.column_name'),
                    key: 'name',
                    scopedSlots: { customRender: 'name' }
                },
                {   
                    width: 100,
                    dataIndex: 'actions',
                    title: '',
                    key: 'actions',
                    scopedSlots: { customRender: 'actions' }
                },
            ],
            tableLoading: false,
            gridApi: null
        }
    },
    computed: {
        ...mapState({
            roles: state => state.organization.roles,
            windowWidth: state => state.windowWidth,
            config: state => state.config.config,
            isMobile: state => state.isMobile
            
        }),
        widget() {
            if(this.isMobile) {
                return () => import('./PermissionList')
            }
            return () => import('./PermissionTable')
        },
        roleList() {
            return this.roles?.[this.organization.id]?.results || []
        },

        roleCount() {
            return this.roles?.[this.organization.id]?.count
        },
        tableSize() {
            return this.config?.theme?.tableSize ? this.config.theme.tableSize : 'small'
        }  
    },
}
</script>

<style>
</style>