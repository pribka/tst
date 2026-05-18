<template>
    <div>
        {{contractor ? contractor.name : "---" }}
    </div>
</template>

<script>
export default {
    name:'TaskContractor',
    props: ['contractor']
    
}
</script>
