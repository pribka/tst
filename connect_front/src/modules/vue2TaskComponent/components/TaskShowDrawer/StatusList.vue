<template>
    <div 
        v-if="status.length" 
        class="status_list"
        :data-guide-id="isInterest ? 'interest-status-flow' : null"
        :class="{ 'status_list--interest': isInterest }">
        <div 
            v-for="(item, index) in status" 
            :key="item.code"
            class="item">
            <div 
                class="wrap"
                :class="[checkActive(item, index), item.color, isAuthor && 'cursor-pointer']"
                @click="changeStatus(item)">
                <a-badge :color="item.color" />
                <span>{{ item.name }}</span>
            </div>
        </div>
    </div>
</template>

<script>
import { mapState } from 'vuex'
import { errorHandler } from '@/utils/index.js'
export default {
    props: {
        task: {
            type: Object,
            required: true
        },
        isAuthor: {
            type: Boolean,
            default: false
        }
    },  
    computed: {
        ...mapState({
            statusList: state => state.task.statusList
        }),
        status() {
            return this.statusList?.[this.task.task_type]?.length ? this.statusList[this.task.task_type] : []
        },
        isInterest() {
            return this.task?.task_type === 'interest'
        },
        currentIndex() {
            const index = this.status.findIndex(f => f.code === this.task.status.code)
            if(index !== -1)
                return index
            else
                return null
        },
        checkStatus() {
            if(this.task.status.is_complete && this.task.status.code === 'failed')
                return 'select failed'
            else if(this.task.status.is_complete)
                return 'select success'
            else
                return 'select'
        }
    },
    methods: {
        checkActive(item, index) {
            if(this.task?.status?.code === item.code)
                return this.checkStatus
            else {
                return index <= this.currentIndex && this.checkStatus
            }
        },
        async changeStatus(status) {
            if(this.isAuthor) {
                try {
                    await this.$store.dispatch('task/changeStatus', {
                        task: this.task, 
                        status
                    })
                } catch(error) {
                    errorHandler({error})
                }
            }
        }
    }
}
</script>

<style lang="scss" scoped>
.status_list{
    display: flex;
    align-items: center;
    margin-bottom: 20px;
    .item{
        width: 100%;
        -moz-user-select: none;
        -khtml-user-select: none;
        user-select: none;
        @media (max-width: 1200px) {
            font-size: 12px;
        }
        &:not(:last-child){
            margin-right: 13px;
        }
        .wrap{
            background: #eee;
            color: var(--text);
            display: flex;
            align-items: center;
            border-radius: var(--borderRadius) 0 0 var(--borderRadius);
            height: 32px;
            line-height: 26px;
            padding: 0 15px 0 15px;
            position: relative;
            margin-right: 10px;
            text-decoration: none;
            -webkit-transition: color 0.2s;
            width: 100%;
            min-width: 0;
            span{
                min-width: 0;
                overflow: hidden;
                text-overflow: ellipsis;
            }
            &::after{
                background: #fff;
                border-bottom: 16px solid transparent;
                border-left: 10px solid #eee;
                border-top: 16px solid transparent;
                content: '';
                position: absolute;
                left: 100%;
                top: 0;
            }
            &.select{
                background: var(--blue);
                color: #fff;
                &::after{
                    border-left: 10px solid var(--blue);
                }
                &.success{
                    background: #89d961;
                    &::after{
                        border-left: 10px solid #89d961;
                    }
                }
                &.failed{
                    background: #f5222d;
                    &::after{
                        border-left: 10px solid #f5222d;
                    }
                }
            }
        }
    }
}

.status_list--interest{
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(132px, 1fr));
    gap: 8px;
    align-items: stretch;
    margin: 0 0 16px;
    padding: 10px;
    border: 1px solid #edf0f4;
    border-radius: 8px;
    background: #fafbfc;

    .item{
        width: auto;
        margin: 0 !important;
        font-size: 12px;

        .wrap{
            min-height: 42px;
            height: auto;
            margin: 0;
            padding: 8px 11px;
            border: 1px solid #e3e7ee;
            border-radius: 7px;
            background: #fff;
            color: #344054;
            line-height: 1.25;
            gap: 7px;
            transition: border-color .15s ease, background-color .15s ease, color .15s ease;

            &::after{
                display: none;
            }

            span{
                white-space: normal;
                overflow: visible;
                text-overflow: unset;
            }

            &.select{
                border-color: #4f7cff;
                background: #eef3ff;
                color: #1d4ed8;

                &.success{
                    border-color: #5fba7d;
                    background: #effaf3;
                    color: #247547;
                }

                &.failed{
                    border-color: #f04438;
                    background: #fff1f0;
                    color: #b42318;
                }
            }
        }
    }
}
</style>
