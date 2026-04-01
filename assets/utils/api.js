import axios from 'axios';

const api = axios.create({
    
});

// Configure Axios to automatically handle Django's CSRF
api.defaults.xsrfCookieName = 'csrftoken';
api.defaults.xsrfHeaderName = 'X-CSRFToken';

// Optional: If you strictly want to use window.csrfToken instead of cookies
api.interceptors.request.use((config) => {
    const token = window.csrfToken;
    if (token) {
        config.headers['X-CSRFToken'] = token;
    }
    return config;
}, (error) => {
    return Promise.reject(error);
});






export {api};