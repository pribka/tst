import { deleteById } from '@/utils/cacheDb'

export const clearGlobalConfigCache = () => deleteById({
    id: 'global',
    databaseName: 'config'
})
