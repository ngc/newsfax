# Newsfax - Fact Checking Chrome Extension MVP

This is the MVP (Minimum Viable Product) for the Newsfax fact-checking Chrome extension. The extension highlights text in web pages based on the truthfulness of statements and provides interactive popovers with fact-checking information.

## Features

- **Text Highlighting**: Automatically highlights specific text phrases on web pages based on fact-checking data
- **Color-coded Truthfulness**: 
  - 🟢 **Green**: TRUE statements
  - 🟡 **Yellow**: SOMEWHAT TRUE statements  
  - 🔴 **Red**: FALSE statements
- **Interactive Popovers**: Click on highlighted text to see a popover with truthfulness information
- **Non-intrusive**: The extension doesn't interfere with the normal browsing experience

## How It Works

1. **Content Script Injection**: The extension injects a React-based content script into every web page
2. **Text Analysis**: The script scans the page for text that matches predefined fact-checking data
3. **Highlighting**: Matching text is wrapped in styled spans with appropriate colors
4. **Popover Display**: When users click highlighted text, a popover appears with fact-checking information

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
2. You should see highlighted text in green, yellow, and red
3. Click on any highlighted text to see the popover
4. Test clicking outside the popover to close it

### 4. Test on Real Websites
Visit any news website and look for the highlighted terms. The extension will automatically highlight any matching text from the dummy data.

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