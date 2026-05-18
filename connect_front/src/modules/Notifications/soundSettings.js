import { getById, setData, updateById } from '@/utils/cacheDb'

const SOUND_SETTINGS_DB = 'notification_sound_settings'
const buildId = userId => `notification_sound_${userId}`

export const getNotificationSoundEnabled = async userId => {
    if(!userId) return true

    try {
        const data = await getById({
            id: buildId(userId),
            databaseName: SOUND_SETTINGS_DB
        })

        if(typeof data?.value === 'boolean')
            return data.value

        return true
    } catch(e) {
        return true
    }
}

export const setNotificationSoundEnabled = async({ userId, enabled }) => {
    if(!userId) return false

    const id = buildId(userId)

    try {
        const current = await getById({
            id,
            databaseName: SOUND_SETTINGS_DB
        })

        if(current) {
            await updateById({
                id,
                value: !!enabled,
                databaseName: SOUND_SETTINGS_DB
            })
        } else {
            await setData({
                data: {
                    id,
                    value: !!enabled
                },
                databaseName: SOUND_SETTINGS_DB
            })
        }

        return true
    } catch(e) {
        return false
    }
}
