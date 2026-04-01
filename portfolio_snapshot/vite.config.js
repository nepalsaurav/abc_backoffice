import path from 'path';

export default function getInputs(rootDir) {
    return {
        'portfolio_snapshot/main': path.resolve(rootDir, 'portfolio_snapshot/frontend/main.js')
    };
}
