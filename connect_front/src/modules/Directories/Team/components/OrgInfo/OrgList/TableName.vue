<template>
    <div class="flex items-center">
        <div :key="currentOrg.logo" class="pr-2">
            <a-avatar 
                :size="30"
                :src="currentOrg.logo"
                icon="fi-rr-users-alt" 
                flaticon />
        </div>
        <span>{{ currentOrg.name }}</span>
    </div>
</template>

<script>
export default {
    props: {
        record: {
            type: Object,
            required: true
        },
        org: {
            type: [Object],
            required: true
        }
    },
    computed: {
        currentOrg() {
            if(this.record.contractor.id === this.org.id)
                return this.record.contractor_parent
            else
                return this.record.contractor
        }
    }
}
</script>