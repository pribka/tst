<template>
    <a-tag 
        class="m-0" 
        :color="color">
        <div 
            v-if="icon" 
            v-tippy="{ inertia : true}"
            class="flex items-center py-1"
            :content="`<div><strong>${statusType}:</strong></div>${status.name}`">
            <i class="fi" :class="iconType"></i>
        </div>
        <template v-else>
            {{status.name}}
        </template>
    </a-tag>
</template>

<script>
export default {
    props: {
        status: {
            type: Object,
            reqired: true
        },
        icon: {
            type: Boolean,
            default: false
        },
        iconType: {
            type: String,
            default: 'fi-rr-bookmark'
        },
        statusType: {
            type: String,
            default: 'Статус'
        }
    },
    computed: {
        color() {
            if(this.status.color) {
                return this.status.color
            } else {
                switch (this.status.code) {
                case 'default':
                    return 'blue'
                    break;
                default:
                    return 'default'
                }
            }
        }
    }
}
</script>