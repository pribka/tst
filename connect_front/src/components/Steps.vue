<template>
    <div class="wrapper">
        <div class="steps">
            <div 
                class="step"
                :style="styleDistance(index)"
                :class="activeClass(index)"
                v-for="step, index in steps"
                :key="index">
                {{ stepNumber(index) }}
            </div>
        </div>
        <div class="skewer"></div>
    </div>
</template>

<script>
export default {
    props: {
        distance: {
            type: Number,
            default: 80
        },
        current: {
            type: Number,
            default: null
        },
        steps: {
            type: Array,
            required: false
        },
        showDecimal: {
            type: Boolean,
            default: false
        },
        highlightPrevious: {
            type: Boolean,
            default: false
        },
    },
    methods: {
        stepNumber(index) {
            const number = index + 1
            if (number < 10) {
                return `0` + number
            }
            return number
        },
        styleDistance(index) {
            if (this.distance && index !== this.steps.length-1) 
                return `margin-right: ${this.distance}px`
            return ``
        },
        activeClass(index) {
            if (this.highlightPrevious) {
                return this.current > index && 'active'   
            }
            return this.current === (index+1) && 'active'   
        }
    }
}
</script>

<style lang="scss" scoped>
$step-round-height: 40px;
.wrapper {
    position: relative;
    height: $step-round-height;
}
.skewer {
    position: absolute;
    top: 50%;
    width: 100%;
    height: 1px;
    background-color: #ebebeb;
}
.steps {
    justify-content: space-between;
    display: flex;
}
.step {
    z-index: 10;

    display: flex;
    align-items: center;
    justify-content: center;

    width: $step-round-height;
    height: $step-round-height;
    min-width: $step-round-height;
    min-height: $step-round-height;
    
    color: #000;
    font-size: 1rem;

    border-radius: 100%;
    background-color: #EBEBEB;

    transition: 
        color 0.3s ease,
        background 0.3s ease;
}
.step:not(:last-child) {
    // margin-right: 1rem;
}
.step.active {
    background-color: var(--blue);
    color: #fff;
}
</style>