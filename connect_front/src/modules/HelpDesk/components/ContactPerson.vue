<template>
    <div v-if="showIcon" class="flex items-center justify-between">
        <div>
            <div class="contact-person-name">{{ contact_person.name }}</div> 
            <div v-if="contact_person.is_main" style="color: #888888;font-size: 12px;line-height: 16px;">{{ $t('helpdesk.is_main') }}</div> 
        </div>
        <a-popover :getPopupContainer="getPopupContainer" :placement="placement">
            <template #content>
                <ListView size="small">
                    <ListViewItem>
                        <span class="font-semibold">
                            {{ contact_person.name }}
                        </span>
                    </ListViewItem>
                    <ListViewItem v-if="contact_person.phone" :title="$t('helpdesk.phone')">
                        <a :href="`tel:${contact_person.phone}`">
                            {{ contact_person.phone }}
                        </a>
                    </ListViewItem>
                    <ListViewItem v-if="contact_person.telegram" :title="$t('helpdesk.telegram')">
                        {{ contact_person.telegram }}
                    </ListViewItem>
                    <ListViewItem v-if="contact_person.email" :title="$t('helpdesk.email')">
                        <a :href="`mailto:${contact_person.email}`">
                            {{ contact_person.email }}
                        </a>
                    </ListViewItem>
                </ListView>
            </template>
            <div>
                <i class="fi" :class="icon" style="margin-right: 8px;"/>
            </div>
        </a-popover>
    </div>
    <a-popover v-else :getPopupContainer="getPopupContainer" :placement="placement">
        <template #content>
            <ListView size="small">
                <ListViewItem>
                    <span class="font-semibold">
                        {{ contact_person.name }}
                    </span>
                </ListViewItem>
                <ListViewItem v-if="contact_person.phone" :title="$t('helpdesk.phone')">
                    <a :href="`tel:${contact_person.phone}`">
                        {{ contact_person.phone }}
                    </a>
                </ListViewItem>
                <ListViewItem v-if="contact_person.telegram" :title="$t('helpdesk.telegram')">
                    {{ contact_person.telegram }}
                </ListViewItem>
                <ListViewItem v-if="contact_person.email" :title="$t('helpdesk.email')">
                    <a :href="`mailto:${contact_person.email}`">
                        {{ contact_person.email }}
                    </a>
                </ListViewItem>
            </ListView>
        </template>
        <div>
            {{ contact_person.name }}
        </div>
    </a-popover>
</template>

<script>
export default {
    props: {
        contact_person: {
            type: Object,
            required: true
        },
        showIcon: {
            type: Boolean,
            default: false
        },
        icon: {
            type: String,
            default: 'fi-rr-info'
        },
        placement: {
            type: String,
            default: "bottom"
        }
    },
    methods: {
        getPopupContainer(trigger) {
            return trigger.parentNode
        }
    }
}
</script>