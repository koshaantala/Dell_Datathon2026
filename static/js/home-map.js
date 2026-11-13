// Home page map: shows assessed spots; clicking anywhere opens a Stay Report.
"use strict";

document.addEventListener("DOMContentLoaded", async () => {
  const element = document.getElementById("map");
  if (!element || !window.L) return;

  const [lat, lon] = element.dataset.center.split(",").map(Number);
  const map = window.HighGround.createMap(element, { scrollWheelZoom: false });
  map.setView([lat, lon], Number(element.dataset.zoom));

  const openReport = (latlng) => {
    const params = new URLSearchParams({ lat: latlng.lat.toFixed(5), lon: latlng.lng.toFixed(5) });
    window.location.href = `/report?${params}`;
  };

  try {
    const response = await fetch(element.dataset.sitesUrl);
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    const layer = L.geoJSON(await response.json(), {
      style: window.HighGround.tileStyle,
      pointToLayer: (_feature, latlng) => L.circleMarker(latlng, { radius: 6 }),
      onEachFeature: (feature, featureLayer) => {
        featureLayer.bindTooltip(feature.properties.locality);
        featureLayer.on("click", (event) => {
          L.DomEvent.stopPropagation(event);
          window.location.href = `/report?site=${encodeURIComponent(feature.properties.id)}`;
        });
      },
    }).addTo(map);
    map.fitBounds(layer.getBounds(), { padding: [30, 30] });
  } catch (error) {
    console.error("Could not load sites", error);
  }

  map.on("click", (event) => openReport(event.latlng));
});
