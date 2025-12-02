/**
 * Time utilities for the settings page.
 * 
 * All times are stored and displayed in UTC.
 */

/**
 * Generate time options for the dropdown (every 15 minutes)
 * Returns options in HH:MM format with 12-hour display labels
 */
export function generateTimeOptions(): Array<{ value: string; label: string }> {
    const options: Array<{ value: string; label: string }> = [];

    for (let hour = 0; hour < 24; hour++) {
        for (let minute = 0; minute < 60; minute += 15) {
            const value = `${hour.toString().padStart(2, '0')}:${minute.toString().padStart(2, '0')}`;
            const label = formatTimeFor12Hour(value);
            options.push({ value, label });
        }
    }

    return options;
}

/**
 * Format HH:MM (24-hour) to 12-hour format with AM/PM
 */
export function formatTimeFor12Hour(time: string): string {
    const [hourStr, minuteStr] = time.split(':');
    const hour = parseInt(hourStr, 10);
    const minute = minuteStr || '00';

    if (hour === 0) {
        return `12:${minute} AM`;
    } else if (hour < 12) {
        return `${hour}:${minute} AM`;
    } else if (hour === 12) {
        return `12:${minute} PM`;
    } else {
        return `${hour - 12}:${minute} PM`;
    }
}

/**
 * Round a time string to the nearest 15 minutes
 */
export function roundToNearest15Minutes(time: string): string {
    const [hours, minutes] = time.split(':').map(Number);
    const roundedMinutes = Math.round(minutes / 15) * 15;

    let finalHours = hours;
    let finalMinutes = roundedMinutes;

    if (roundedMinutes === 60) {
        finalMinutes = 0;
        finalHours = (hours + 1) % 24;
    }

    return `${String(finalHours).padStart(2, '0')}:${String(finalMinutes).padStart(2, '0')}`;
}
