# Newsfax - Fact Checking Chrome Extension MVP

This is the MVP (Minimum Viable Product) for the Newsfax fact-checking Chrome extension. The extension highlights text in web pages based on the truthfulness of statements and provides interactive popovers with detailed fact-checking information including AI summaries and credible sources.

## 🚀 How to Use

1. **Load the extension** in Chrome (see installation instructions below)
2. **Navigate to any webpage** with news articles or text content
3. **Click the Newsfax extension icon** in your browser toolbar
4. **Wait for analysis** - a loading indicator will appear while the backend processes the page
5. **See highlighted facts** - text will be highlighted in different colors based on truthfulness
6. **Click highlighted text** - view detailed fact-checking information with sources

## Features

- **On-Demand Analysis**: Fact-checking only starts when you click the extension icon
- **Backend Simulation**: Simulates real API calls with loading states and delays
- **Text Highlighting**: Highlights specific text phrases based on fact-checking data
- **Color-coded Truthfulness**: 
  - 🟢 **Green**: TRUE statements
  - 🟡 **Yellow**: SOMEWHAT TRUE statements  
  - 🔴 **Red**: FALSE statements
- **Detailed Popovers**: Click highlighted text for AI summaries and credible sources
- **Interactive Source Icons**: macOS dock-like hover effects for source navigation
- **Clean Scanning Animation**: Bright blue scanning line sweeps vertically down the page during processing
- **Glassmorphism UI**: Modern, beautiful interface with blur effects

## How It Works

1. **Extension Icon Click**: User clicks the Newsfax icon in the browser toolbar
2. **Background Communication**: Background script sends message to content script
3. **Backend Simulation**: Content script makes simulated API call with 2.2s delay
4. **Scanning Animation**: Clean blue scanning line sweeps vertically down the page while processing
5. **Text Analysis**: Script scans page for text matching fact-checking data
6. **Highlighting**: Matching text is wrapped in color-coded spans
7. **Interactive Popovers**: Click highlighted text for detailed information and sources

## Current Implementation

### Dummy Data
The MVP uses a hardcoded list of fact-checking data for demonstration:

```typescript
const DUMMY_FACTS: CheckedFact[] = [
  { text: "climate change", truthfulness: "TRUE" },
  { text: "artificial intelligence", truthfulness: "SOMEWHAT TRUE" },
  { text: "vaccines cause autism", truthfulness: "FALSE" },
  { text: "renewable energy", truthfulness: "TRUE" },
  { text: "unemployment rate", truthfulness: "SOMEWHAT TRUE" },
  { text: "inflation", truthfulness: "SOMEWHAT TRUE" },
  { text: "social media", truthfulness: "SOMEWHAT TRUE" },
  { text: "electric vehicles", truthfulness: "TRUE" }
];
```

### Architecture
- **Types**: Defined in `src/types.ts` with `CheckedFact` interface
- **Content Script**: Main logic in `src/content.tsx` using React
- **Styling**: CSS-based highlighting and popover styles in `src/content.css`
- **Manifest**: Chrome extension configuration in `manifest.json`

## Testing the Extension

### 1. Install and Build
```bash
cd extension
pnpm install
pnpm run dev
```

### 2. Load in Chrome
1. Open Chrome and go to `chrome://extensions/`
2. Enable "Developer mode" in the top right
3. Click "Load unpacked" and select the `extension/dist` folder
4. The extension should appear in your extensions list

### 3. Test with Demo Page
1. Open the `test.html` file in your browser
2. **Click the Newsfax extension icon** in your browser toolbar
3. Watch the bright blue scanning line sweep down the page (2.2 seconds)
4. You should see highlighted text in green, yellow, and red
5. Click on any highlighted text to see the detailed popover
6. Hover over source icons to see the macOS dock effect
7. Click source icons to open URLs in new tabs

### 4. Test on Real Websites
1. Visit any news website (BBC, CNN, etc.)
2. **Click the Newsfax extension icon** to start analysis
3. Watch the bright blue scanning line as the backend processes the content
4. Look for highlighted terms from the fact-checking database

## File Structure

```
extension/
├── src/
│   ├── types.ts          # TypeScript interfaces
│   ├── content.tsx       # Main content script logic
│   ├── content.css       # Styling for highlights and popovers
│   └── ...
├── manifest.json         # Chrome extension manifest
├── test.html            # Test page for demonstration
└── vite.config.ts       # Vite configuration
```

## Technical Implementation Details

### Text Highlighting Algorithm
1. **TreeWalker**: Uses `document.createTreeWalker` to find all text nodes
2. **Filtering**: Skips script, style, and already-highlighted elements
3. **Regex Matching**: Case-insensitive matching of fact-checking terms
4. **DOM Manipulation**: Replaces text nodes with highlighted spans

### Popover Positioning
- Uses `getBoundingClientRect()` for accurate positioning
- Centered horizontally above the clicked element
- Includes a CSS arrow pointing to the highlighted text
- Automatically closes when clicking outside

### Event Handling
- **Click Detection**: Listens for clicks on highlighted elements
- **Data Storage**: Stores fact-checking data in HTML data attributes
- **State Management**: React state for popover visibility and positioning

## Future Enhancements

1. **Backend Integration**: Replace dummy data with real API calls
2. **Performance Optimization**: Debounce highlighting for dynamic content
3. **More Sophisticated Matching**: Handle partial matches and context
4. **User Preferences**: Allow users to customize colors and behavior
5. **Analytics**: Track which facts are being clicked most often

## Development Notes

- The extension uses React with TypeScript for type safety
- CORS is properly configured for development
- CSS is scoped to avoid conflicts with host websites
- The extension is designed to be non-intrusive and performant

## Troubleshooting

- **No Highlights**: Check that the extension is enabled and refresh the page
- **CORS Errors**: Make sure the dev server is running and CORS is configured
- **Popover Not Showing**: Check browser console for JavaScript errors
- **Build Issues**: Ensure all dependencies are installed with `pnpm install` 