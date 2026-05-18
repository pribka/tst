<template>
    <a-tag class="" :color="getStatus(sprint.status) && getStatus(sprint.status).color">
        {{getStatus(sprint.status) && getStatus(sprint.status).name}}
    </a-tag>
</template>

<script>
import actions from '../actions'
export default {
    mixins: [actions],
    props: {
        sprint: Object
    }
}
</script>

<style>

</style>