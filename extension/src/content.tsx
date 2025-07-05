import React, { useEffect, useState } from "react";
import { createRoot } from "react-dom/client";
import type { CheckedFact, TruthfulnessType, Source } from "./types";
import "./content.css";

// Dummy data for fact checking
const DUMMY_FACTS: CheckedFact[] = [
  {
    text: "climate change",
    truthfulness: "TRUE",
    summary:
      "Climate change is a well-established scientific fact supported by overwhelming evidence from multiple independent research institutions worldwide.",
    sources: [
      {
        url: "https://www.nasa.gov/climate",
        favicon: "https://www.nasa.gov/favicon.ico",
      },
      {
        url: "https://www.noaa.gov/climate",
        favicon: "https://www.noaa.gov/favicon.ico",
      },
      {
        url: "https://www.ipcc.ch/",
        favicon: "https://www.ipcc.ch/favicon.ico",
      },
    ],
  },
  {
    text: "artificial intelligence",
    truthfulness: "SOMEWHAT TRUE",
    summary:
      "While AI technology is rapidly advancing, claims about its capabilities are often exaggerated or lack proper context about current limitations.",
    sources: [
      {
        url: "https://www.nature.com/",
        favicon: "https://www.nature.com/favicon.ico",
      },
      {
        url: "https://www.sciencemag.org/",
        favicon: "https://www.sciencemag.org/favicon.ico",
      },
      {
        url: "https://www.technologyreview.com/",
        favicon: "https://www.technologyreview.com/favicon.ico",
      },
    ],
  },
  {
    text: "vaccines cause autism",
    truthfulness: "FALSE",
    summary:
      "This claim has been thoroughly debunked by numerous large-scale studies. No credible scientific evidence supports any link between vaccines and autism.",
    sources: [
      {
        url: "https://www.cdc.gov/",
        favicon: "https://www.cdc.gov/favicon.ico",
      },
      {
        url: "https://www.who.int/",
        favicon: "https://www.who.int/favicon.ico",
      },
      {
        url: "https://www.nejm.org/",
        favicon: "https://www.nejm.org/favicon.ico",
      },
    ],
  },
  {
    text: "renewable energy",
    truthfulness: "TRUE",
    summary:
      "Renewable energy technologies are proven, cost-effective, and increasingly competitive with fossil fuels according to industry data.",
    sources: [
      {
        url: "https://www.iea.org/",
        favicon: "https://www.iea.org/favicon.ico",
      },
      {
        url: "https://www.irena.org/",
        favicon: "https://www.irena.org/favicon.ico",
      },
      {
        url: "https://www.energy.gov/",
        favicon: "https://www.energy.gov/favicon.ico",
      },
    ],
  },
  {
    text: "unemployment rate",
    truthfulness: "SOMEWHAT TRUE",
    summary:
      "Unemployment statistics are generally accurate but may not capture underemployment or discouraged workers, requiring careful interpretation.",
    sources: [
      {
        url: "https://www.bls.gov/",
        favicon: "https://www.bls.gov/favicon.ico",
      },
      {
        url: "https://www.federalreserve.gov/",
        favicon: "https://www.federalreserve.gov/favicon.ico",
      },
    ],
  },
  {
    text: "inflation",
    truthfulness: "SOMEWHAT TRUE",
    summary:
      "Inflation data is generally reliable but interpretation depends on methodology and time frame. Different measures may show varying trends.",
    sources: [
      {
        url: "https://www.federalreserve.gov/",
        favicon: "https://www.federalreserve.gov/favicon.ico",
      },
      {
        url: "https://www.bls.gov/",
        favicon: "https://www.bls.gov/favicon.ico",
      },
    ],
  },
  {
    text: "social media",
    truthfulness: "SOMEWHAT TRUE",
    summary:
      "Claims about social media impacts are often mixed - some effects are well-documented while others are still being researched.",
    sources: [
      {
        url: "https://www.pewresearch.org/",
        favicon: "https://www.pewresearch.org/favicon.ico",
      },
      {
        url: "https://www.apa.org/",
        favicon: "https://www.apa.org/favicon.ico",
      },
    ],
  },
  {
    text: "electric vehicles",
    truthfulness: "TRUE",
    summary:
      "Electric vehicles are a proven technology with clear environmental benefits and rapidly improving performance metrics.",
    sources: [
      {
        url: "https://www.epa.gov/",
        favicon: "https://www.epa.gov/favicon.ico",
      },
      {
        url: "https://www.energy.gov/",
        favicon: "https://www.energy.gov/favicon.ico",
      },
      {
        url: "https://www.iea.org/",
        favicon: "https://www.iea.org/favicon.ico",
      },
    ],
  },
];

interface PopoverState {
  isVisible: boolean;
  isClosing: boolean;
  x: number;
  y: number;
  fact: CheckedFact | null;
  arrowOffset: number;
  showBelow: boolean;
}

const FactChecker: React.FC = () => {
  const [popover, setPopover] = useState<PopoverState>({
    isVisible: false,
    isClosing: false,
    x: 0,
    y: 0,
    fact: null,
    arrowOffset: 0,
    showBelow: false,
  });

  const [hoveredSourceIndex, setHoveredSourceIndex] = useState<number | null>(
    null
  );

  const handleSourceClick = (source: Source) => {
    window.open(source.url, "_blank", "noopener,noreferrer");
  };

  const getTruthfulnessClass = (truthfulness: TruthfulnessType): string => {
    switch (truthfulness) {
      case "TRUE":
        return "true";
      case "FALSE":
        return "false";
      case "SOMEWHAT TRUE":
        return "somewhat-true";
      default:
        return "";
    }
  };

  const getTruthfulnessLabel = (truthfulness: TruthfulnessType): string => {
    switch (truthfulness) {
      case "TRUE":
        return "True";
      case "FALSE":
        return "False";
      case "SOMEWHAT TRUE":
        return "Somewhat True";
      default:
        return "";
    }
  };

  const highlightText = () => {
    // Get all text nodes in the document
    const walker = document.createTreeWalker(
      document.body,
      NodeFilter.SHOW_TEXT,
      {
        acceptNode: (node) => {
          // Skip script and style elements
          const parent = node.parentElement;
          if (!parent) return NodeFilter.FILTER_REJECT;

          const tagName = parent.tagName.toLowerCase();
          if (["script", "style", "noscript", "textarea"].includes(tagName)) {
            return NodeFilter.FILTER_REJECT;
          }

          // Skip already highlighted text
          if (parent.classList.contains("newsfax-highlight")) {
            return NodeFilter.FILTER_REJECT;
          }

          return NodeFilter.FILTER_ACCEPT;
        },
      }
    );

    const textNodes: Text[] = [];
    let node;
    while ((node = walker.nextNode())) {
      textNodes.push(node as Text);
    }

    // Process each fact
    DUMMY_FACTS.forEach((fact) => {
      const regex = new RegExp(fact.text, "gi");

      textNodes.forEach((textNode) => {
        const text = textNode.textContent;
        if (!text) return;

        const matches = text.match(regex);
        if (!matches) return;

        // Create a temporary div to hold the HTML
        const tempDiv = document.createElement("div");
        tempDiv.innerHTML = text.replace(regex, (match) => {
          const className = getTruthfulnessClass(fact.truthfulness);
          return `<span class="newsfax-highlight ${className}" data-fact="${encodeURIComponent(
            JSON.stringify(fact)
          )}">${match}</span>`;
        });

        // Replace the text node with the new HTML
        const fragment = document.createDocumentFragment();
        while (tempDiv.firstChild) {
          fragment.appendChild(tempDiv.firstChild);
        }

        textNode.parentNode?.replaceChild(fragment, textNode);
      });
    });
  };

  const handleHighlightClick = (event: MouseEvent) => {
    const target = event.target as HTMLElement;
    if (!target.classList.contains("newsfax-highlight")) return;

    event.preventDefault();
    event.stopPropagation();

    const factData = target.getAttribute("data-fact");
    if (!factData) return;

    try {
      const fact = JSON.parse(decodeURIComponent(factData)) as CheckedFact;
      const rect = target.getBoundingClientRect();

      // Use exact click position
      const clickX = event.clientX;
      const clickY = event.clientY;
      let x = clickX;
      let y = clickY - 10;
      let showBelow = false;

      // Ensure popover stays within viewport
      const popoverWidth = 350; // max-width from CSS
      const popoverHeight = 150; // approximate height with summary and sources

      // Adjust horizontal position if it would go off-screen
      if (x - popoverWidth / 2 < 10) {
        x = popoverWidth / 2 + 10;
      } else if (x + popoverWidth / 2 > window.innerWidth - 10) {
        x = window.innerWidth - popoverWidth / 2 - 10;
      }

      // Adjust vertical position if it would go off-screen
      if (y - popoverHeight < 10) {
        y = clickY + 25; // Show below click position instead
        showBelow = true;
      }

      // Calculate arrow position relative to the popover
      const arrowOffset = clickX - x;

      setPopover({
        isVisible: true,
        isClosing: false,
        x,
        y,
        fact,
        arrowOffset,
        showBelow,
      });
    } catch (error) {
      console.error("Error parsing fact data:", error);
    }
  };

  const handleDocumentClick = (event: MouseEvent) => {
    const target = event.target as HTMLElement;
    if (
      !target.closest(".newsfax-popover") &&
      !target.classList.contains("newsfax-highlight")
    ) {
      // Start fade-out animation
      setPopover((prev) => ({ ...prev, isClosing: true }));

      // Hide popover after animation completes
      setTimeout(() => {
        setPopover((prev) => ({ ...prev, isVisible: false, isClosing: false }));
      }, 150); // Match the fade-out animation duration
    }
  };

  useEffect(() => {
    // Wait for the page to load before highlighting
    const timer = setTimeout(() => {
      highlightText();
    }, 1000);

    // Add event listeners
    document.addEventListener("click", handleHighlightClick);
    document.addEventListener("click", handleDocumentClick);

    return () => {
      clearTimeout(timer);
      document.removeEventListener("click", handleHighlightClick);
      document.removeEventListener("click", handleDocumentClick);
    };
  }, []);

  return (
    <>
      {popover.isVisible && popover.fact && (
        <div
          className={`newsfax-popover ${getTruthfulnessClass(
            popover.fact.truthfulness
          )} ${popover.isClosing ? "fade-out" : ""} ${
            popover.showBelow ? "show-below" : ""
          }`}
          style={{
            left: popover.x,
            top: popover.y,
          }}
        >
          <div className="newsfax-popover-header">
            {getTruthfulnessLabel(popover.fact.truthfulness)}
          </div>
          <div className="newsfax-popover-summary">{popover.fact.summary}</div>
          <div className="newsfax-popover-sources">
            <div className="sources-label">Sources:</div>
            <div className="sources-dock">
              {popover.fact.sources.map((source, index) => (
                <div
                  key={index}
                  className="source-icon"
                  style={{
                    transform: `scale(${
                      hoveredSourceIndex === index ? 1.3 : 1
                    }) translateY(${hoveredSourceIndex === index ? -4 : 0}px)`,
                    zIndex: hoveredSourceIndex === index ? 10 : 1,
                  }}
                  onMouseEnter={() => setHoveredSourceIndex(index)}
                  onMouseLeave={() => setHoveredSourceIndex(null)}
                  onClick={() => handleSourceClick(source)}
                >
                  <img
                    src={source.favicon}
                    alt={`Source ${index + 1}`}
                    onError={(e) => {
                      (e.target as HTMLImageElement).src =
                        "data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMTYiIGhlaWdodD0iMTYiIHZpZXdCb3g9IjAgMCAxNiAxNiIgZmlsbD0ibm9uZSIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj4KPHBhdGggZD0iTTggMTVBNyA3IDAgMSAxIDggMUE3IDcgMCAwIDEgOCAxNVoiIGZpbGw9IiM4ODg4ODgiLz4KPHBhdGggZD0iTTcuNSA0VjhINS41TDggMTEuNUwxMC41IDhIOC41VjRINy41WiIgZmlsbD0iI0ZGRkZGRiIvPgo8L3N2Zz4K";
                    }}
                  />
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
    </>
  );
};

// Create a container for the React app
const container = document.createElement("div");
container.id = "newsfax-fact-checker";
container.style.position = "fixed";
container.style.top = "0";
container.style.left = "0";
container.style.width = "100%";
container.style.height = "100%";
container.style.pointerEvents = "none";
container.style.zIndex = "999999";

// Make sure popovers can be interacted with
container.style.setProperty("pointer-events", "none");
const style = document.createElement("style");
style.textContent = `
  #newsfax-fact-checker .newsfax-popover {
    pointer-events: auto;
  }
`;
document.head.appendChild(style);

document.body.appendChild(container);

// Render the React component
const root = createRoot(container);
root.render(<FactChecker />);
