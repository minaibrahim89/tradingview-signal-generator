const fs = require('fs');
const path = require('path');

// Path to the index.html file
const indexPath = path.join(__dirname, 'static', 'index.html');

console.log('Running fix-static-paths.js');
console.log(`Checking for ${indexPath}`);

if (fs.existsSync(indexPath)) {
  console.log('Reading index.html');
  let indexContent = fs.readFileSync(indexPath, 'utf8');
  
  // Fix the paths to include /static/ prefix
  indexContent = indexContent.replace(/src="\/assets\//g, 'src="/static/assets/');
  indexContent = indexContent.replace(/href="\/assets\//g, 'href="/static/assets/');
  indexContent = indexContent.replace(/href="\/favicon.ico"/g, 'href="/static/favicon.ico"');
  
  console.log('Writing updated index.html');
  fs.writeFileSync(indexPath, indexContent);
  console.log('Paths fixed successfully');
} else {
  console.error('Error: index.html not found');
} 