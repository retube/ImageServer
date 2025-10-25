/**
 * Fetch current weather data from Open-Meteo for the given coordinates.
 *
 * @param {number} lat - Latitude
 * @param {number} lon - Longitude
 * @returns {Promise<Object>} - Parsed JSON weather response
 */
export async function getCurrentWeather(lat, lon) {
  const params = new URLSearchParams({
    latitude: lat,
    longitude: lon,
    current: ['temperature_2m', 'wind_speed_10m', 'is_day', 'weather_code'].join(','),
    timezone: 'auto'
  });

  const url = `https://api.open-meteo.com/v1/forecast?${params.toString()}`;

  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), 8000);

  try {
    const response = await fetch(url, { signal: controller.signal });
    if (!response.ok) {
      throw new Error(`Weather fetch failed: HTTP ${response.status}`);
    }
    return await response.json();
  } finally {
    clearTimeout(timeout);
  }
}
