// Shared helpers for Charcoal Grill Coach
$(function () {
  // Toast notification system
  window.showToast = function (message, type = "info") {
    type = type || "info"; // default to info

    var toastHtml = `
      <div class="toast align-items-center text-white bg-${type} border-0" role="alert" aria-live="assertive" aria-atomic="true">
        <div class="d-flex">
          <div class="toast-body">
            ${message}
          </div>
          <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast" aria-label="Close"></button>
        </div>
      </div>
    `;

    var toastContainer = document.getElementById("toast-container");
    if (!toastContainer) {
      toastContainer = document.createElement("div");
      toastContainer.id = "toast-container";
      toastContainer.setAttribute("aria-live", "polite");
      toastContainer.setAttribute("aria-atomic", "true");
      toastContainer.style.position = "fixed";
      toastContainer.style.top = "20px";
      toastContainer.style.right = "20px";
      toastContainer.style.zIndex = "1050";
      document.body.appendChild(toastContainer);
    }

    var tempDiv = document.createElement("div");
    tempDiv.innerHTML = toastHtml;
    var toastElement = tempDiv.firstChild;
    toastContainer.appendChild(toastElement);

    var toast = new bootstrap.Toast(toastElement);
    toast.show();

    // Remove element after toast is hidden
    toastElement.addEventListener("hidden.bs.toast", function () {
      toastElement.remove();
    });
  };

  // Utility: Debounce API calls to prevent duplicate submissions
  window.debounceAPI = function (fn, delay = 300) {
    let timeoutId;
    return function (...args) {
      clearTimeout(timeoutId);
      timeoutId = setTimeout(() => fn(...args), delay);
    };
  };

  // Smooth page transitions
  $(document).on("click", 'a[href^="/"]', function (e) {
    var href = $(this).attr("href");
    // Don't apply transition to API calls
    if (href.includes("/api/")) return;
  });
});
