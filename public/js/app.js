// show tooltip at data point 'd' using step communities data 'steps'
function showTooltip(d, steps) {
  d3.select('body').selectAll('.tooltip').remove();
  const tooltip = d3.select('body')
    .append('div')
    .attr('class', 'tooltip')
    .style('opacity', 0);
  tooltip.transition()
    .duration(200)
    .each('start', function() { d3.select(this).style('block'); })
    .style('opacity', 1);

  const FONT_SIZE = 14; // in pixels
  const TOOLTIP_WIDTH = 20; // in rem
  const ARROW_MARGIN = 1.65;
  const ARROW_WIDTH = FONT_SIZE;
  const DATE_FORMAT = d3.time.format('%c');

  const rightOrLeftLimit = FONT_SIZE * TOOLTIP_WIDTH;
  const direction = d3.event.pageX > rightOrLeftLimit ? 'right' : 'left';
  const left = direction === 'right' ?
    d3.event.pageX - rightOrLeftLimit :
    d3.event.pageX - ARROW_MARGIN * FONT_SIZE - ARROW_WIDTH / 2;

  const community = steps[d.step].communities[d.community];
  const time = DATE_FORMAT(new Date(steps[d.step].time * 1000));

  tooltip.html(`<div class="community">
      <p class="attribute">${community.data['topic']}</p>
      <p><b>Time (UTC):</b> ${time}</p>
      <p>${community.users.length} user(s)</p>
    </div>`)
    .classed(direction, true)
    .style({left: `${left}px`, top: (d3.event.pageY + 16) + 'px'});
}

// hide any currently displaying tooltip
function hideTooltip() {
  d3.select('.tooltip').transition()
    .duration(200)
    .each('end', function() { this.remove(); })
    .style('opacity', 0);
}

// initialise the chart display
function initChart(timeline, events, steps, defaultColorKey, status) {
  status.text('initialising chart ...');
  const colors = d3.scale.category20();
  const numSteps = Object.keys(steps).length;
  const eventDropsChart = d3.chart.eventDrops()
    .start(new Date(steps[1].time * 1000) - 3600000)
    .end(new Date(steps[numSteps].time * 1000 + 7200000))
    .date(d => new Date(steps[d.step].time * 1000))
    .labelsWidth(100)
    .eventColor((d, i) => {
      return colors(steps[d.step].communities[d.community].data[defaultColorKey]);
    })
    .events(events)
    .dropSize(d => 8)
    .mouseover((data) => showTooltip(data, steps))
    .mouseout(hideTooltip);

  d3.select('#chart-panel').style('opacity', 1);
  d3.select('#chart-container')
    .datum(timeline)
    .call(eventDropsChart);
  status.text('ready');
}

// load data to be displayed
function loadData(dataset, minSteps, status) {
  var timeline, events = {}, steps, defaultColorKey;
  status.text('loading dataset "' + dataset + '" with ' + minSteps + ' minimum steps ...');
  d3.json('data/' + dataset + '.timeline.json', (err, data) => {
    if (err) return console.warn(err);

    // filter timeline according to given minimum steps
    timeline = data.filter(e => e.data.length >= minSteps);

    // now, load the timeline events
    status.text('loading events data ...');
    d3.json('data/' + dataset + '.events.json', (err, data) => {
      if (err) return console.warn(err);

      // filter events according to resulting filtered timeline
      let names = timeline.map(e => e.name);
      for (let key in data)
        events[key] = data[key].filter(e => {
          if (e.name !== undefined) {
            return names.indexOf(e.name) != -1 ? true : false;
          } else {
            return names.indexOf(e.source.name) != - 1 &&
              names.indexOf(e.target.name) != -1 ? true : false;
          }
        });

      // now, load the step communities
      status.text('loading step communities data ...');
      d3.json('data/' + dataset + '.steps.json', (err, data) => {
        if (err) return console.warn(err);
        steps = data['steps'];
        defaultColorKey = data['default_color_key'];

        // finally, initialise the chart with all loaded data
        initChart(timeline, events, steps, defaultColorKey, status);
      });
    });
  });
}

// start the app
document.addEventListener('DOMContentLoaded', () => {
  const datasets = d3.select('#datasets');
  const minSteps = d3.select('#minSteps');
  const btnLoad = d3.select('#btnLoad');
  const status = d3.select('#status');

  // initialise UI
  status.text('initialising UI ...');
  d3.select('#chart-panel').style('opacity', 0);

  // initialise dataset select box
  datasets.selectAll('*').remove();
  AVAIL_DATASETS.forEach(id => {
    datasets.append('option')
      .property('value', id)
      .text(id);
  });

  // initialise minSteps input box
  minSteps.property('value', 1);

  // initialise load button
  btnLoad.on('click', event => {
    loadData(datasets.property('value'), minSteps.property('value'), status);
  });

  // all set
  status.text('ready');
});
