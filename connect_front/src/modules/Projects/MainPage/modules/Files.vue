<template>
    <div ref="groupLightWrap">
        <Files
            :sourceId="id"
            :isFounder="fileFounder"
            :active="active"
            :isStudent="isStudent"/>
    </div>
</template>

<script>
export default {
    name: "GroupsAndProjectFiles",
    props: {
        id: {
            type: [String, Number],
            default: null
        },
        active: {
            type: [String, Number],
            default: null
        },
        isStudent: {
            type: Boolean,
            required: true
        },
        actions: {
            type: Object,
            default: () => null
        }
    },
    components: {
        Files: () => import('@apps/vue2Files')
    },
    computed: {
        fileFounder() {
            if(this.actions?.create_file) {
                return true
            } else {
                return false
            }
            // return this.actions?.create_file ? true || false
        }
    }
}
</script>