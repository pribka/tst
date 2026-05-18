<template>
    <div class="rew_act">
        <div 
            v-tippy="{ 
                content: $t('helpdesk.very_bad'), 
                trigger: 'mouseenter', 
                hideOnClick: true, 
                inertia: true, 
                duration: [200,200], 
                interactive: false, 
                placement: 'top'
            }"
            :class="value === 1 && 'active'"
            class="rew_act__item sm_1"
            @click="itemSelect(1)">
            <svg xmlns="http://www.w3.org/2000/svg" id="Layer_1" data-name="Layer 1" viewBox="0 0 24 24" width="512" height="512"><path d="M16.789,17.976A15.4,15.4,0,0,0,12,17a15.4,15.4,0,0,0-4.793.976,1,1,0,0,1-1.052-1.518A6.836,6.836,0,0,1,12,13a6.827,6.827,0,0,1,5.842,3.458A1,1,0,0,1,16.789,17.976ZM24,12A12.013,12.013,0,0,0,12,0C-3.9.6-3.893,23.4,12,24A12.013,12.013,0,0,0,24,12Zm-2,0A10.011,10.011,0,0,1,12,22C-1.249,21.5-1.244,2.5,12,2A10.011,10.011,0,0,1,22,12Zm-4.168-.445a1,1,0,0,0-.277-1.387L15.8,9l1.752-1.168a1,1,0,0,0-1.11-1.664l-3,2a1.007,1.007,0,0,0,0,1.664l3,2a1,1,0,0,0,1.387-.277Zm-10.277.277,3-2a1.007,1.007,0,0,0,0-1.664l-3-2a1,1,0,0,0-1.11,1.664L8.2,9,6.445,10.168a1,1,0,0,0,1.11,1.664Z"/></svg>
        </div>
        <div 
            v-tippy="{ 
                content: $t('helpdesk.bad'), 
                trigger: 'mouseenter', 
                hideOnClick: true, 
                inertia: true, 
                duration: [200,200], 
                interactive: false, 
                placement: 'top'
            }"
            :class="value === 2 && 'active'"
            class="rew_act__item sm_2"
            @click="itemSelect(2)">
            <svg xmlns="http://www.w3.org/2000/svg" id="Layer_1" data-name="Layer 1" viewBox="0 0 24 24" width="512" height="512"><path d="M12,24A12,12,0,1,1,24,12,12.013,12.013,0,0,1,12,24ZM12,2A10,10,0,1,0,22,12,10.011,10.011,0,0,0,12,2Zm5.746,15.667a1,1,0,0,0-.08-1.413A9.454,9.454,0,0,0,12,14a9.454,9.454,0,0,0-5.666,2.254,1,1,0,0,0,1.33,1.494A7.508,7.508,0,0,1,12,16a7.51,7.51,0,0,1,4.336,1.748,1,1,0,0,0,1.41-.081ZM6,10c0,1,.895,1,2,1s2,0,2-1a2,2,0,0,0-4,0Zm8,0c0,1,.895,1,2,1s2,0,2-1a2,2,0,0,0-4,0Z"/></svg>
        </div>
        <div 
            v-tippy="{ 
                content: $t('helpdesk.average'), 
                trigger: 'mouseenter', 
                hideOnClick: true, 
                inertia: true, 
                duration: [200,200], 
                interactive: false, 
                placement: 'top'
            }"
            class="rew_act__item sm_3"
            :class="value === 3 && 'active'"
            @click="itemSelect(3)">
            <svg xmlns="http://www.w3.org/2000/svg" id="Layer_1" data-name="Layer 1" viewBox="0 0 24 24" width="512" height="512"><path d="M12,24A12,12,0,1,1,24,12,12.013,12.013,0,0,1,12,24ZM12,2A10,10,0,1,0,22,12,10.011,10.011,0,0,0,12,2Zm5,14a1,1,0,0,0-1-1H8a1,1,0,0,0,0,2h8A1,1,0,0,0,17,16ZM6,10c0,1,.895,1,2,1s2,0,2-1a2,2,0,0,0-4,0Zm8,0c0,1,.895,1,2,1s2,0,2-1a2,2,0,0,0-4,0Z"/></svg>
        </div>
        <div 
            v-tippy="{ 
                content: $t('helpdesk.good'), 
                trigger: 'mouseenter', 
                hideOnClick: true, 
                inertia: true, 
                duration: [200,200], 
                interactive: false, 
                placement: 'top'
            }"
            class="rew_act__item sm_4"
            :class="value === 4 && 'active'"
            @click="itemSelect(4)">
            <svg xmlns="http://www.w3.org/2000/svg" id="Layer_1" data-name="Layer 1" viewBox="0 0 24 24" width="512" height="512"><path d="M12,24A12,12,0,1,1,24,12,12.013,12.013,0,0,1,12,24ZM12,2A10,10,0,1,0,22,12,10.011,10.011,0,0,0,12,2Zm5.666,13.746a1,1,0,0,0-1.33-1.494A7.508,7.508,0,0,1,12,16a7.509,7.509,0,0,1-4.334-1.746,1,1,0,0,0-1.332,1.492A9.454,9.454,0,0,0,12,18,9.454,9.454,0,0,0,17.666,15.746ZM6,10c0,1,.895,1,2,1s2,0,2-1a2,2,0,0,0-4,0Zm8,0c0,1,.895,1,2,1s2,0,2-1a2,2,0,0,0-4,0Z"/></svg>
        </div>
        <div 
            v-tippy="{ 
                content: $t('helpdesk.very_good'), 
                trigger: 'mouseenter', 
                hideOnClick: true, 
                inertia: true, 
                duration: [200,200], 
                interactive: false, 
                placement: 'top'
            }"
            class="rew_act__item sm_5"
            :class="value === 5 && 'active'"
            @click="itemSelect(5)">
            <svg xmlns="http://www.w3.org/2000/svg" id="Layer_1" data-name="Layer 1" viewBox="0 0 24 24" width="512" height="512"><path d="M10,12a1,1,0,0,1-1-1c0-1.054-.68-2-1-2s-1,.946-1,2a1,1,0,0,1-2,0C5,9.108,6.232,7,8,7s3,2.108,3,4A1,1,0,0,1,10,12Zm9-1c0-1.892-1.232-4-3-4s-3,2.108-3,4a1,1,0,0,0,2,0c0-1.054.68-2,1-2s1,.946,1,2a1,1,0,0,0,2,0Zm5,1A12.013,12.013,0,0,0,12,0C-3.9.6-3.893,23.4,12,24A12.013,12.013,0,0,0,24,12Zm-2,0A10.011,10.011,0,0,1,12,22C-1.249,21.5-1.244,2.5,12,2A10.011,10.011,0,0,1,22,12Zm-4.334,3.746a1,1,0,0,0-1.33-1.493,6.36,6.36,0,0,1-8.67,0,1,1,0,0,0-1.332,1.492A9.454,9.454,0,0,0,12,18,9.454,9.454,0,0,0,17.666,15.746Z"/></svg>
        </div>
    </div>
</template>

<script>
export default {
    props: {
        value: { type: [Number, String, Object] }
    },
    methods: {
        itemSelect(type) {
            this.$emit('input', type)
        }
    }
}
</script>

<style lang="scss" scoped>
.rew_act{
    display: flex;
    align-items: center;
    gap: 15px;
    justify-content: center;
    &__item{
        user-select: none;
        cursor: pointer;
        svg{
            cursor: pointer;
            width: 40px;
            height: 40px;
            transition: all 0.3s cubic-bezier(0.645, 0.045, 0.355, 1);
        }
        &.active,
        &:hover{
            svg{
                transform: scale(1.2);
            }
        }
        &.sm_1{
            &.active,
            &:hover{
                fill: #f90a2e;
            }
        }
        &.sm_2{
            &.active,
            &:hover{
                fill: #e7a125;
            }
        }
        &.sm_3{
            &.active,
            &:hover{
                fill: #f4d729;
            }
        }
        &.sm_4{
            &.active,
            &:hover{
                fill: #89eb3e;
            }
        }
        &.sm_5{
            &.active,
            &:hover{
                fill: #2bab30;
            }
        }
    }
}
</style>