
import eventBus from '@/utils/eventBus'
import store from '@/store/index.js'

export const getColor = (name) => {
    switch (name) {
    case "success": return 'rgba(135, 208, 104, 1);'
    case "primary": return 'rgba(29, 101, 192, 1);'
    case "info": return 'rgba(45, 183, 245, 1);'
    case "warning": return 'rgba(250, 158, 58, 1);'
    case "error": return 'rgba(246, 59, 69, 1);'
    }
}

export const getBackground = (name) => {
    switch (name) {
    case "success": return 'rgba(135, 208, 104, .1);'
    case "primary": return 'rgba(29, 101, 192, .1);'
    case "info": return 'rgba(45, 183, 245, .1);'
    case "warning": return 'rgba(250, 158, 58, .1);'
    case "error": return 'rgba(246, 59, 69, .1);'
    }
}

export const getNotificationIconClass = icon => {
    switch (icon) {
    case 'ellipsis': return 'fi fi-rr-comment-alt'
    case 'info': return 'fi fi-rr-info'
    case 'profile': return 'fi fi-rr-list-check'
    case 'schedule': return 'fi fi-rr-megaphone'
    case 'file-text': return 'fi fi-rr-document-signed'
    default: return null
    }
}

const NOTIFICATION_URL_RE = /(https?:\/\/[^\s<>"')\]]+|www\.[^\s<>"')\]]+)(\s*\/+)?/gi

const ensureAnchorAttrs = a => {
    if (!a.getAttribute('target')) a.setAttribute('target', '_blank')
    const rel = a.getAttribute('rel') || ''
    const parts = new Set(rel.split(/\s+/).filter(Boolean))
    parts.add('noopener')
    parts.add('noreferrer')
    a.setAttribute('rel', Array.from(parts).join(' '))
}

const createContainerWithLinks = html => {
    if (typeof document === 'undefined') return null

    const container = document.createElement('div')
    container.innerHTML = html || ''

    const walker = document.createTreeWalker(container, NodeFilter.SHOW_TEXT, null, false)
    const textNodes = []
    while (walker.nextNode()) textNodes.push(walker.currentNode)

    textNodes.forEach(node => {
        if (!node.parentElement) return
        if (node.parentElement.closest('.n_link')) return
        if (node.parentElement.closest('a')) return
        const text = node.nodeValue
        if (!text || !NOTIFICATION_URL_RE.test(text)) return
        NOTIFICATION_URL_RE.lastIndex = 0

        const frag = document.createDocumentFragment()
        let lastIndex = 0
        let match

        while ((match = NOTIFICATION_URL_RE.exec(text)) !== null) {
            const fullMatch = match[0]
            const main = match[1]
            const trailingSlashesGroup = match[2] || ''
            const start = match.index

            if (start > lastIndex) {
                frag.appendChild(document.createTextNode(text.slice(lastIndex, start)))
            }

            let urlPart = main + trailingSlashesGroup.replace(/\s+/g, '')
            let trailing = ''

            while (urlPart.length && /[.,;:!?)\]\u00A0]$/.test(urlPart)) {
                trailing = urlPart.slice(-1) + trailing
                urlPart = urlPart.slice(0, -1)
            }

            if (!urlPart) {
                frag.appendChild(document.createTextNode(fullMatch))
                lastIndex = start + fullMatch.length
                continue
            }

            const a = document.createElement('a')
            const href = urlPart.startsWith('http') ? urlPart : `http://${urlPart}`
            a.setAttribute('href', href)
            a.textContent = urlPart
            ensureAnchorAttrs(a)
            frag.appendChild(a)

            if (trailing) frag.appendChild(document.createTextNode(trailing))
            lastIndex = start + fullMatch.length
        }

        if (lastIndex < text.length) {
            frag.appendChild(document.createTextNode(text.slice(lastIndex)))
        }

        node.parentNode.replaceChild(frag, node)
    })

    Array.from(container.querySelectorAll('a')).forEach(a => {
        if (a.closest('.n_link')) return
        ensureAnchorAttrs(a)
    })

    return container
}

const createDescriptorFromElement = el => {
    if (!el) return null

    if (el.classList && el.classList.contains('n_link')) {
        return {
            kind: 'notification_link',
            name: el.getAttribute('data-link-type'),
            query: el.getAttribute('data-link-query'),
            toOpen: el.getAttribute('data-link-open')
        }
    }

    if (el.tagName === 'A') {
        return {
            kind: 'anchor',
            href: el.getAttribute('href'),
            target: el.getAttribute('target') || '_blank',
            rel: el.getAttribute('rel') || 'noopener noreferrer'
        }
    }

    return null
}

export const linkifyNotificationHtml = html => {
    const container = createContainerWithLinks(html)
    return container ? container.innerHTML : html || ''
}

export const getLastNotificationLink = html => {
    const container = createContainerWithLinks(html)
    if (!container) return null

    const elements = Array.from(container.querySelectorAll('.n_link, a'))
        .filter(el => !el.closest('.n_link a'))

    if (!elements.length) return null

    return createDescriptorFromElement(elements[elements.length - 1])
}

const wait = (interval = 50, timeout = 600) => new Promise(resolve => {
    const start = Date.now()
    const loop = () => {
        if (Date.now() - start >= timeout) return resolve()
        setTimeout(loop, interval)
    }
    loop()
})

export const openNotificationLink = async(link, options = {}) => {
    if (!link || !store) return false

    const {
        router,
        route,
        messageText = ''
    } = options
    if (!router || !route) return false
    const isMobile = !!store.state.isMobile

    if (link.kind === 'anchor' && link.href) {
        if (typeof window !== 'undefined') {
            window.open(link.href, link.target || '_blank')
        }
        return true
    }

    if (link.kind !== 'notification_link') return false

    const { name, query, toOpen } = link

    if (name === 'chat' && query) {
        const parseQuery = JSON.parse(query)
        const chatId = parseQuery.chat_id
        if (isMobile)
            delete parseQuery.chat_id
        if (route.name === 'chat' && !isMobile) {
            if (route.query?.chat_id) {
                if (parseQuery.ai_summary && route.query?.chat_id === parseQuery.chat_id)
                    eventBus.$emit('chat_ai_summary_show')
                if (route.query?.chat_id === parseQuery.chat_id) {
                    const oQuery = JSON.parse(JSON.stringify(route.query))
                    oQuery.message_id = parseQuery.message_id
                    router.replace({ query: oQuery })
                        .then(() => {
                            eventBus.$emit('CHAT_SEARCH_USER_TAGS')
                        })
                } else {
                    const oQuery = JSON.parse(JSON.stringify({
                        ...route.query,
                        ...parseQuery
                    }))
                    router.replace({ query: oQuery })
                        .then(() => {
                            eventBus.$emit('CHAT_SEARCH_SELECT_CHAT')
                        })
                }
            } else {
                const oQuery = JSON.parse(JSON.stringify({
                    ...route.query,
                    ...parseQuery
                }))
                router.replace({ query: oQuery })
                    .then(() => {
                        eventBus.$emit('CHAT_SEARCH_SELECT_CHAT')
                    })
            }
        } else {
            if (isMobile)
                router.push({ name: 'chat-body', params: { id: chatId }, query: parseQuery }).catch(e => {})
            else
                router.push({ name: 'chat', query: parseQuery }).catch(e => {})
        }
        store.commit('notifications/SET_DRAWER_VISIBLE', false)
        return true
    }

    const hasQuery = Object.keys(route.query || {}).length > 0
    if (hasQuery) {
        if (route.query?.task)
            eventBus.$emit('CLOSE_SHOW_TASK_DRAWER')
        if (route.query?.sprint)
            eventBus.$emit('close_sprint_drawer')
        await router.replace({ query: {} }).catch(e => {})
        await wait()
    }

    const jsonStr = query?.replace(/(\w+:)|(\w+ :)/g, m => '"' + m.substring(0, m.length - 1) + '":')
    const obj = jsonStr ? JSON.parse(jsonStr) : {}

    if (name === 'full_invest_project_info') {
        toOpen === 'true' ? store.commit('notifications/SET_DRAWER_Z_INDEX') : store.commit('notifications/SET_DRAWER_VISIBLE', false)
        router.push({ name, params: { id: obj.id } }).catch(e => {})
        return true
    }

    if (name === 'project_organization_member_invite') {
        eventBus.$emit('open_member_organization_invite_modal', { data: obj, message: messageText })
        return true
    }

    if (toOpen === null || toOpen === 'false') {
        store.commit('notifications/SET_DRAWER_VISIBLE', false)
        router.push({ name, query: obj }).catch(e => {})
    } else {
        store.commit('notifications/SET_DRAWER_Z_INDEX')
        router.push({ query: obj }).catch(e => {})
    }

    return true
}
