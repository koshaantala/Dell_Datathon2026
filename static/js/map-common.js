// Shared map helpers. Map settings come from data-* attributes set in the templates,
// which read them from content/site.en.yaml (the `map:` section).
"use strict";

window.HighGround = window.HighGround || {};

window.HighGround.createMap = function createMap(element, options = {}) {
  const map = L.map(element, { scrollWheelZoom: options.scrollWheelZoom ?? true });
  L.tileLayer(element.dataset.tileUrl, {
    maxZoom: 19,
    attribution: element.dataset.attribution,
  }).addTo(map);
  return map;
};

window.HighGround.tileStyle = {
  color: "#c2410c",
  weight: 2,
  fillColor: "#c2410c",
  fillOpacity: 0.25,
};
