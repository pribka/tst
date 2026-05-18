import SoundMaster from './soundMaster'

const build = url => {
    const a = new Audio(url)
    a.preload = 'auto'
    return a
}

const base = process.env.BASE_URL || '/'
const sounds = {
    chat_new_message: build(`${base}sound/new_message.mp3`),
    notify_new: build(`${base}sound/new_notify.mp3`),
    call_incoming: build(`${base}sound/call_bells.wav`),
    call_sending: build(`${base}sound/call_sending.mp3`)
}

export const initSounds = () => {
    SoundMaster.setResolver(k => sounds[k])
    return sounds
}
