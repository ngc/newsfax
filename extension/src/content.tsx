import React, { useEffect, useState } from "react";
import { createRoot } from "react-dom/client";
import type { CheckedFact, TruthfulnessType, Source } from "./types";
import "./content.css";

// Declare chrome global for TypeScript
declare global {
  interface Window {
    chrome: any;
  }
  const chrome: any;
}

// Real API call to backend with minimum loading time
const fetchFactCheckingData = async (): Promise<CheckedFact[]> => {
  const currentUrl = window.location.href;
  const apiUrl = "http://localhost:8000/factcheck";
  const minLoadingTime = 3000; // 3 seconds minimum loading time

  // Start timing
  const startTime = Date.now();

  try {
    // Make the API call
    const apiCall = async (): Promise<CheckedFact[]> => {
      // Make the initial request
      const response = await fetch(apiUrl, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ url: currentUrl }),
      });

      if (response.status === 200) {
        // Fact checking is already complete
        return await response.json();
      } else if (response.status === 202) {
        // Fact checking is starting/in progress, need to poll
        console.log("Fact checking started, polling for completion...");

        // Poll every 1 second until completion
        return new Promise((resolve, reject) => {
          const pollInterval = setInterval(async () => {
            try {
              const pollResponse = await fetch(apiUrl, {
                method: "POST",
                headers: {
                  "Content-Type": "application/json",
                },
                body: JSON.stringify({ url: currentUrl }),
              });

              if (pollResponse.status === 200) {
                clearInterval(pollInterval);
                const facts = await pollResponse.json();
                resolve(facts);
              } else if (pollResponse.status === 202) {
                // Still processing, continue polling
                console.log("Still processing...");
              } else {
                clearInterval(pollInterval);
                reject(new Error(`API error: ${pollResponse.status}`));
              }
            } catch (error) {
              clearInterval(pollInterval);
              reject(error);
            }
          }, 1000);
        });
      } else {
        throw new Error(`API error: ${response.status}`);
      }
    };

    // Execute the API call
    const facts = await apiCall();

    // Calculate how much time has passed
    const elapsedTime = Date.now() - startTime;
    const remainingTime = Math.max(0, minLoadingTime - elapsedTime);

    // If less than 3 seconds have passed, wait for the remaining time
    if (remainingTime > 0) {
      console.log(
        `Waiting ${remainingTime}ms more for minimum loading time...`
      );
      await new Promise((resolve) => setTimeout(resolve, remainingTime));
    }

    return facts;
  } catch (error) {
    console.error("Error fetching fact checking data:", error);

    // Still enforce minimum loading time even on error
    const elapsedTime = Date.now() - startTime;
    const remainingTime = Math.max(0, minLoadingTime - elapsedTime);

    if (remainingTime > 0) {
      await new Promise((resolve) => setTimeout(resolve, remainingTime));
    }

    // Return empty array on error so the extension doesn't break
    return [];
  }
};

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

  const [facts, setFacts] = useState<CheckedFact[]>([]);
  const [isLoading, setIsLoading] = useState(false);

  const handleSourceClick = (source: Source) => {
    window.open(source.url, "_blank", "noopener,noreferrer");
  };

  const startFactChecking = async () => {
    if (isLoading || facts.length > 0) return; // Already loaded or loading

    setIsLoading(true);
    console.log("Starting fact-checking...");

    try {
      const factsData = await fetchFactCheckingData();
      setFacts(factsData);

      // Wait a bit for state to update, then highlight
      setTimeout(() => {
        highlightText(factsData);
        console.log("Fact-checking complete!");
      }, 100);
    } catch (error) {
      console.error("Failed to fetch fact-checking data:", error);
    } finally {
      setIsLoading(false);
    }
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

  const highlightText = (factsData: CheckedFact[]) => {
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
    factsData.forEach((fact: CheckedFact) => {
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
    // Listen for messages from background script
    const messageListener = (message: any) => {
      if (message.action === "START_FACT_CHECKING") {
        startFactChecking();
      }
    };

    // Add message listener
    chrome.runtime.onMessage.addListener(messageListener);

    // Add event listeners
    document.addEventListener("click", handleHighlightClick);
    document.addEventListener("click", handleDocumentClick);

    return () => {
      chrome.runtime.onMessage.removeListener(messageListener);
      document.removeEventListener("click", handleHighlightClick);
      document.removeEventListener("click", handleDocumentClick);
    };
  }, [isLoading, facts]);

  return (
    <>
      {/* Scanning ray animation */}
      {isLoading && (
        <div className="newsfax-scanner-overlay">
          <div className="scanner-ray"></div>
        </div>
      )}

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
