<template>
    <div class="user-item" :class="checked && checkedClass">
        <a-checkbox
            v-if="multiple"
            size="large"
            class="checkbox" 
            :checked="checked"
            @click="itemSelect(item, true)" />
        <a-radio
            v-else
            :value="item.id"
            @click="itemSelect(item, true)" />
        <a-avatar
            icon="user"
            :src="avatarSrc"
            class="avatar"
            @click="itemSelect(item, true)" />
        <div class="username" @click="itemSelect(item, true)">
            <div class="name">
                {{ item.full_name || item.name }}
            </div>
            <div v-if="item.job_title" class="job_title">
                {{ item.job_title }} 
            </div>
        </div>
    </div>
</template>

<script>
export default {
    name: 'UserItem',
    props: {
        item: {
            type: Object,
            required: true,
        },
        multiple: {
            type: Boolean,
            default: false
        },
        checkedClass: {
            type: String,
            default: ''
        },
        checkSelected: {
            type: Function,
            default: () => {}
        },
        itemSelect: {
            type: Function,
            default: () => {}
        },
    },
    computed: {
        avatarSrc() {
            return this.item?.avatar?.path || this.item?.image?.path || this.item.logo
        },
        checked() {
            return this.checkSelected(this.item)
        }
    }
}
</script>

<style lang="scss" scoped>
.user-item {
    display: flex;
    align-items: center;
    gap: 12px;
    width: 100%;
    border-radius: 8px;
    padding: 8px 12px;
    &:hover{
        background: rgb(255, 255, 255);
    }
    &:not(:last-child){
        margin-bottom: 4px;
    }
}
.avatar {
    cursor: pointer;
    min-width: 32px;

}
.checkbox {
    position: relative;
    z-index: 1000;
}
.username {
    transition: color 0.2s ease;
    cursor: pointer;
    &:hover{
        color: var(--primaryColor);
    }
    display: flex;
    flex-direction: column;
    .name {
        transition: color 0.2s ease;
        display: -webkit-box;
        -webkit-line-clamp: 1;
        -webkit-box-orient: vertical;
        overflow: hidden;
        text-overflow: ellipsis;
        line-height: 1.5;
        max-height: calc(1 * 1.5em);
        word-break: break-word;
    }
    .job_title {
        font-size: 12px;
        line-height: 16px;
        color: rgba(136, 136, 136, 1);

        transition: color 0.2s ease;
        display: -webkit-box;
        -webkit-line-clamp: 1;
        -webkit-box-orient: vertical;
        overflow: hidden;
        text-overflow: ellipsis;
        line-height: 1.5;
        max-height: calc(1 * 1.5em);
        word-break: break-word;
    }
}
:deep {
    .ant-checkbox-inner {
        width: 20px;
        height: 20px;
        border-radius: 4px;
    }
}

.list_item {
    padding-left: 35px;
    & + & {
        margin-top: 20px;
    }
}


.item_angle {
    position: relative;
    z-index: 1000;

    display: flex;
    justify-content: center;
    flex-shrink: 0;
    width: 20px;
    
    margin-right: 15px;

    color: var(--primaryColor);
    transition: transform 0.2s ease;
    cursor: pointer;
}

.item_angle.expanded {
    transform: rotate(180deg);
}


.selectable {
    .username,
    .organization_name {
        cursor: pointer;
    }
}
.selectable:hover {
    .username,
    .organization_name {
        color: var(--primaryColor);
    }
}

</style>