<template>
    <span>
        <template v-if="item.children_count">
            <span class="mr-2 font-light">
                <a-tooltip destroyTooltipOnHide>
                    <template slot="title">
                        {{ $t('task.subtask_count') }}
                    </template>
                    <span class="mr-1">
                        <i class="fi fi-rr-list-check"></i>                            
                    </span>
                    <span>{{ item.children_count }}/{{ item.completed_children_count }}</span>
                </a-tooltip>
            </span>
        </template>
        <template v-if="item.comments_count">
            <span class="mr-2 font-light">
                <a-tooltip destroyTooltipOnHide>
                    <template slot="title">
                        {{ $t('task.comment_count') }}
                    </template>
                    <span class="mr-1">
                        <i class="fi fi-rr-comment-alt"></i>                        
                    </span>
                    <span>{{ item.comments_count }}</span>
                </a-tooltip>
            </span>
        </template>
        <template v-if="item.attachments_count">
            <span class="mr-2 font-light">
                <a-tooltip destroyTooltipOnHide>
                    <template slot="title">
                        {{ $t('task.files_count') }}
                    </template>
                    <span class="mr-1">
                        <i class="fi fi-rr-clip"></i>                        
                    </span>
                    <span>{{ item.attachments_count }}</span>
                </a-tooltip>
            </span>
        </template>
        <template v-if="item.has_description">
            <span class="mr-2 font-light">
                <a-tooltip destroyTooltipOnHide>
                    <template slot="title">
                        {{ $t('task.card_desc') }}
                    </template>
                    <i class="fi fi-rr-align-left"></i> 
                </a-tooltip>
            </span>
        </template>
    </span>
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