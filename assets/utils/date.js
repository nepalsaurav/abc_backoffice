export const formatDate = (iso) => {
    if (!iso) return "Never";
    return new Date(iso).toLocaleString('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit',
        hour12: true
    });
};