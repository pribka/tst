<template>
    <div class="flex-grow flex min-h-0">
        <UniversalTable 
            :model="model"
            :pageName="pageName"
            :tableType="contractorsType"
            :endpoint="endpoint" />
    </div>
</template>

<script>
import UniversalTable from '@/components/TableWidgets/UniversalTable'
import { mapState } from 'vuex'

export default { 
    components: {
        UniversalTable,
    },
    props: {
        pageName: {
            type: String,
            required: true
        }
    },
    data() {
        return {
            tableType: 'contractors',
        }
    },
    computed: {
        ...mapState({
            models: state => state.contractors.models,
            contractorsType: state => state.contractors.contractorsType
        }),
        model() {
            return this.models[this.contractorsType]
        },
        isLead() {
            return this.contractorsType === 'leads'
        },
        endpoint() {
            if(this.isLead)
                return `/catalogs/leads/`
            return `/catalogs/contractors/detailed_list/`
        },
    },
}
</script>