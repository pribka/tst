<template>
    <canvas
        v-if="enabled"
        ref="canvas"
        class="snow_canvas"/>
</template>

<script>
export default {
    name: 'SnowCanvas',
    data() {
        return {
            enabled: true,
            ctx: null,
            width: 0,
            height: 0,
            flakes: [],
            animationId: null
        }
    },
    mounted() {
        //this.enabled = localStorage.getItem('show_snow') === 'true'
        //if (!this.enabled) return

        this.initCanvas()
        this.createSnow()
        this.loop()
        window.addEventListener('resize', this.onResize)
    },
    beforeDestroy() {
        cancelAnimationFrame(this.animationId)
        window.removeEventListener('resize', this.onResize)
    },
    methods: {
        initCanvas() {
            this.ctx = this.$refs.canvas.getContext('2d')
            this.onResize()
        },
        onResize() {
            this.width = window.innerWidth
            this.height = window.innerHeight
            this.$refs.canvas.width = this.width
            this.$refs.canvas.height = this.height
            this.createSnow()
        },
        createSnow() {
            const baseCount = Math.floor(this.width / 6)

            this.flakes = Array.from({ length: baseCount }, () => {
                const depth = Math.random()

                return {
                    x: Math.random() * this.width,
                    y: Math.random() * this.height,
                    r: depth * 3 + 0.5,
                    speed: depth * 2 + 0.3,
                    drift: (Math.random() - 0.5) * depth,
                    opacity: depth * 0.6 + 0.2,
                    color: depth > 0.6 ? '255,255,255' : '210,210,210'
                }
            })
        },

        draw() {
            this.ctx.clearRect(0, 0, this.width, this.height)

            this.flakes.forEach(flake => {
                this.ctx.fillStyle = `rgba(${flake.color},${flake.opacity})`
                this.ctx.beginPath()
                this.ctx.arc(flake.x, flake.y, flake.r, 0, Math.PI * 2)
                this.ctx.fill()
            })
        },
        update() {
            this.flakes.forEach(flake => {
                flake.y += flake.speed
                flake.x += flake.drift

                if (flake.y > this.height) {
                    flake.y = -flake.r
                    flake.x = Math.random() * this.width
                }

                if (flake.x > this.width) flake.x = 0
                if (flake.x < 0) flake.x = this.width
            })
        },
        loop() {
            this.draw()
            this.update()
            this.animationId = requestAnimationFrame(this.loop)
        }
    }
}
</script>

<style scoped>
.snow_canvas {
    position: fixed;
    inset: 0;
    pointer-events: none;
    z-index: 9999
}
</style>