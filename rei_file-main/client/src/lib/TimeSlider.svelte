<script>
  import { onMount, createEventDispatcher } from 'svelte';
  import { select } from 'd3-selection';
  import { scaleTime } from 'd3-scale';
  import { brushX } from 'd3-brush';
  import { axisBottom } from 'd3-axis';
  import { timeFormat } from 'd3-time-format';
  import { extent } from 'd3-array';

  export let startDate = null;   // Initial start date
  export let endDate = null;     // Initial end date
  export let height = 60;        // Height of the timeslider
  export let margin = { top: 10, right: 40, bottom: 30, left: 40 };

  // Event dispatcher
  const dispatch = createEventDispatcher();
  
  // Local state
  let svg;
  let brush;
  let x;
  let xAxis;
  let width;
  let container;
  
  onMount(() => {
    // Wait for container to be available and measure its width
    if (container) {
      initializeSlider();
      return () => {
        // Cleanup
      };
    }
  });

  function initializeSlider() {
    // Get dimensions
    width = container.clientWidth - margin.left - margin.right;
    
    // Set up the full date range for the slider
    const minDate = new Date('2022-01-01');
    const maxDate = new Date('2024-12-31');
    
    // Create an array of dates between min and max (e.g., monthly increments)
    const dateRange = [];
    let currentDate = new Date(minDate);
    
    while (currentDate <= maxDate) {
      dateRange.push(new Date(currentDate));
      currentDate.setMonth(currentDate.getMonth() + 1);
    }

    // Set initial values if not provided
    if (!startDate) startDate = '2022-01-01';
    if (!endDate) endDate = '2024-09-31';
    
    // Parse initial dates if they're strings
    const parsedStartDate = startDate instanceof Date ? startDate : new Date(startDate);
    const parsedEndDate = endDate instanceof Date ? endDate : new Date(endDate);
    
    // Create scales
    x = scaleTime()
      .domain(extent(dateRange))
      .range([0, width]);
    
    // Create the SVG and append g elements
    svg = select(container)
      .append('svg')
      .attr('width', width + margin.left + margin.right)
      .attr('height', height + margin.top + margin.bottom)
      .append('g')
      .attr('transform', `translate(${margin.left},${margin.top})`);
    
    // Create axis with appropriate tick format for the full date range (years span)
    xAxis = axisBottom(x)
      .tickFormat(timeFormat('%b %Y'))
      .ticks(width > 600 ? 10 : 5);
    
    // Append axis
    svg.append('g')
      .attr('class', 'x-axis')
      .attr('transform', `translate(0,${height - margin.bottom})`)
      .call(xAxis);
    
    // Customize the axis appearance
    svg.selectAll('.x-axis path, .x-axis line')
      .style('stroke', '#000')
      .style('shape-rendering', 'crispEdges');
    
    svg.selectAll('.x-axis text')
      .style('font-size', '10px')
      .style('font-family', 'Avenir, sans-serif');
    
    // Create brush
    brush = brushX()
      .extent([[0, 0], [width, height - margin.bottom]])
      .on('brush', brushed)
      .on('end', brushEnded);
    
    // Append brush
    const brushG = svg.append('g')
      .attr('class', 'brush')
      .call(brush);
    
    // Style the brush
    brushG.selectAll('.selection')
      .style('fill', '#000')
      .style('fill-opacity', 0.3)
      .style('stroke', '#000')
      .style('stroke-width', 2);
    
    // Add custom handles
    const handleHeight = height - margin.bottom;
    const handleWidth = 8;
    
    brushG.selectAll('.handle')
      .style('fill', '#000')
      .style('stroke', '#000')
      .style('stroke-width', 1)
      .attr('rx', 3)
      .attr('ry', 3);
    
    // Set initial brush position
    brush.move(brushG, [
      x(parsedStartDate),
      x(parsedEndDate)
    ]);
  }
  
  function brushed(event) {
    if (!event.selection) return;
    
    // Get the selection range
    const [x0, x1] = event.selection;
    
    // Convert to dates
    const newStartDate = x.invert(x0);
    const newEndDate = x.invert(x1);
    
    // Update local state (without triggering API calls)
    updateDates(newStartDate, newEndDate, false);
  }
  
  function brushEnded(event) {
    if (!event.selection) return;
    
    // Get the selection range
    const [x0, x1] = event.selection;
    
    // Convert to dates
    const newStartDate = x.invert(x0);
    const newEndDate = x.invert(x1);
    
    // Update local state and dispatch events
    updateDates(newStartDate, newEndDate, true);
  }
  
  function updateDates(newStartDate, newEndDate, dispatchEvent) {
    // Format dates to YYYY-MM-DD
    const formattedStartDate = formatDate(newStartDate);
    const formattedEndDate = formatDate(newEndDate);
    
    // Update local values
    startDate = formattedStartDate;
    endDate = formattedEndDate;
    
    // Calculate appropriate aggregation level based on date range
    const aggregationLevel = determineAggregationLevel(newStartDate, newEndDate);
    
    // Dispatch event to parent
    if (dispatchEvent) {
      dispatch('dateRangeChange', {
        startDate: formattedStartDate,
        endDate: formattedEndDate,
        aggregationLevel
      });
    }
  }
  
  function determineAggregationLevel(startDate, endDate) {
    // Calculate the difference in days between the two dates
    const diffTime = Math.abs(endDate - startDate);
    const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
    
    // Define thresholds and corresponding aggregation levels
    if (diffDays > 365) {
      return 'monthly';
    } else if (diffDays > 90) {
      return 'weekly';
    } else if (diffDays > 30) {
      return 'daily';
    } else {
      return 'hourly'; // For smaller ranges, use the most granular data available
    }
  }
  
  function formatDate(date) {
    return date.toISOString().split('T')[0];
  }
  
  // Handle container resize
  $: if (container && container.clientWidth > 0) {
    // Clear previous SVG
    if (svg) {
      select(container).selectAll('*').remove();
      initializeSlider();
    }
  }
</script>

<div class="timeslider-container" bind:this={container}>
  <!-- D3 will append the SVG here -->
</div>

<style>
  .timeslider-container {
    width: 100%;
    position: relative;
  }
  
  :global(.brush .handle) {
    cursor: ew-resize;
  }
  
  :global(.brush .selection) {
    cursor: move;
  }
</style>