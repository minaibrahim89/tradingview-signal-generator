const fs = require('fs');
const path = require('path');
const { execSync } = require('child_process');

console.log('Environment Check for Email Forwarder UI');
console.log('=======================================\n');

// Check Node.js version
console.log('Node.js version:', process.version);
console.log('npm version:', execSync('npm -v').toString().trim());

// Check if frontend directory exists
const frontendDir = path.join(__dirname, 'frontend');
console.log(`\nChecking frontend directory: ${frontendDir}`);
if (fs.existsSync(frontendDir)) {
    console.log('✅ Frontend directory exists');

    // Check if package.json exists
    const pkgJsonPath = path.join(frontendDir, 'package.json');
    if (fs.existsSync(pkgJsonPath)) {
        console.log('✅ package.json exists');

        // Check package.json content
        try {
            const pkgJson = require(pkgJsonPath);
            console.log('Dependencies:');
            console.log('- vite:', pkgJson.devDependencies.vite || 'Not found');
            console.log('- react:', pkgJson.dependencies.react || 'Not found');
        } catch (err) {
            console.log('❌ Error reading package.json:', err.message);
        }

        // Check if node_modules exists
        const nodeModulesPath = path.join(frontendDir, 'node_modules');
        if (fs.existsSync(nodeModulesPath)) {
            console.log('✅ node_modules directory exists');

            // Check if vite is installed
            const vitePath = path.join(nodeModulesPath, 'vite');
            if (fs.existsSync(vitePath)) {
                console.log('✅ vite is installed');
            } else {
                console.log('❌ vite is NOT installed in node_modules');
            }
        } else {
            console.log('❌ node_modules directory does NOT exist. Need to run npm install');
        }

        // Check vite.config.js
        const viteConfigPath = path.join(frontendDir, 'vite.config.js');
        if (fs.existsSync(viteConfigPath)) {
            console.log('✅ vite.config.js exists');
            console.log('\nContent of vite.config.js:');
            console.log(fs.readFileSync(viteConfigPath, 'utf8'));
        } else {
            console.log('❌ vite.config.js does NOT exist');
        }
    } else {
        console.log('❌ package.json does NOT exist');
    }
} else {
    console.log('❌ Frontend directory does NOT exist');
}

console.log('\n\nRecommended fix steps:');
console.log('1. cd email_forwarder/frontend');
console.log('2. rm -rf node_modules package-lock.json');
console.log('3. npm install');
console.log('4. npm run dev'); 