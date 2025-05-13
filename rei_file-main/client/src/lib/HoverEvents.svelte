<script>
  export let xScale;
  export let margin;
  export let width;
  export let height;
  export let hoveredDate;
  export let xPos;
  export let aggregationLevel = 'hourly'; // Add aggregation level as a prop

  const handleMousemove = function (e) {
    // Get the x position relative to the chart area
    const mouseX = e.offsetX - margin.left;
    
    // Get the date from the x position
    const date = xScale.invert(mouseX);
    
    // Store the raw timestamp for precise calculations
    hoveredDate = date.getTime();
    
    // Store the x position for the vertical line
    xPos = mouseX;
  };

  const handleMouseleave = function () {
    hoveredDate = null;
    xPos = 0;
  };
</script>

<rect
  class="hover-listener"
  fill="transparent"
  {width}
  {height}
  on:mousemove={handleMousemove}
  on:mouseleave={handleMouseleave}
/>

{#if hoveredDate}
  <line
    x1={xPos}
    x2={xPos}
    y1={0}
    y2={height}
    stroke="darkgrey"
    stroke-dasharray="2, 2"
    pointer-events="none"
  />
{/if}

<style>
  rect {
    cursor: crosshair;
  }
</style>