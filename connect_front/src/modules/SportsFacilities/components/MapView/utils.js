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

export function iconCreateFunction(cluster) {
    const markers = cluster.getAllChildMarkers()
    const totalMarkers = markers.length

    return L.divIcon({
        className: 'custom-marker',
        html: `
            <div class="circle-container">
                <div class="circle-text">${totalMarkers}</div>
            </div>
            `,
        iconSize: [40, 40]
    })
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