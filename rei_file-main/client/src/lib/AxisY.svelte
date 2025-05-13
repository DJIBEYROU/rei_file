<script>
  export let width;
  export let yScale;
  export let title;
  export let ticks;
  export let orientation = "left"; // Default to left orientation

  const TICK_LENGTH = 10;
  const TEXT_MARGIN = 8;
</script>

<g class='axis y'>
  {#each ticks as tick, index}
    <g 
      class='tick' 
      transform="translate(0, {yScale(tick)})"
    >
      <!-- For left orientation -->
      {#if orientation === "left"}
        <line 
          x1={-TICK_LENGTH} 
          x2={width} 
          y1={0} 
          y2={0} 
          stroke={index === 0 ? '#8f8f8f' : '#e5e7eb'} 
        /> 
        <text 
          x={-TICK_LENGTH-TEXT_MARGIN} 
          dominant-baseline="middle"
          text-anchor="end"
        >
          {tick}
        </text>
      {:else}
        <!-- For right orientation -->
        <line 
          x1={0} 
          x2={TICK_LENGTH} 
          y1={0} 
          y2={0} 
          stroke={index === 0 ? '#8f8f8f' : '#e5e7eb'} 
        /> 
        <text 
          x={TICK_LENGTH+TEXT_MARGIN} 
          dominant-baseline="middle"
          text-anchor="start"
        >
          {tick}
        </text>
      {/if}
    </g>
  {/each}
  
  <!-- Axis title -->
  {#if orientation === "left"}
    <text 
      class="axis-title" 
      x={-TICK_LENGTH-30} 
      y={-36} 
      dy="4" 
      dominant-baseline="hanging" 
      text-anchor="start"
    >
      {title}
    </text>
  {:else}
    <text 
      class="axis-title" 
      x={TICK_LENGTH+30} 
      y={-36} 
      dy="4" 
      dominant-baseline="hanging" 
      text-anchor="end"
    >
      {title}
    </text>
  {/if}
  
  <!-- Axis line -->
<!--   {#if orientation === "left"}
    <line
      class="axis-line"
      x1={0}
      x2={0}
      y1={0}
      y2={yScale.range()[0]}
      stroke="#8f8f8f"
    />
  {:else}
    <line
      class="axis-line"
      x1={0}
      x2={0}
      y1={0}
      y2={yScale.range()[0]}
      stroke="#8f8f8f"
    />
  {/if} -->
</g>

<style>
  text {
    font-size: 0.7rem;
    fill: black;
  }
  
  .axis-title {
    font-size: 0.75rem;
    font-weight: 500;
  }
</style>