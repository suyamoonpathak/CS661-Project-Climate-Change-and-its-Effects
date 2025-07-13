document.addEventListener("DOMContentLoaded", function () {

  d3.csv("bird_migration_data.csv").then(data => {
    // Preprocess
    const filteredData = data.map(d => ({
      Temperature: +d["Temperature_C"] + 273.15,
      Humidity: +d["Humidity_%"],
      MigrationStatus: d["Migration_Success"],
      Species: d["Species"],
      Continent: d["Region"],
      Pressure: +d["Pressure_hPa"],
      WindSpeed: +d["Wind_Speed_kmph"],
      Migration_Start_Month: +d["Migration_Start_Month"],
      Migration_End_Month: +d["Migration_End_Month"]
    }));

    // Dropdowns
    const speciesList = Array.from(new Set(filteredData.map(d => d.Species))).sort();
    const continentList = Array.from(new Set(filteredData.map(d => d.Continent))).sort();

    d3.select("#speciesDropdown")
      .selectAll("option")
      .data(["All"].concat(speciesList))
      .enter()
      .append("option")
      .text(d => d);

    d3.select("#continentDropdown")
      .selectAll("option")
      .data(["All"].concat(continentList))
      .enter()
      .append("option")
      .text(d => d);

    // Set default axis values
    document.getElementById("xAxisSelect").value = "Temperature";
    document.getElementById("yAxisSelect").value = "Humidity";

    // SVG Setup
    const width = 600, height = 500;
    const margin = { top: 30, right: 30, bottom: 90, left: 60 };
    const svg = d3.select("#heatmapContainer")
      .append("svg")
      .attr("width", width + margin.left + margin.right)
      .attr("height", height + margin.top + margin.bottom + 50)
      .append("g")
      .attr("transform", `translate(${margin.left},${margin.top})`);

    // Tooltip
    const tooltip = d3.select("body")
      .append("div")
      .attr("class", "tooltip")
      .style("opacity", 0);

    // Define gradient and legend container
    const defs = svg.append("defs");
    const linearGradient = defs.append("linearGradient")
      .attr("id", "legend-gradient")
      .attr("x1", "0%").attr("y1", "0%")
      .attr("x2", "100%").attr("y2", "0%");

    const legendWidth = 300;  // increase from 200 → 300 or more
const legendHeight = 30;  // increase from 20 → 30 for thicker bar

    const legendSvg = svg.append("g")
      .attr("class", "legend")
      .attr("transform", `translate(${(width - legendWidth) / 2}, ${height + 40})`);

    // Get binned data
    function getBinnedData() {
      const selectedSpecies = d3.select("#speciesDropdown").property("value");
      const selectedContinent = d3.select("#continentDropdown").property("value");
      const xAxis = d3.select("#xAxisSelect").property("value");
      const yAxis = d3.select("#yAxisSelect").property("value");

      const binSize = 5;
      const binCounts = new Map();

      filteredData.forEach(d => {
        if (
          (selectedSpecies === "All" || d.Species === selectedSpecies) &&
          (selectedContinent === "All" || d.Continent === selectedContinent)
        ) {
          if (isNaN(d[xAxis]) || isNaN(d[yAxis])) return;

          const xBin = Math.floor(d[xAxis] / binSize) * binSize;
          const yBin = Math.floor(d[yAxis] / binSize) * binSize;
          const key = `${xBin}-${yBin}`;

          if (!binCounts.has(key)) {
            binCounts.set(key, { Success: 0, XBin: xBin, YBin: yBin });
          }

          if (d.MigrationStatus === "Successful") {
            binCounts.get(key).Success += 1;
          }
        }
      });

      return Array.from(binCounts.values());
    }

    // Draw heatmap and legend
    function updateHeatmap() {
      svg.selectAll("g.axis").remove();
      svg.selectAll("text.label").remove();
      svg.selectAll("rect.cell").remove();
      legendSvg.selectAll("*").remove();

      const binnedData = getBinnedData();
      const xBins = Array.from(new Set(binnedData.map(d => d.XBin))).sort((a, b) => a - b);
      const yBins = Array.from(new Set(binnedData.map(d => d.YBin))).sort((a, b) => a - b);

      const axisUnits = {
        Temperature: "Temperature (K)",
        Humidity: "Humidity (%)",
        Pressure: "Pressure (hPa)",
        WindSpeed: "Wind Speed (km/h)",
      };

      const xAxisLabel = d3.select("#xAxisSelect").property("value");
      const yAxisLabel = d3.select("#yAxisSelect").property("value");
      const xLabelText = axisUnits[xAxisLabel] || xAxisLabel;
      const yLabelText = axisUnits[yAxisLabel] || yAxisLabel;

      const xScale = d3.scaleBand().domain(xBins).range([0, width]).padding(0.05);
      const yScale = d3.scaleBand().domain(yBins).range([height, 0]).padding(0.05);
      const maxSuccess = d3.max(binnedData, d => d.Success);
      const colorScale = d3.scaleSequential()
        .domain([0, maxSuccess || 1])
        .interpolator(d3.interpolateMagma);

      // Draw axis labels
      svg.append("text")
        .attr("class", "label")
        .attr("x", width / 2)
        .attr("y", height + 35)
        .attr("text-anchor", "middle")
        .style("font-size", "18px")
        .style("font-family", "Courier New")
        .text(xLabelText);

      svg.append("text")
        .attr("class", "label")
        .attr("transform", "rotate(-90)")
        .attr("x", -height / 2)
        .attr("y", -45)
        .attr("text-anchor", "middle")
        .style("font-size", "18px")
        .style("font-family", "Courier New")
        .text(yLabelText);

      svg.append("g")
        .attr("class", "axis")
        .attr("transform", `translate(0, ${height})`)
        .call(d3.axisBottom(xScale).tickSize(0))
        .selectAll("text")
        .style("font-family", "Courier New")
        .style("font-size", "11px");

      svg.append("g")
        .attr("class", "axis")
        .call(d3.axisLeft(yScale).tickSize(0))
        .selectAll("text")
        .style("font-family", "Courier New")
        .style("font-size", "11px");

      // Draw cells
      svg.selectAll("rect.cell")
        .data(binnedData)
        .enter()
        .append("rect")
        .attr("class", "cell")
        .attr("x", d => xScale(d.XBin))
        .attr("y", d => yScale(d.YBin))
        .attr("width", xScale.bandwidth())
        .attr("height", yScale.bandwidth())
        .style("fill", d => colorScale(d.Success))
        .on("mouseover", function (event, d) {
          d3.select(this).style("stroke", "#000").style("stroke-width", 2);
          tooltip.transition().style("opacity", 1);
          tooltip
            .html(`${xAxisLabel}: ${d.XBin}<br>${yAxisLabel}: ${d.YBin}<br>Successes: ${d.Success}`)
            .style("left", (event.pageX + 10) + "px")
            .style("top", (event.pageY - 10) + "px");
        })
        .on("mouseout", function () {
          d3.select(this).style("stroke", "none");
          tooltip.transition().style("opacity", 0);
        });

      // Update gradient
      linearGradient.selectAll("stop").remove();
      linearGradient.append("stop").attr("offset", "0%").attr("stop-color", colorScale(0));
      linearGradient.append("stop").attr("offset", "100%").attr("stop-color", colorScale(maxSuccess || 1));

      // Color bar
      legendSvg.append("rect")
        .attr("width", legendWidth)
        .attr("height", legendHeight)
        .style("fill", "url(#legend-gradient)")
        .style("stroke", "#333");

      // Legend axis
      const legendScale = d3.scaleLinear()
        .domain([0, maxSuccess || 1])
        .range([0, legendWidth]);

      const legendAxis = d3.axisBottom(legendScale)
        .ticks(5)
        .tickSize(legendHeight + 4)
        .tickFormat(d3.format("d"));

      legendSvg.append("g")
  .attr("transform", `translate(0, ${legendHeight})`)  // move axis below the color bar
  .call(legendAxis)
  .call(g => g.select(".domain").remove())  // remove axis line
  .call(g => g.selectAll("text")
    .style("font-family", "Courier New")
    .style("font-size", "10px")
    .attr("dy", "1em"));  // shift labels down for clarity

    }

    // Listeners
    d3.select("#speciesDropdown").on("change", updateHeatmap);
    d3.select("#continentDropdown").on("change", updateHeatmap);
    d3.select("#xAxisSelect").on("change", updateHeatmap);
    d3.select("#yAxisSelect").on("change", updateHeatmap);

    // Initial draw
    updateHeatmap();
  });

});
