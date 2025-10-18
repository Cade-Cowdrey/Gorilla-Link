/* ==============================================================
   Gorilla-Link / PSU Connect
   engagement.js — Live Like System (AJAX + Dynamic UI)
   ============================================================== */

document.addEventListener("DOMContentLoaded", () => {
  const likeButtons = document.querySelectorAll("[data-like-btn]");

  likeButtons.forEach((btn) => {
    btn.addEventListener("click", async () => {
      const postId = btn.getAttribute("data-post-id");
      const isLiked = btn.classList.contains("liked");
      const countElement = document.querySelector(
        `[data-like-count="${postId}"]`
      );

      // Provide visual feedback immediately
      btn.disabled = true;

      try {
        const response = await fetch(`/api/${isLiked ? "unlike" : "like"}/${postId}`, {
          method: isLiked ? "DELETE" : "POST",
          headers: {
            "Content-Type": "application/json",
            "X-Requested-With": "XMLHttpRequest",
          },
        });

        if (!response.ok) {
          console.warn("Request failed:", response.status);
          btn.disabled = false;
          return;
        }

        const data = await response.json();

        // Toggle state
        btn.classList.toggle("liked", !isLiked);

        // Update icon (❤️ vs 🤍 or SVG)
        const icon = btn.querySelector("i");
        if (icon) {
          icon.classList.toggle("fa-solid", !isLiked);
          icon.classList.toggle("fa-regular", isLiked);
        } else {
          btn.textContent = !isLiked ? "❤️" : "🤍";
        }

        // Update like count
        if (countElement && data.likes_count !== undefined) {
          countElement.textContent = data.likes_count;
        }
      } catch (err) {
        console.error("Error:", err);
      } finally {
        btn.disabled = false;
      }
    });
  });
});
