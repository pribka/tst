<template>
    <div class="flex items-center">
        <div class="mr-2">
            <a-button
                v-if="!record.showChildren"
                type="link"
                size="small"
                class="p-0 text-current"
                flaticon
                @click="openOrganizationDrawer"
                icon="fi fi-rr-add" />
            <a-button
                v-else
                type="link"
                size="small"
                class="p-0 text-current"
                flaticon
                @click="openOrganizationDrawer"
                icon="fi fi-rr-minus-circle" />
        </div>
        <div class="flex items-center">
            <div :key="record.logo" class="pr-2">
                <a-avatar 
                    :size="30"
                    :src="record.logo"
                    icon="fi-rr-users-alt" 
                    flaticon />
            </div>
            <button class="blue_color" 
                    @click="openOrganizationDrawer">
                {{ record.name }}
            </button>
        </div>
    </div>
</template>

<script>
import eventBus from '@/utils/eventBus'
export default {
    props: {
        record: {
            type: Object,
            required: true
        },
        indent: {
            type: Object,
            default: () => null
        },
        expanded: {
            type: Number,
            default: null
        },
        toggleChildren: {
            type: Function,
            default: () => {}
        }
    },
    methods: {
        openOrganizationDrawer() {
            eventBus.$emit('open_organization_drawer_view', this.record)
        }
    }
}
</script>