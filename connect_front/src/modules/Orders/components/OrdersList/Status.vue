<template>
    <a-tag 
        class="m-0" 
        :color="color">
        <div 
            v-if="icon" 
            v-tippy="{ inertia : true}"
            class="flex items-center py-1"
            @click="click(id, statusRecord)"
            :content="`<div><strong>${statusType}:</strong></div><div>${status.name}</div><div>${extraInfo}</div>`">
            <i class="fi" :class="iconType"></i>
        </div>
        <template v-else>
            <div @click="click(id, statusRecord)">
                {{status.name}}
            </div>
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
        extraInfo: {
            type: String,
            default: ''
        },
        statusType: {
            type: String,
            default: 'Статус'
        },
        click: {
            type: Function,
            default: () => {}
        },
        id: {
            type: String,
            default: 'Статус'
        },
        statusRecord: {
            type: Object,
            default: () => null
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