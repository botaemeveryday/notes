document.addEventListener("DOMContentLoaded", () => {
  const highlightBlocks = document.querySelectorAll(".highlight");

  highlightBlocks.forEach((block) => {
    block.style.position = "relative";

    const button = document.createElement("button");
    button.className = "copy-code-btn absolute top-3 right-3 p-2 rounded-lg bg-base-content/10 text-base-content/50 hover:bg-base-content/20 hover:text-base-content transition-all opacity-0 group-hover:opacity-100 backdrop-blur-sm";
    button.setAttribute("aria-label", "Копировать код");
    button.setAttribute("title", "Копировать");
    
    const iconCopy = `<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="9" y="9" width="13" height="13" rx="2" ry="2"></rect><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"></path></svg>`;
    const iconCheck = `<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#10b981" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="20 6 9 17 4 12"></polyline></svg>`;

    button.innerHTML = iconCopy;
    
    block.classList.add("group");
    block.appendChild(button);

    button.addEventListener("click", async () => {
      const codeElement = block.querySelector("code");
      let textToCopy = codeElement.innerText;

      try {
        await navigator.clipboard.writeText(textToCopy);
        
        button.innerHTML = iconCheck;
        button.classList.add("bg-green-500/20", "text-green-500");
        
        setTimeout(() => {
          button.innerHTML = iconCopy;
          button.classList.remove("bg-green-500/20", "text-green-500");
        }, 2000);
      } catch (err) {
        console.error("Ошибка копирования: ", err);
      }
    });
  });
});