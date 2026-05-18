export const declOfNum = (n, text_forms) => {
    n = Math.abs(n) % 100; var n1 = n % 10;
    if (n > 10 && n < 20) { return text_forms[2]; }
    if (n1 > 1 && n1 < 5) { return text_forms[1]; }
    if (n1 === 1) { return text_forms[0]; }
    return text_forms[2];
}

export const chatName = (chat) => {

}

export const isFileImage = (file) => {
    return file && file['type'].split('/')[0] === 'image'
}

const isImageFileType = (type) => {
    return !!type && type.indexOf('image/') === 0;
}

export const clearMessageHtmlTruncate = (text, maxLen = 100, suffix = '…') => {
    if (!text) return ''

    const ALLOWED = new Set([
        'A',
        'B',
        'STRONG',
        'I',
        'U',
        'S',
        'DEL',
        'STRIKE'
    ])

    const doc = new DOMParser().parseFromString(String(text), 'text/html')

    const escapeAttr = v =>
        String(v)
            .replace(/&/g, '&amp;')
            .replace(/"/g, '&quot')
            .replace(/</g, '&lt')
            .replace(/>/g, '&gt')

    const isMentionSpan = el => {
        if (el.tagName !== 'SPAN') return false
        const cls = el.getAttribute('class') || ''
        return cls.split(/\s+/).includes('mention') || cls.split(/\s+/).includes('user_chat_mention')
    }

    const normalize = s =>
        String(s)
            .replace(/(\r\n|\n|\r)/g, ' ')
            .replace(/\s+/g, ' ')
            .trim()

    let left = maxLen
    let cut = false

    const takeText = s => {
        if (!s || left <= 0) {
            if (s && left <= 0) cut = true
            return ''
        }

        const normalized = normalize(s)
        if (!normalized) return ''

        if (normalized.length <= left) {
            left -= normalized.length
            return normalized
        }

        cut = true
        const part = normalized.slice(0, left)
        left = 0
        return part
    }

    const renderMentionSpan = el => {
        const cls = (el.getAttribute('class') || '')
            .split(/\s+/)
            .filter(Boolean)
            .join(' ')

        const attrs = []
        if (cls) attrs.push(`class="${escapeAttr(cls)}"`)

        const allowedData = ['data-mention', 'data-id', 'data-type']
        allowedData.forEach(name => {
            const val = el.getAttribute(name)
            if (val != null && val !== '') attrs.push(`${name}="${escapeAttr(val)}"`)
        })

        const inner = render(el)
        if (!inner) return ''
        return `<span ${attrs.join(' ')}>${inner}</span>`
    }

    const render = node => {
        if (left <= 0) return ''

        let result = ''

        node.childNodes.forEach(child => {
            if (left <= 0) return

            if (child.nodeType === Node.TEXT_NODE) {
                const t = takeText(child.textContent)
                if (t) {
                    if (result && !result.endsWith(' ') && !t.startsWith(' ')) result += ' '
                    result += t
                }
                return
            }

            if (child.nodeType !== Node.ELEMENT_NODE) {
                result += render(child)
                return
            }

            if (child.tagName === 'BR') {
                if (result && !result.endsWith(' ')) result += ' '
                return
            }

            if (child.tagName === 'P' || child.tagName === 'DIV') {
                const inner = render(child)
                if (inner) {
                    if (result && !result.endsWith(' ')) result += ' '
                    result += inner
                    if (!result.endsWith(' ')) result += ' '
                }
                return
            }

            if (child.tagName === 'A' && ALLOWED.has('A')) {
                const href = child.getAttribute('href')
                const inner = render(child)
                if (!inner) return

                if (href) {
                    result += `<a href="${escapeAttr(href)}" target="_blank">${inner}</a>`
                } else {
                    result += inner
                }
                return
            }

            if (isMentionSpan(child)) {
                const m = renderMentionSpan(child)
                if (m) {
                    if (result && !result.endsWith(' ')) result += ' '
                    result += m
                }
                return
            }

            if (ALLOWED.has(child.tagName)) {
                const tag = child.tagName.toLowerCase()
                const inner = render(child)
                if (!inner) return
                result += `<${tag}>${inner}</${tag}>`
                return
            }

            result += render(child)
        })

        return normalize(result)
    }

    const out = normalize(render(doc.body))
    if (!out) return ''

    return cut ? out + suffix : out
}

export const clearMessageHtml = text => {
    if (!text) return ''

    const ALLOWED = new Set([
        'A',
        'B',
        'STRONG',
        'I',
        'U',
        'S',
        'DEL',
        'STRIKE'
    ])

    const doc = new DOMParser().parseFromString(String(text), 'text/html')

    const escapeAttr = v =>
        String(v)
            .replace(/&/g, '&amp;')
            .replace(/"/g, '&quot')
            .replace(/</g, '&lt')
            .replace(/>/g, '&gt')

    const isMentionSpan = el => {
        if (el.tagName !== 'SPAN') return false
        const cls = el.getAttribute('class') || ''
        return cls.split(/\s+/).includes('mention') || cls.split(/\s+/).includes('user_chat_mention')
    }

    const renderMentionSpan = el => {
        const cls = (el.getAttribute('class') || '')
            .split(/\s+/)
            .filter(Boolean)
            .join(' ')

        const attrs = []
        if (cls) attrs.push(`class="${escapeAttr(cls)}"`)

        const allowedData = ['data-mention', 'data-id', 'data-type']
        allowedData.forEach(name => {
            const val = el.getAttribute(name)
            if (val != null && val !== '') attrs.push(`${name}="${escapeAttr(val)}"`)
        })

        const inner = render(el)
        return `<span ${attrs.join(' ')}>${inner}</span>`
    }

    const render = node => {
        let result = ''

        node.childNodes.forEach(child => {
            if (child.nodeType === Node.TEXT_NODE) {
                result += child.textContent
            } else if (child.nodeType === Node.ELEMENT_NODE) {
                if (child.tagName === 'BR') {
                    result += ' '
                } else if (child.tagName === 'P' || child.tagName === 'DIV') {
                    const inner = render(child)
                    if (inner) result += inner + ' '
                } else if (child.tagName === 'A' && ALLOWED.has('A')) {
                    const href = child.getAttribute('href')
                    if (href) {
                        result += `<a href="${escapeAttr(href)}" target="_blank">${render(child)}</a>`
                    } else {
                        result += render(child)
                    }
                } else if (isMentionSpan(child)) {
                    result += renderMentionSpan(child)
                } else if (ALLOWED.has(child.tagName)) {
                    const tag = child.tagName.toLowerCase()
                    result += `<${tag}>${render(child)}</${tag}>`
                } else {
                    result += render(child)
                }
            } else {
                result += render(child)
            }
        })

        return result
    }

    return render(doc.body)
        .replace(/(\r\n|\n|\r)/g, ' ')
        .replace(/\s+/g, ' ')
        .trim()
}
