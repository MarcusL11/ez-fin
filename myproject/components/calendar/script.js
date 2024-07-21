/* In a file called [project root]/components/calendar/script.js */
(function () {
  if (document.querySelector(".calendar-component")) {
    document.querySelector(".calendar-component").onclick = function () {
      alert("Clicked calendar!");
    };
  }
})();
