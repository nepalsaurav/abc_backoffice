import path from 'path';

export default function getInputs(rootDir) {
    return {
        'portfolio_snapshot/portfolio_dashboard/main': path.resolve(rootDir, 'portfolio_snapshot/dashboard_frontend/main.js')
    };
}
