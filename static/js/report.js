// Stay Report: draws the small map, then fills the AI summary and live data.
// All wording comes from data-* attributes rendered from content/site.*.yaml.
"use strict";

async function getJson(url) {
  const response = await fetch(url);
  if (!response.ok) throw new Error(`HTTP ${response.status}`);
  return response.json();
}

function fill(template, values) {
  return template.replace(/\{(\w+)\}/g, (_match, key) => values[key] ?? "");
}

function drawSiteMap() {
  const element = document.getElementById("site-map");
  if (!element || !window.L) return;
  const map = window.HighGround.createMap(element, { scrollWheelZoom: false });
  const bounds = element.dataset.bounds;
  if (bounds) {
    const [west, south, east, north] = bounds.split(",").map(Number);
    const box = L.rectangle([[south, west], [north, east]], window.HighGround.tileStyle).addTo(map);
    map.fitBounds(box.getBounds(), { maxZoom: 16, padding: [40, 40] });
  } else {
    const point = [Number(element.dataset.lat), Number(element.dataset.lon)];
    L.circleMarker(point).addTo(map);
    map.setView(point, 15);
  }
}

async function loadSummary(siteId, lang) {
  const element = document.getElementById("summary");
  if (!element) return;
  element.classList.add("is-loading");
  try {
    const data = await getJson(`/api/summary?site=${encodeURIComponent(siteId)}&lang=${lang}`);
    element.textContent = data.summary;
    element.dataset.source = data.source;
  } catch (error) {
    console.warn("Summary unavailable; keeping the template text", error);
  } finally {
    element.classList.remove("is-loading");
  }
}

async function loadLive(siteId) {
  const section = document.getElementById("live");
  if (!section) return;
  const status = section.querySelector(".live-status");
  const list = section.querySelector(".live-alerts");
  section.hidden = false;
  try {
    const data = await getJson(`/api/live?site=${encodeURIComponent(siteId)}`);
    if (data.alerts === null && data.gauge === null) throw new Error("No live data");
    const lines = [];
    if (data.gauge) {
      lines.push(fill(status.dataset.gaugeTemplate, {
        gauge_name: status.dataset.gaugeName,
        value: data.gauge.value.toFixed(2),
        unit: data.gauge.unit,
        time: new Date(data.gauge.time).toLocaleString(),
      }));
    }
    if (data.alerts && data.alerts.length === 0) lines.push(status.dataset.noAlerts);
    status.textContent = lines.join(" ");
    for (const alert of data.alerts || []) {
      const item = document.createElement("li");
      item.textContent = alert.headline || alert.event;
      list.appendChild(item);
    }
  } catch (error) {
    status.textContent = status.dataset.unavailable;
  }
}

document.addEventListener("DOMContentLoaded", () => {
  const report = document.querySelector(".report");
  if (!report) return;
  drawSiteMap();
  loadSummary(report.dataset.site, report.dataset.lang);
  if (report.dataset.liveEnabled === "true") loadLive(report.dataset.site);
});
