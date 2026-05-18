<template>
    <div class="report_call">
        <div class="report_call__header">
            <h4><slot name="h_title"></slot></h4>
            <div class="report_range">
                <slot name="h_range"></slot>
            </div>
        </div>
        <slot />
    </div>
</template>

<style lang="scss" scoped>
.report_call{
    background: #fff;
    border-radius: 8px;
    padding: 20px;
    &__header{
        display: flex;
        align-items: center;
        justify-content: space-between;
        padding-bottom: 15px;
        h4{
            white-space: nowrap;
            font-size: 18px;
            color: #000;
            padding-right: 20px;
        }
    }
    .report_range{
        &::v-deep{
            .ant-calendar-picker{
                .ant-calendar-range-picker-separator{
                    color: #000;
                    padding: 0 6px;
                }
                .ant-calendar-picker-input{
                    background-color: transparent;
                    border: 0px;
                    padding: 0px 30px 0px 0px;
                    display: flex;
                    justify-content: flex-end;
                    box-shadow: initial!important;
                }
                .ant-calendar-range-picker-input{
                    width: 27%;
                }
            }
        }
    }
}
</style>