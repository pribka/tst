export const handleKeyPress = event => {
    const charCode = event.keyCode || event.which
    const charStr = String.fromCharCode(charCode)
    if (!/^\d$/.test(charStr))
        event.preventDefault()
}

export const decParser = input => {
    const sanitizedInput = input.replace(',', '.')
    const cleanedInput = sanitizedInput.replace(/[^\d.]/g, '')
    const parts = cleanedInput.split('.')
    if (parts.length > 2)
        return parts[0] + '.' + parts[1]
    if (parts[1]?.length > 1)
        parts[1] = parts[1].slice(0, 1)
    return parts.join('.')
}