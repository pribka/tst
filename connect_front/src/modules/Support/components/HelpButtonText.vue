<template>
    <a-tag class="cursor-pointer flex items-center" contrastText color="orange" @click="open">
        <i class="fi fi-rr-interrogation" />
        <span class="ml-2 font-normal text-[#2D2D2D]">
            {{ $t('support.work_use') }}
        </span>
    </a-tag>
</template>

<script>
export default {
    props: {
        partType: {
            type: String,
            default: 'sections'
        },
        partCode: {
            type: String,
            required: true
        },
        type: {
            type: String,
            default: 'text'
        }
    },
    methods: {
        open() {
            const query = this.$route.query
            this.$router.replace({ query: { ...query, help: true, [this.partType]: this.partCode }})
        }
    }
}
</script>