<template>
    <div class="stat_card">
        <div class="head_info">
            <div class="info">
                <div class="value">
                    <span>
                        {{ statValue }}
                    </span>
                </div>
                <div class="label">
                    {{ statLaebel }}
                </div>
            </div>
        </div>
        <div 
            v-if="statProgress" 
            class="stat">
            <a-progress 
                :status="statProgressStatus"
                :stroke-color="statProgressColor"
                :percent="statProgressPercent" />
        </div>
    </div>
</template>

<script>
export default {
    props: {
        statLaebel: {
            type: String,
            required: true
        },
        statValue: {
            type: [Number, String],
            required: true
        },
        statProgress: {
            type: Boolean,
            default: true
        },
        statProgressStatus: {
            type: String,
            default: 'active'
        },
        statProgressPercent: {
            type: [Number, String],
            default: 0
        },
        statProgressColor: {
            type: [String, Object],
            default: '#1d65c0'
        }
    }
}
</script>

<style lang="scss" scoped>
.stat_card{
    padding: 20px;
    border-radius: 5px;
    background: #eff2f5;
    .head_info{
        margin-bottom: 15px;
        .label{
            font-weight: 300;
        }
        .value{
            color: #000;
            font-size: 28px;
            font-weight: 900;
        }
    }
}
</style>

<style lang="scss">
.stat_card{
    .ant-progress-inner{
        background-color: #fff;
    }
}
</style>