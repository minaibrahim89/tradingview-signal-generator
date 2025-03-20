/**
 * Simple script to fix static asset paths in built frontend
 */
const fs = require('fs');
const path = require('path');

// Path to the index.html file in the static directory
const indexPath = path.join(__dirname, 'static', 'index.html');

console.log('Running fix-static-paths.js');
console.log(`Checking for ${indexPath}`);

if (fs.existsSync(indexPath)) {
  console.log('Reading index.html');
  let indexContent = fs.readFileSync(indexPath, 'utf8');
  
  // Fix paths to include /static/ prefix for assets
  indexContent = indexContent.replace(/src="\/assets\//g, 'src="/static/assets/');
  indexContent = indexContent.replace(/href="\/assets\//g, 'href="/static/assets/');
  
  // Fix favicon path if present
  indexContent = indexContent.replace(/href="\/favicon.ico"/g, 'href="/static/favicon.ico"');
  
  console.log('Writing updated index.html');
  fs.writeFileSync(indexPath, indexContent);
  console.log('Static paths fixed successfully');
} else {
  console.error('Error: index.html not found in static directory');
  console.log('Current directory:', __dirname);
  
  // Try to create the static directory if it doesn't exist
  const staticDir = path.join(__dirname, 'static');
  if (!fs.existsSync(staticDir)) {
    console.log('Static directory not found, creating it');
    try {
      fs.mkdirSync(staticDir, { recursive: true });
      console.log('Static directory created');
    } catch (err) {
      console.error('Failed to create static directory:', err);
    }
  }
} 