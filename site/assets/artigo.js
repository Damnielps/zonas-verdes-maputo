/* Página do artigo: tema claro/escuro (mesma chave do site) e sumário recolhível em telas estreitas. */
(function () {
  var root = document.documentElement;
  var mq = window.matchMedia ? matchMedia("(prefers-color-scheme: dark)") : null;
  function guardado() { try { return localStorage.getItem("zv-tema"); } catch (e) { return null; } }
  function aplica(t) { root.setAttribute("data-theme", t); }
  aplica(guardado() || (mq && mq.matches ? "dark" : "light"));
  var btn = document.getElementById("btnTema");
  if (btn) btn.addEventListener("click", function () {
    var t = root.getAttribute("data-theme") === "dark" ? "light" : "dark";
    aplica(t); try { localStorage.setItem("zv-tema", t); } catch (e) {}
  });
  if (mq) {
    var f = function () { if (!guardado()) aplica(mq.matches ? "dark" : "light"); };
    if (mq.addEventListener) mq.addEventListener("change", f); else if (mq.addListener) mq.addListener(f);
  }
  var sum = document.querySelector("details.sumario");
  if (sum && window.matchMedia && matchMedia("(max-width: 960px)").matches) sum.removeAttribute("open");
})();
