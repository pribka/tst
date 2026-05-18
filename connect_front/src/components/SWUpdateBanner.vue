<template>
    <div v-if="online && swUpdate" class="sw_update_banner">
        <p>{{ $t('app_update_text') }}</p>
        <div class="flex justify-center w-full">
            <a-button ghost class="flex items-center px-8" :loading="loading" icon="sync" @click="update">
                {{ $t('app_update') }}
            </a-button>
        </div>
    </div>
</template>

<script>
import { mapState } from 'vuex'

export default {
    computed: {
        ...mapState({
            swUpdate: state => state.swUpdate,
            swRegistration: state => state.swRegistration,
            online: state => state.online
        })
    },
    data() {
        return {
            loading: false
        }
    },
    methods: {
        async update() {
            this.loading = true
            try {
                const reg = this.swRegistration || window.__swRegistration__
                if (!reg || !reg.waiting) return

                const onChange = () => {
                    navigator.serviceWorker.removeEventListener('controllerchange', onChange)
                    location.reload()
                }
                navigator.serviceWorker.addEventListener('controllerchange', onChange)

                await reg.waiting.postMessage({ type: 'SKIP_WAITING' })
            } catch (e) {
                console.error('SW update error', e)
            } finally {
                this.loading = false
            }
        }
    }

}
</script>

<style lang="scss" scoped>
.sw_update_banner{
  position: fixed;
  z-index: 700;
  background: rgba(0, 0, 0, 0.8);
  color: #fff;
  padding: 15px;
  border-radius: 5px;
  bottom: 20px;
  right: 20px;
  text-align: center;
  p{
    font-size: 16px;
    margin-bottom: 10px;
  }
}
</style>

