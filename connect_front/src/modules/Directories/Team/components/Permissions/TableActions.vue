<template>
    <div>
        <span 
            @click="params.openEditRoleDrawer(params.data)"
            class="mr-4 blue_color cursor-pointer text-base">
            <i class="fi fi-rr-edit"></i>
        </span>
        <span 
            @click="params.confirmDeleteRole(params.data)"
            class="text_red cursor-pointer text-base">
            <i class="fi fi-rr-trash"></i>
        </span>
    </div>
</template>

<script>
export default {
}
</script>

<style>

</style>