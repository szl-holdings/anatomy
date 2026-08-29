/* Thin YACHAY overlay — points at the Second Brain Space.
 * Additive HUD only. Not a Three.js rewrite. 0-CDN. Handles-only SOFTWARE.
 * Private 9464-node graph is not here. Λ = Conjecture 1.
 */
(function (root) {
  "use strict";
  var SPACE = "https://huggingface.co/spaces/SZLHOLDINGS/second-brain";
  var GH = "https://github.com/szl-holdings/szl-second-brain";
  var css = [
    "#yachay-sb{position:fixed;z-index:22;right:12px;bottom:12px;max-width:min(340px,92vw);",
    "font-family:ui-monospace,Consolas,monospace;font-size:11px;line-height:1.45;",
    "color:#eef3f6;background:rgba(8,11,20,.88);border:1px solid rgba(58,244,200,.35);",
    "border-radius:12px;padding:10px 12px;pointer-events:auto;backdrop-filter:blur(6px)}",
    "#yachay-sb b{color:#3af4c8}#yachay-sb a{color:#3af4c8;text-decoration:none}",
    "#yachay-sb .dim{color:#8aa0b3;margin-top:6px}"
  ].join("");
  var style = document.createElement("style");
  style.textContent = css;
  document.head.appendChild(style);
  var box = document.createElement("aside");
  box.id = "yachay-sb";
  box.setAttribute("aria-label", "YACHAY second brain note");
  box.innerHTML =
    "<div><b>YACHAY · Second Brain</b></div>" +
    "<div>Read-only cortex overlay. SOFTWARE handles-only retrieval over the public 575-chunk projection.</div>" +
    "<div><a href=\"" + SPACE + "\">Space SZLHOLDINGS/second-brain</a> · " +
    "<a href=\"" + GH + "\">GitHub</a></div>" +
    "<div class=\"dim\">Not weights. Not the 3D atlas. Not the private 9464-node graph. " +
    "Does not overwrite SZL-Khipu-1.5B-BrainNavigator (abstain 2/6). Λ = Conjecture 1.</div>";
  function mount() {
    if (!document.body) return;
    if (!document.getElementById("yachay-sb")) document.body.appendChild(box);
  }
  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", mount);
  } else {
    mount();
  }
  root.SZL_YACHAY_SECOND_BRAIN = { space: SPACE, github: GH, kind: "SOFTWARE" };
})(typeof window !== "undefined" ? window : this);
