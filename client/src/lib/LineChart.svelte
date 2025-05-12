<script>
  import { onMount, afterUpdate } from 'svelte'
  import { groups, max } from 'd3-array'
  import { scaleLinear, scaleTime } from 'd3-scale'
  import { line } from 'd3-shape'
  import AxisX from './AxisX.svelte'
  import AxisY from './AxisY.svelte'
  import { translations } from './consts.js'

  export let data
  export let currentLang = 'en';
  
  const margin = { top: 40, right: 60, bottom: 30, left: 60 };
  let div
  let width = 200
  let height = 520
  let innerHeight = height - margin.top - margin.bottom
  let innerWidth = width - margin.left - margin.right

  onMount(() => {
    updateChartSize()
  })

  afterUpdate(() => {
    updateChartSize()
  })

  function updateChartSize() {
    if (div) {
      width = div.clientWidth
      innerWidth = width - margin.left - margin.right
      height = div.clientHeight
      innerHeight = height - margin.top - margin.bottom
    }
  }

  $: maxValue = data && data.length > 0 
    ? max(data, d => d.value) * 1.1 
    : 1000;
  
  $: lineData = groups(
    data,
    d => d.type
  )

  $: yScale = scaleLinear()
      .domain([0, maxValue])
      .range([innerHeight, 0]);

  $: xScale = scaleTime()
    .domain([new Date(data[0]['date_id']), new Date(data[data.length-1]['date_id'])])
    .range([0, innerWidth]);

  $: lineGenerator = line()
    .x((d, i) => xScale(new Date(d.date_id)))
    .y((d) => yScale(d.value))
</script>

<div class="chart-container" bind:this={div}>
  <svg {width} {height}>
    <g transform="translate({margin.left} {margin.top})">
      <AxisX
        height={innerHeight}
        width={innerWidth} 
        {xScale}
        interval="monthly"
        customTicks={[data[0]['date_id'], data[data.length-1]['date_id']]}
      />
      <AxisY 
        width={innerWidth} 
        {yScale} 
        ticks={yScale.ticks(6)}
        title={translations[currentLang]['powerGeneration'] || 'powerGeneration'}
      />
      {#each lineData as d}
        <path
          d={lineGenerator(d[1])} 
          stroke="black"
          fill="transparent" 
          stroke-width="3" 
        />
        <circle
          cx={xScale(new Date(d[1][0].date_id))}
          cy={yScale(d[1][0].value)}
          r={5}
          fill="black"
        />
        <circle
          cx={xScale(new Date(d[1][d[1].length - 1].date_id))}
          cy={yScale(d[1][d[1].length - 1].value)}
          r={5}
          fill="black"
        />
        <text
          x={xScale(new Date(d[1][0].date_id)) + 10}
          y={yScale(d[1][0].value) - 10}
          fill="black"
          text-anchor="start"
        >
          {d[0]}
        </text>
      {/each}
    </g>
  </svg>
</div>

<style>
  .chart-container {
    width: 100%;
    height: 100%;
  }
</style>