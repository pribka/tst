import L from 'leaflet'

export const maxBounds = [
    [56.0, 35.0],
    [39.0, 92.0]
]

export function addDataLazy(targetArray, data, mapFunction = item => item, batchSize = 3, delay = 300) {
    let currentIndex = 0
    const loadNextBatch = () => {
        if (currentIndex >= data.length) return
        const batch = data.slice(currentIndex, currentIndex + batchSize)
        targetArray.push(...batch.map(mapFunction))
        currentIndex += batchSize

        if (currentIndex < data.length)
            setTimeout(loadNextBatch, delay)
    }

    loadNextBatch()
}

export function expandBounds(bounds, margin) {
    const { _southWest, _northEast } = bounds;
    const latDiff = (_northEast.lat - _southWest.lat) * margin;
    const lngDiff = (_northEast.lng - _southWest.lng) * margin;

    return [
        [_southWest.lat - latDiff, _southWest.lng - lngDiff],
        [_northEast.lat + latDiff, _northEast.lng + lngDiff]
    ]
}

export function generateIcon(marker) {
    const { orange, red, white, yellow, total } = marker.summary
    const percentages = [
        { value: orange, color: 'orange' },
        { value: red, color: 'red' },
        { value: white, color: 'white' },
        { value: yellow, color: 'yellow' }
    ].map(segment => ({
        ...segment,
        percentage: (segment.value / total) * 100
    }))
    let offset = 0
    const paths = percentages.map(({ percentage, color }) => {
        const path = `
                <path class="circle ${color}" 
                    stroke-dasharray="${percentage} 100" 
                    stroke-dashoffset="${offset}" 
                    d="M18 2.0845
                    a 15.9155 15.9155 0 0 1 0 31.831
                    a 15.9155 15.9155 0 0 1 0 -31.831" />
                `
        offset -= percentage
        return path
    }).join('')
    return paths
}

export function getMarkerColor(marker) {
    switch (true) {
    case marker.total_value === 0:
        return 'white'
    case marker.total_value >= 1 && marker.total_value <= 2:
        return 'yellow'
    case marker.total_value >= 3 && marker.total_value <= 5:
        return 'orange'
    case marker.total_value > 5:
        return 'red'
    default:
        return ''
    }
}

export function isPointInPolygon(point, polygon) {
    let inside = false
    for (let i = 0, j = polygon.length - 1; i < polygon.length; j = i++) {
        const xi = polygon[i][0], yi = polygon[i][1]
        const xj = polygon[j][0], yj = polygon[j][1]

        const intersect =
        yi > point[0] !== yj > point[0] &&
        point[1] < ((xj - xi) * (point[0] - yi)) / (yj - yi) + xi

        if (intersect) inside = !inside
    }
    return inside
}

export function createClusterIcon(summary) {
    const stats = {
        orange: summary.orange || 0,
        red: summary.red || 0,
        white: summary.white || 0,
        yellow: summary.yellow || 0,
    }
    const totalMarkers = summary.total || 1

    const percentages = [
        { value: stats.orange, color: "orange" },
        { value: stats.red, color: "red" },
        { value: stats.white, color: "white" },
        { value: stats.yellow, color: "yellow" },
    ].map((segment) => ({
        ...segment,
        percentage: (segment.value / totalMarkers) * 100,
    }))

    let offset = 0;
    const paths = percentages
        .map(({ percentage, color }) => {
            const path = `
            <path class="circle ${color}" 
            stroke-dasharray="${percentage} 100" 
            stroke-dashoffset="${offset}" 
            d="M18 2.0845
                a 15.9155 15.9155 0 0 1 0 31.831
                a 15.9155 15.9155 0 0 1 0 -31.831" />
        `;
            offset -= percentage
            return path;
        })
        .join("")

    return L.divIcon({
        className: "custom-marker",
        html: `
        <div class="circle-container">
            <svg viewBox="0 0 36 36" class="circular-chart">
            ${paths}
            </svg>
            <div class="circle-text">${totalMarkers}</div>
        </div>
        `,
        iconSize: [40, 40]
    })
}

export function iconCreateFunction(cluster) {
    const markers = cluster.getAllChildMarkers()
    const stats = markers.reduce(
        (acc, marker) => {
            const totalValue = marker.options.data?.total_value || 0
            if (totalValue === 0) acc.white++
            else if (totalValue <= 2) acc.yellow++
            else if (totalValue <= 5) acc.orange++
            else acc.red++
            return acc
        },
        { orange: 0, red: 0, white: 0, yellow: 0 }
    )

    const totalMarkers = markers.length
    const percentages = [
        { value: stats.orange, color: 'orange' },
        { value: stats.red, color: 'red' },
        { value: stats.white, color: 'white' },
        { value: stats.yellow, color: 'yellow' }
    ].map(segment => ({
        ...segment,
        percentage: (segment.value / totalMarkers) * 100
    }))

    let offset = 0
    const paths = percentages
        .map(({ percentage, color }) => {
            const path = `
                <path class="circle ${color}" 
                stroke-dasharray="${percentage} 100" 
                stroke-dashoffset="${offset}" 
                d="M18 2.0845
                    a 15.9155 15.9155 0 0 1 0 31.831
                    a 15.9155 15.9155 0 0 1 0 -31.831" />
            `
            offset -= percentage
            return path
        })
        .join('')

    return L.divIcon({
        className: 'custom-marker',
        html: `
            <div class="circle-container">
                <svg viewBox="0 0 36 36" class="circular-chart">
                ${paths}
                </svg>
                <div class="circle-text">${totalMarkers}</div>
            </div>
            `,
        iconSize: [40, 40]
    })
}