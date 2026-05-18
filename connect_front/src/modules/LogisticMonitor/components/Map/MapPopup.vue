<template>
    <div>
        <div class="mb-1">
            #{{ item.counter }} - {{ item.name }}
        </div>
        <div class="flex items-center justify-between mb-1">
            <a-tag :color="item.status.color === 'default' ? '' : item.status.color">
                {{ item.status.name }}
            </a-tag>
            <div 
                class="users_info flex items-center" 
                :ref="`kanban_card_${item.id}`">
                <div class="flex">
                    <Profiler
                        :user="item.owner"
                        :showUserName="false"
                        initStatus
                        :avatarSize="18" />
                </div>
                <a-icon 
                    type="right" 
                    class="mx-1 text-xs" />
                <div class="flex">
                    <Profiler
                        :user="item.operator"
                        :showUserName="false"
                        initStatus
                        :avatarSize="18" />
                </div>
            </div>
        </div>
        <div>
            Адрес: {{ this.item.next_delivery_point.name }}
        </div>
    </div>
</template>

<script>
export default {
    props: {
        item: {
            type: Object,
            required: true
        }
    }
}
</script>