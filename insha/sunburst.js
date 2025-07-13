d3.csv("bird_migration_data.csv").then(data => {
  // Filter only needed columns
  const filteredData = data.map(d => ({
    Temperature: +d["Temperature_C"] + 273.15,
    Humidity: +d["Humidity_%"],
    MigrationStatus: d["Migration_Success"],
    MigrationReason: d["Migration_Reason"],
    Species: d["Species"],
    Continent: d["Region"],
    Pressure: +d["Pressure_hPa"],
    WindSpeed: +d["Wind_Speed_kmph"],
    Habitat: d["Habitat"],
    WeatherCondition: d["Weather_Condition"]
  }));
console.log("Filtered Data Example:", filteredData.slice(0, 5));
function buildHierarchy(data) {
  const root = { name: "MigrationReasons", children: [] };

  data.forEach(d => {
    const reason = d.MigrationReason;
    const species = d.Species;
    const continent = d.Continent;

    if (!reason || !species || !continent) return;

    // Find or create Reason node
    let reasonNode = root.children.find(r => r.name === reason);
    if (!reasonNode) {
      reasonNode = { name: reason, children: [] };
      root.children.push(reasonNode);
    }

    // Find or create Species node
    let speciesNode = reasonNode.children.find(s => s.name === species);
    if (!speciesNode) {
      speciesNode = { name: species, children: [] };
      reasonNode.children.push(speciesNode);
    }

    // Find or create Continent leaf
    let continentNode = speciesNode.children.find(c => c.name === continent);
    if (!continentNode) {
      continentNode = { name: continent, value: 0 };
      speciesNode.children.push(continentNode);
    }

    // Increment count
    continentNode.value += 1;
  });

  return root;
  
}
const hierarchyData = buildHierarchy(filteredData);
console.log(hierarchyData);
drawSunburst(hierarchyData);


function drawSunburst(data) {
  const width = 600;
  const radius = width / 2;

  const color = d3.scaleOrdinal(d3.quantize(d3.interpolateRainbow, data.children.length + 1));

  const hierarchy = d3.hierarchy(data)
    .sum(d => d.value || 0)
    .sort((a, b) => b.value - a.value);

  const root = d3.partition()
    .size([2 * Math.PI, hierarchy.height + 1])(hierarchy);

  root.each(d => d.current = d); // Save current state for transitions

  // Clean container
  d3.select("#sunburstContainer").selectAll("*").remove();

  const svg = d3.select("#sunburstContainer")
    .append("svg")
    .attr("viewBox", [-width / 2, -width / 2, width, width])
    .style("font", "12px sans-serif");

  const arc = d3.arc()
    .startAngle(d => d.x0)
    .endAngle(d => d.x1)
    .padAngle(d => Math.min((d.x1 - d.x0) / 2, 0.005))
    .padRadius(radius * 1.5)
    .innerRadius(d => d.y0 * radius / root.height)
    .outerRadius(d => Math.max(d.y0 * radius / root.height, d.y1 * radius / root.height - 1));

  const path = svg.append("g")
    .selectAll("path")
    .data(root.descendants().slice(1)) // remove root
    .join("path")
    .attr("fill", d => { while (d.depth > 1) d = d.parent; return color(d.data.name); })
    .attr("fill-opacity", d => arcVisible(d.current) ? (d.children ? 0.6 : 0.4) : 0)
    .attr("pointer-events", d => arcVisible(d.current) ? "auto" : "none")
    .attr("d", d => arc(d.current))
    .on("click", (event, d) => {
  clicked(event, d); // your zoom function (if needed)

  // 🔁 Call other chart update functions here:
  updateHabitatChart(d.data);   // ← implement this
  updateWeatherChart(d.data);   // ← implement this
  updateStoryCard(d.data);      // optional storytelling panel
});


  path.filter(d => d.children).style("cursor", "pointer").on("click", clicked);

  // Tooltip
  const tooltip = d3.select("body").append("div")
    .attr("class", "tooltip")
    .style("opacity", 0);

  path.on("mouseover", function (event, d) {
    tooltip.transition().duration(100).style("opacity", 0.9);
    tooltip.html(`<strong>${d.ancestors().map(d => d.data.name).reverse().join(" → ")}</strong><br/>${d.value} migrations`)
      .style("left", (event.pageX + 10) + "px")
      .style("top", (event.pageY - 20) + "px");
  }).on("mouseout", () => tooltip.transition().duration(200).style("opacity", 0));

  const label = svg.append("g")
    .attr("pointer-events", "none")
    .attr("text-anchor", "middle")
    .style("user-select", "none")
    .selectAll("text")
    .data(root.descendants().slice(1))
    .join("text")
    .attr("dy", "0.35em")
    .attr("fill-opacity", d => +labelVisible(d.current))
    .attr("transform", d => labelTransform(d.current))
    .text(d => d.data.name);

  const parent = svg.append("circle")
    .datum(root)
    .attr("r", radius / root.height)
    .attr("fill", "none")
    .attr("pointer-events", "all")
    .on("click", clicked);

  function clicked(event, p) {
    parent.datum(p.parent || root);

    root.each(d => d.target = {
      x0: Math.max(0, Math.min(1, (d.x0 - p.x0) / (p.x1 - p.x0))) * 2 * Math.PI,
      x1: Math.max(0, Math.min(1, (d.x1 - p.x0) / (p.x1 - p.x0))) * 2 * Math.PI,
      y0: Math.max(0, d.y0 - p.depth),
      y1: Math.max(0, d.y1 - p.depth)
    });

    const t = svg.transition().duration(event.altKey ? 7500 : 750);

    path.transition(t)
      .tween("data", d => {
        const i = d3.interpolate(d.current, d.target);
        return t => d.current = i(t);
      })
      .filter(function (d) {
        return +this.getAttribute("fill-opacity") || arcVisible(d.target);
      })
      .attr("fill-opacity", d => arcVisible(d.target) ? (d.children ? 0.6 : 0.4) : 0)
      .attr("pointer-events", d => arcVisible(d.target) ? "auto" : "none")
      .attrTween("d", d => () => arc(d.current));

    label.filter(function (d) {
      return +this.getAttribute("fill-opacity") || labelVisible(d.target);
    }).transition(t)
      .attr("fill-opacity", d => +labelVisible(d.target))
      .attrTween("transform", d => () => labelTransform(d.current));
  }

  function arcVisible(d) {
    return d.y1 <= 3 && d.y0 >= 1 && d.x1 > d.x0;
  }

  function labelVisible(d) {
    return d.y1 <= 3 && d.y0 >= 1 && (d.y1 - d.y0) * (d.x1 - d.x0) > 0.03;
  }

  function labelTransform(d) {
    const x = (d.x0 + d.x1) / 2 * 180 / Math.PI;
    const y = (d.y0 + d.y1) / 2 * radius / root.height;
    return `rotate(${x - 90}) translate(${y},0) rotate(${x < 180 ? 0 : 180})`;
  }
}
function getFilteredData(nodeData, fullData) {
  const path = nodeData.ancestors().slice(1).map(d => d.data.name); // Skip root
  console.log("Clicked Path:", path); // ✅ Show selection path

  const filtered = fullData.filter(d => {
    if (path.length === 1) {
      return d.MigrationReason === path[0];
    } else if (path.length === 2) {
      return d.MigrationReason === path[0] && d.Species === path[1];
    } else if (path.length === 3) {
      return d.MigrationReason === path[0] && d.Species === path[1] && d.Continent === path[2];
    }
    return false;
  });

  console.log("Filtered Data Count:", filtered.length); // ✅ Show how many records match
  console.log("Sample Filtered Data:", filtered.slice(0, 3)); // Optional: peek at a few

  return filtered;
}



function updateHabitatChart(nodeData) {
  const filtered = getFilteredData(nodeData, filteredData);
  const habitatCounts = d3.rollup(
    filtered,
    v => v.length,
    d => d.Habitat
  );

  const data = Array.from(habitatCounts, ([habitat, count]) => ({ habitat, count }));

  // Render bar chart (or donut/pie) in `#habitatChart` container
  renderBarChart("#habitatChart", data, "Habitat Type", "Number of Migrations");
}
function updateWeatherChart(nodeData) {
  const filtered = getFilteredData(nodeData, filteredData);
  const weatherCounts = d3.rollup(
    filtered,
    v => v.length,
    d => d.Weather
  );

  const data = Array.from(weatherCounts, ([weather, count]) => ({ weather, count }));
  renderBarChart("#weatherChart", data, "Weather", "Frequency");
}


function updateStoryCard(nodeData) {
  const filtered = getFilteredData(nodeData, filteredData);
  const species = nodeData.name;

  const total = filtered.length;
  const mostCommonHabitat = d3.rollups(filtered, v => v.length, d => d.Habitat)
                              .sort((a, b) => b[1] - a[1])[0][0];
  const mostCommonWeather = d3.rollups(filtered, v => v.length, d => d.Weather)
                              .sort((a, b) => b[1] - a[1])[0][0];

  d3.select("#storyCard").html(`
    <h3>${species}</h3>
    <p><strong>Total Migrations:</strong> ${total}</p>
    <p><strong>Common Habitat:</strong> ${mostCommonHabitat}</p>
    <p><strong>Frequent Weather:</strong> ${mostCommonWeather}</p>
  `);
}



});

