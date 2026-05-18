import store from '@/store'
const ai = store.getters['config/ai']
export const vars = {
    ai_name: ai?.name,
    ai_placeholder: ai?.placeholder,
    ai_desc: ai?.desc,
    ai_avatar: "/img/ai_logo.jpg",
}