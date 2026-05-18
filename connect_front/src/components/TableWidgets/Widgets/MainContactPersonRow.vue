<template>
    <div v-if="record.main_contact_person">
        <div>{{ record.main_contact_person.name }}</div>
        <div v-if="record.main_contact_person.post_inst" style="color: #888888;font-size: 13px;line-height: 17px;">{{ record.main_contact_person.post_inst.name }}</div>
    </div>
</template>

<script>
export default {
    props: {
        record: {
            type: Object
        }
    }

}
</script>