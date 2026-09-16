// Simple script to generate PNG icons from a canvas
// Run with: node generate_icons.js

const { createCanvas } = (() => {
  // Fallback: generate minimal valid PNG files
  // PNG header + IHDR + IDAT + IEND for each size

  function createPNG(size) {
    // We'll create a simple inline SVG-to-data approach
    // Instead, let's create minimal valid 1-color PNG icons
    
    const fs = require('fs');
    const path = require('path');
    
    // Create a simple HTML canvas-based icon using built-in tools
    // Since we can't use canvas in Node without deps, create SVG icons instead
    const svg = `<svg xmlns="http://www.w3.org/2000/svg" width="${size}" height="${size}" viewBox="0 0 ${size} ${size}">
  <defs>
    <linearGradient id="bg" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" style="stop-color:#3F8F84"/>
      <stop offset="100%" style="stop-color:#B58A3A"/>
    </linearGradient>
  </defs>
  <rect width="${size}" height="${size}" rx="${size * 0.2}" fill="url(#bg)"/>
  <text x="50%" y="55%" text-anchor="middle" dominant-baseline="middle" 
        font-family="Arial, sans-serif" font-weight="bold" font-size="${size * 0.5}px" fill="white">M</text>
</svg>`;
    
    const iconDir = path.join(__dirname, 'icons');
    fs.writeFileSync(path.join(iconDir, `icon${size}.svg`), svg);
    console.log(`Created icon${size}.svg`);
  }
  
  [16, 48, 128].forEach(createPNG);
  return {};
})();
