function RadarChart(id, data, options) {
  console.log("Initial data received by RadarChart:", data); // Debug log

  var cfg = {
    w: 600,
    h: 600,
margin: { top: 60, right: 60, bottom: 60, left: 60 },

    maxValue: 0,
    labelFactor: 1.15,
    wrapWidth: 100,
    opacityArea: 0.35,
    dotRadius: 4,
    opacityCircles: 0.1,
    strokeWidth: 2,
    roundStrokes: false,
    color: d3.scaleOrdinal(d3.schemeCategory10)
  };

  // Merge options into cfg
  if(typeof options !== 'undefined'){
    for(var i in options){
      if(typeof options[i] !== 'undefined'){ cfg[i] = options[i]; }
    }
  }
  console.log("Final configuration:", cfg); // Debug log

  // Extract axes and calculate max value (using the new data structure)
  const allAxis = data[0].axes.map(i => i.axis);
  const maxValue = Math.max(cfg.maxValue, d3.max(data, i => d3.max(i.axes, o => o.value)));
  console.log("All axes:", allAxis, "Max value:", maxValue); // Debug log

  var total = allAxis.length,
      radius = Math.min(cfg.w/2, cfg.h/2),
      Format = d3.format('.0%'),
      angleSlice = Math.PI * 2 / total;

  var rScale = d3.scaleLinear()
      .range([0, radius])
      .domain([0, maxValue]);

  // Clear previous SVG if exists
  d3.select(id).select("svg").remove();

  var svg = d3.select(id).append("svg")
      .attr("width", cfg.w + cfg.margin.left + cfg.margin.right)
      .attr("height", cfg.h + cfg.margin.top + cfg.margin.bottom)
      .attr("class", "radar" + id);

  var g = svg.append("g")
      .attr("transform", "translate(" + (cfg.w / 2 + cfg.margin.left) + "," + (cfg.h / 2 + cfg.margin.top) + ")");

  // Add glow filter
  var filter = g.append('defs').append('filter').attr('id','glow'),
      feGaussianBlur = filter.append('feGaussianBlur').attr('stdDeviation','2.5').attr('result','coloredBlur'),
      feMerge = filter.append('feMerge'),
      feMergeNode_1 = feMerge.append('feMergeNode').attr('in','coloredBlur'),
      feMergeNode_2 = feMerge.append('feMergeNode').attr('in','SourceGraphic');

  // Draw grid circles
  var axisGrid = g.append("g").attr("class", "axisWrapper");

  axisGrid.selectAll(".levels")
     .data(d3.range(1,(cfg.levels+1)).reverse())
     .enter()
      .append("circle")
      .attr("class", "gridCircle")
      .attr("r", d => radius / cfg.levels * d)
      .style("fill", "#CDCDCD")
      .style("stroke", "#CDCDCD")
      .style("fill-opacity", cfg.opacityCircles)
      .style("filter" , "url(#glow)");

  // Add axis labels
  axisGrid.selectAll(".axisLabel")
     .data(d3.range(1,(cfg.levels+1)).reverse())
     .enter().append("text")
     .attr("class", "axisLabel")
     .attr("x", 4)
     .attr("y", d => -d * radius / cfg.levels)
     .attr("dy", (d, i) => {
  const angle = angleSlice * i;
  return (Math.sin(angle) > 0.1) ? "1.2em" : (Math.sin(angle) < -0.1) ? "-0.4em" : "0.35em";
})

     .style("font-size", "01px")
     .attr("fill", "#737373")
     .text(d => Format(maxValue * d / cfg.levels));

  // Draw axes
  var axis = axisGrid.selectAll(".axis")
      .data(allAxis)
      .enter()
      .append("g")
      .attr("class", "axis");

  axis.append("line")
      .attr("x1", 0)
      .attr("y1", 0)
      .attr("x2", (d, i) => rScale(maxValue * 1.1) * Math.cos(angleSlice * i - Math.PI/2))
      .attr("y2", (d, i) => rScale(maxValue * 1.1) * Math.sin(angleSlice * i - Math.PI/2))
      .attr("class", "line")
      .style("stroke", "white")
      .style("stroke-width", "2px");

  axis.append("text")
  .attr("class", "legend")
  .style("font-size", "13px")
  .style("fill", "#333")
  .style("font-weight", "bold")
  .attr("text-anchor", "middle")
  .attr("dy", "0.35em")
  .attr("x", (d, i) => rScale(maxValue * cfg.labelFactor) * Math.cos(angleSlice * i - Math.PI/2))
  .attr("y", (d, i) => rScale(maxValue * cfg.labelFactor) * Math.sin(angleSlice * i - Math.PI/2))
  .text(d => d)
  .call(wrap, cfg.wrapWidth);


  // Create radar line generator
  var radarLine = d3.lineRadial()
      .curve(cfg.roundStrokes ? d3.curveCardinalClosed : d3.curveLinearClosed)
      .radius(d => rScale(d.value))
      .angle((d,i) => i * angleSlice);

  console.log("Radar line generator created"); // Debug log

  // Create blobs (the actual radar shapes)
  var blobWrapper = g.selectAll(".radarWrapper")
      .data(data)
      .enter().append("g")
      .attr("class", "radarWrapper");

  console.log("Creating blobs for", data.length, "data points"); // Debug log

  // Add the filled radar areas
  blobWrapper.append("path")
      .attr("class", "radarArea")
      .attr("d", d => radarLine(d.axes)) // Changed to use d.axes
      .style("fill", (d,i) => cfg.color(i))
      .style("fill-opacity", cfg.opacityArea)
      .on('mouseover', function(e, d){
          console.log("Mouseover:", d.species); // Debug log
          d3.selectAll(".radarArea").transition().duration(200).style("fill-opacity", 0.1); 
          d3.select(this).transition().duration(200).style("fill-opacity", 0.7);    
      })
      .on('mouseout', function(){
          d3.selectAll(".radarArea").transition().duration(200).style("fill-opacity", cfg.opacityArea);
      });

  // Add the radar stroke outlines
  blobWrapper.append("path")
      .attr("class", "radarStroke")
      .attr("d", d => radarLine(d.axes)) // Changed to use d.axes
      .style("stroke-width", cfg.strokeWidth + "px")
      .style("stroke", (d,i) => cfg.color(i))
      .style("fill", "none")
      .style("filter" , "url(#glow)");

  // Add the circles at each data point
  blobWrapper.selectAll(".radarCircle")
      .data(d => d.axes) // Changed to use d.axes
      .enter().append("circle")
      .attr("class", "radarCircle")
      .attr("r", cfg.dotRadius)
      .attr("cx", (d,i) => rScale(d.value) * Math.cos(angleSlice * i - Math.PI/2))
      .attr("cy", (d,i) => rScale(d.value) * Math.sin(angleSlice * i - Math.PI/2))
      .style("fill", (d,i,j) => cfg.color(j))
      .style("fill-opacity", 0.8);

  // Create invisible circles for tooltips
  var blobCircleWrapper = g.selectAll(".radarCircleWrapper")
      .data(data)
      .enter().append("g")
      .attr("class", "radarCircleWrapper");

  blobCircleWrapper.selectAll(".radarInvisibleCircle")
      .data(d => d.axes) // Changed to use d.axes
      .enter().append("circle")
      .attr("class", "radarInvisibleCircle")
      .attr("r", cfg.dotRadius * 1.5)
      .attr("cx", (d,i) => rScale(d.value) * Math.cos(angleSlice * i - Math.PI/2))
      .attr("cy", (d,i) => rScale(d.value) * Math.sin(angleSlice * i - Math.PI/2))
      .style("fill", "#f5f5f5")
      .style("stroke", "#ddd")
	  .style("stroke-width", "0.2px")

      .on("mouseover", function(e, d) {
          const newX = parseFloat(d3.select(this).attr('cx')) - 10;
          const newY = parseFloat(d3.select(this).attr('cy')) - 10;
          tooltip.attr('x', newX).attr('y', newY)
                 .text(`${d.axis}: ${Format(d.value)}`) // Show axis name and value
                 .transition().duration(200).style('opacity', 1);
      })
      .on("mouseout", function(){
          tooltip.transition().duration(200).style("opacity", 0);
      });

  // Add tooltip
  var tooltip = g.append("text")
      .attr("class", "tooltip")
      .style("opacity", 0)
      .style("font-size", "12px")
      .style("font-weight", "bold");

  // Text wrapping function
  function wrap(text, width) {
      text.each(function() {
          var text = d3.select(this),
              words = text.text().split(/\s+/).reverse(),
              word,
              line = [],
              lineNumber = 0,
              lineHeight = 1.4,
              y = text.attr("y"),
              x = text.attr("x"),
              dy = parseFloat(text.attr("dy")),
              tspan = text.text(null).append("tspan").attr("x", x).attr("y", y).attr("dy", dy + "em");
          while (word = words.pop()) {
              line.push(word);
              tspan.text(line.join(" "));
              if (tspan.node().getComputedTextLength() > width) {
                  line.pop();
                  tspan.text(line.join(" "));
                  line = [word];
                  tspan = text.append("tspan").attr("x", x).attr("y", y).attr("dy", ++lineNumber * lineHeight + dy + "em").text(word);
              }
          }
      });
  }

  console.log("Radar chart rendering complete"); // Debug log
}

document.addEventListener("DOMContentLoaded", function () {
  d3.csv("bird_migration_data.csv").then(data => {
    // Step 1: Filter & preprocess the data
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

    let fullData = [];
    let selectedSpecies = new Set();

    // Step 2: Normalize and structure data for radar chart
   function getNormalizedRadarData() {
  const successful = filteredData.filter(d => d.MigrationStatus === "Successful");
  const grouped = d3.groups(successful, d => d.Species);

  const rawAverages = grouped.map(([species, values]) => ({
    species: species,
    Temperature: d3.mean(values, d => d.Temperature - 273.15),
    Humidity: d3.mean(values, d => d.Humidity),
    Pressure: d3.mean(values, d => d.Pressure),
    WindSpeed: d3.mean(values, d => d.WindSpeed)
  }));

  const minVals = {
    Temperature: d3.min(rawAverages, d => d.Temperature),
    Humidity: d3.min(rawAverages, d => d.Humidity),
    Pressure: d3.min(rawAverages, d => d.Pressure),
    WindSpeed: d3.min(rawAverages, d => d.WindSpeed)
  };

  const maxVals = {
    Temperature: d3.max(rawAverages, d => d.Temperature),
    Humidity: d3.max(rawAverages, d => d.Humidity),
    Pressure: d3.max(rawAverages, d => d.Pressure),
    WindSpeed: d3.max(rawAverages, d => d.WindSpeed)
  };

  const minMaxNormalized = rawAverages.map(d => ({
    species: d.species,
    axes: [
      { axis: "Temperature (°C)", value: (d.Temperature - minVals.Temperature) / (maxVals.Temperature - minVals.Temperature) },
      { axis: "Humidity (%)", value: (d.Humidity - minVals.Humidity) / (maxVals.Humidity - minVals.Humidity) },
      { axis: "Pressure (hPa)", value: (d.Pressure - minVals.Pressure) / (maxVals.Pressure - minVals.Pressure) },
      { axis: "Wind Speed (km/h)", value: (d.WindSpeed - minVals.WindSpeed) / (maxVals.WindSpeed - minVals.WindSpeed) }
    ]
  }));

  return minMaxNormalized;
}


    // Step 3: Create checkboxes
    function createCheckboxes(data) {
      const container = d3.select("#controls");
      container.html("");

      data.forEach(d => {
        const id = `check-${d.species.replace(/\s+/g, "_")}`;

        container.append("label")
          .style("margin-right", "12px")
          .html(`
            <input type="checkbox" id="${id}" checked />
            ${d.species}
          `);

        d3.select(`#${id}`).on("change", function () {
          if (this.checked) {
            selectedSpecies.add(d.species);
          } else {
            selectedSpecies.delete(d.species);
          }
          updateRadarChart();
        });
      });
    }

    // Step 4: Redraw chart when checkboxes change
    function updateRadarChart() {
      const filtered = fullData.filter(d => selectedSpecies.has(d.species));

      const radarOptions = {
        w: 500,
        h: 500,
        margin: { top: 50, right: 50, bottom: 50, left: 50 },
        maxValue: 1.0,
        levels: 5,
        roundStrokes: true,
        color: d3.scaleOrdinal([...d3.schemeSet2, ...d3.schemeSet3]),
        opacityArea: 0.15
      };

      RadarChart(".radarChart", filtered, radarOptions);
    }

    // Step 5: Initial draw
    fullData = getNormalizedRadarData();
    fullData.forEach(d => selectedSpecies.add(d.species));
    createCheckboxes(fullData);
    updateRadarChart();
  });
});
