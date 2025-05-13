<script>
  import { onMount, afterUpdate } from 'svelte';
  import { min, max } from 'd3-array';
  import { scaleOrdinal, scaleLinear, scaleTime } from "d3-scale";
  import { area, stack, line } from "d3-shape";
  import AxisX from "./AxisX.svelte";
  import AxisY from "./AxisY.svelte";
  import HoverEvents from "./HoverEvents.svelte";
  import Tooltip from "./Tooltip.svelte";
  import { fade } from "svelte/transition";
  import { colors, translations } from './consts.js'

  export let data, aggregationLevel, clickedItem
  export let currentLang = 'en';

  const colorScale = scaleOrdinal()
    .domain(Object.keys(colors)) 
    .range(Object.values(colors))

  const margin = { top: 40, right: 50, bottom: 30, left: 50 }; // Increased right margin for second y-axis
  let div
  let height = 520;
  let width = 600;

  let innerHeight = height - margin.top - margin.bottom;
  let innerWidth = width - margin.left - margin.right;

  $: hoveredDate = null
  $: xPos = 0

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

  function sortEnergyTypesByTotal(data) {
    // Get all energy types (excluding date, region, demand and spot-price)
    const energyTypes = Object.keys(data[0] || {}).filter(
      key => key !== 'date' && key !== 'region' && key !== 'demand' && key !== 'spot_price'
    );
    
    // Calculate total value for each energy type
    const energyTotals = {};
    energyTypes.forEach(energyType => {
      energyTotals[energyType] = data.reduce((total, entry) => 
        total + (entry[energyType] || 0), 0);
    });
    
    // Sort energy types by total value (descending)
    return energyTypes.sort((a, b) => energyTotals[b] - energyTotals[a]);
  }

  // Separate keys into positive and negative stacks
  function separatePositiveNegativeKeys(data, keys) {
    const positiveKeys = [];
    const negativeKeys = [];
    
    keys.forEach(key => {
      // Check if this energy type has any negative values
      const hasNegativeValues = data.some(d => (d[key] || 0) < 0);
      const hasPositiveValues = data.some(d => (d[key] || 0) > 0);
      
      if (hasNegativeValues) negativeKeys.push(key);
      if (hasPositiveValues) positiveKeys.push(key);
    });
    
    return { positiveKeys, negativeKeys };
  }

  $: stackKeys = sortEnergyTypesByTotal(data);
  $: keySeparation = separatePositiveNegativeKeys(data, stackKeys);
  $: positiveKeys = keySeparation.positiveKeys;
  $: negativeKeys = keySeparation.negativeKeys;

  // Calculate the main y-axis domain for stacked areas and demand
  $: yDomainMin = Math.min(
    min(data, d => {
      // Calculate cumulative negative values for each data point
      let cumulativeNegative = 0;
      negativeKeys.forEach(key => {
        const value = d[key] || 0;
        if (value < 0) cumulativeNegative += value;
      });
      return cumulativeNegative;
    }),
    min(data, d => d.demand || 0) // Include demand in min calculation
  ) * 1.1; // Add 10% buffer

  $: yDomainMax = Math.max(
    max(data, d => {
      // Calculate cumulative positive values for each data point
      let cumulativePositive = 0;
      positiveKeys.forEach(key => {
        const value = d[key] || 0;
        if (value > 0) cumulativePositive += value;
      });
      return cumulativePositive;
    }),
    max(data, d => d.demand || 0) // Include demand in max calculation
  ) * 1.1; // Add 10% buffer

  // Calculate the second y-axis domain for spot-price
  //$: y2DomainMin = min(data, d => d['spot_price'] || 0) * 0.9; // Add 10% buffer
  //$: y2DomainMax = max(data, d => d['spot_price'] || 0) * 1.1; // Add 10% buffer
  $: y2DomainMin = 0
  $: y2DomainMax = 130

  $: yScale = scaleLinear()
    .domain([yDomainMin, yDomainMax])
    .range([innerHeight, 0]);

  $: y2Scale = scaleLinear()
    .domain([y2DomainMin, y2DomainMax])
    .range([innerHeight, 0]);

  $: xScale = scaleTime()
    .domain([new Date(data[0]['date']), new Date(data[data.length-1]['date'])])
    .range([0, innerWidth]);

  // Create separate stacks for positive and negative values
  $: positiveStackedData = stack()
    .keys(positiveKeys)
    .offset(stackOffsetDiverging)(
      data.map(d => {
        // Create a copy of each data point with only positive values
        const positiveData = { ...d };
        stackKeys.forEach(key => {
          positiveData[key] = d[key] > 0 ? d[key] : 0;
        });
        return positiveData;
      })
    );

  $: negativeStackedData = stack()
    .keys(negativeKeys)
    .offset(stackOffsetDiverging)(
      data.map(d => {
        // Create a copy of each data point with only negative values
        const negativeData = { ...d };
        stackKeys.forEach(key => {
          negativeData[key] = d[key] < 0 ? d[key] : 0;
        });
        return negativeData;
      })
    );

  // Custom stack offset function for diverging stacks (positive/negative)
  function stackOffsetDiverging(series, order) {
    if (!series.length) return;
    
    for (let i = 0, n = series[0].length; i < n; ++i) {
      let pos = 0;
      let neg = 0;
      
      for (let j = 0; j < series.length; ++j) {
        const value = series[j][i][1] - series[j][i][0];
        
        if (value < 0) {
          series[j][i][1] = neg;
          series[j][i][0] = neg += value;
        } else {
          series[j][i][0] = pos;
          series[j][i][1] = pos += value;
        }
      }
    }
  }

  $: areaFunc = area()
    .x(d => xScale(new Date(d.data.date)))
    .y0(d => yScale(d[0]))
    .y1(d => yScale(d[1]));

  // Line generator for demand (left y-axis)
  $: demandLine = line()
    .x(d => xScale(new Date(d.date)))
    .y(d => yScale(d.demand || 0));

  // Line generator for spot_price (right y-axis)
  $: spotPriceLine = line()
    .x(d => xScale(new Date(d.date)))
    .y(d => y2Scale(d['spot_price'] || 0));

  $: hoveredData = hoveredDate ? findClosestDataPoint(data, hoveredDate, aggregationLevel) : null;

  function findClosestDataPoint(data, hoveredTimestamp, aggregationLevel) {
    if (!data.length) return null;
    
    return data.reduce((closest, current) => {
      const currentDate = new Date(current.date);
      const currentTimestamp = currentDate.getTime();
      const closestDate = closest ? new Date(closest.date) : null;
      const closestTimestamp = closestDate ? closestDate.getTime() : null;
      
      // First entry or exact match
      if (!closest || currentTimestamp === hoveredTimestamp) {
        return current;
      }
      
      // For different aggregation levels, adjust how we determine "closest"
      if (aggregationLevel === 'hourly') {
        // For hourly data, simple timestamp difference is appropriate
        if (Math.abs(currentTimestamp - hoveredTimestamp) < Math.abs(closestTimestamp - hoveredTimestamp)) {
          return current;
        }
      } 
      else if (aggregationLevel === 'daily') {
        // For daily data, compare day boundaries
        const hoveredDay = new Date(hoveredTimestamp).setHours(0, 0, 0, 0);
        const currentDay = new Date(currentDate).setHours(0, 0, 0, 0);
        const closestDay = new Date(closestDate).setHours(0, 0, 0, 0);
        
        if (Math.abs(currentDay - hoveredDay) < Math.abs(closestDay - hoveredDay)) {
          return current;
        }
      }
      else if (aggregationLevel === 'weekly') {
        // For weekly data, find the closest week start
        const hoveredWeekStart = getWeekStart(new Date(hoveredTimestamp));
        const currentWeekStart = getWeekStart(currentDate);
        const closestWeekStart = getWeekStart(closestDate);
        
        if (Math.abs(currentWeekStart.getTime() - hoveredWeekStart.getTime()) < 
            Math.abs(closestWeekStart.getTime() - hoveredWeekStart.getTime())) {
          return current;
        }
      }
      else if (aggregationLevel === 'monthly') {
        // For monthly data, compare month and year
        const hoveredDate = new Date(hoveredTimestamp);
        const hoveredMonth = hoveredDate.getMonth();
        const hoveredYear = hoveredDate.getFullYear();
        
        const currentMonth = currentDate.getMonth();
        const currentYear = currentDate.getFullYear();
        
        const closestMonth = closestDate.getMonth();
        const closestYear = closestDate.getFullYear();
        
        // Calculate "distance" in months
        const hoveredTotalMonths = (hoveredYear * 12) + hoveredMonth;
        const currentTotalMonths = (currentYear * 12) + currentMonth;
        const closestTotalMonths = (closestYear * 12) + closestMonth;
        
        if (Math.abs(currentTotalMonths - hoveredTotalMonths) < 
            Math.abs(closestTotalMonths - hoveredTotalMonths)) {
          return current;
        }
      }
      
      return closest;
    }, null);
  }

  // Helper function to get the start of a week (Sunday)
  function getWeekStart(date) {
    const result = new Date(date);
    const day = result.getDay(); // 0 = Sunday, 1 = Monday, etc.
    result.setDate(result.getDate() - day); // Go back to the previous Sunday
    result.setHours(0, 0, 0, 0); // Reset time to start of day
    return result;
  }
</script>

<div class="chart-container" bind:this={div}>
  <svg
    {width}
    {height}
  >
    <g transform="translate({margin.left} {margin.top})">
      <!-- Main Y-Axis (left) -->
      <AxisY
        width={innerWidth} 
        {yScale} 
        ticks={yScale.ticks(8)}
        title={translations[currentLang]['powerGeneration'] || 'powerGeneration'}
        orientation="left"
      />
      
      <!-- Secondary Y-Axis (right) -->
      <g transform="translate({innerWidth}, 0)">
        <AxisY
          width={0}
          yScale={y2Scale}
          ticks={y2Scale.ticks(8)}
          title={translations[currentLang]['systemPrice'] || 'systemPrice'}
          orientation="right"
        />
      </g>
      
      <!-- X-Axis -->
      <AxisX
        height={innerHeight}
        width={innerWidth} 
        interval={aggregationLevel}
        {xScale}
      />
      
      <!-- Zero line -->
      <line 
        x1="0" 
        y1={yScale(0)} 
        x2={innerWidth} 
        y2={yScale(0)} 
        stroke="black" 
        stroke-width="1" 
        stroke-dasharray="4,4" 
      />
      
      <!-- Positive stacked areas -->
      {#each positiveStackedData as d, index}
        <path
          transition:fade
          d={areaFunc(d)}
          stroke={colorScale(d.key)}
          fill={colorScale(d.key)}
          stroke-width="1"
          opacity={clickedItem
          ? clickedItem === d.key 
            ? 1
            : 0.2
          : 1}
        />
      {/each}
      
      <!-- Negative stacked areas -->
      {#each negativeStackedData as d, index}
        <path
          transition:fade
          d={areaFunc(d)}
          stroke={colorScale(d.key)}
          fill={colorScale(d.key)}
          stroke-width="1"
          opacity={clickedItem
          ? clickedItem === d.key 
            ? 1
            : 0.2
          : 1}
        />
      {/each}
      
      <!-- Demand line (using left y-axis) -->
      <path 
        d={demandLine(data)} 
        fill="none" 
        stroke="black" 
        stroke-width="2" 
      />
      
      <!-- Spot-price line (using right y-axis) -->
      <path 
        d={spotPriceLine(data)} 
        fill="none" 
        stroke="purple" 
        stroke-width="2" 
      />
      
      <HoverEvents
        width={innerWidth}
        height={innerHeight}
        {xScale}
        {margin}
        bind:hoveredDate
        bind:xPos
      />
    </g>
  </svg>
  {#if hoveredDate && hoveredData}
    <Tooltip 
      data={hoveredData} 
      x={xPos} 
      {colorScale} 
      {width} 
      showDemand={true}
      showSpotPrice={true}
      aggregationLevel={aggregationLevel}
      currentLang={currentLang}
    />
  {/if}
</div>

<style>
  .chart-container {
    position: relative;
    width: 100%;
    height: 100%;
  }
</style>
