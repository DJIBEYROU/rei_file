<script>
    import { timeMonth, timeWeek, timeDay, timeHour, timeInterval } from 'd3-time';
    
    export let height;
    export let xScale;
    export let interval;
    export let width = 0; // chart width from parent component
    export let customTicks = null; // Allow custom ticks to be passed in
    
    const TICK_LENGTH = 4;
    const IDEAL_TICK_SPACING = 80; // Target pixels between ticks
  
    // Generate appropriate ticks based on interval, domain range, and chart width
    $: ticks = customTicks || getTicks(xScale, timeInterval);
    
    // For debugging: log the number of ticks generated
    $: if (ticks && ticks.length > 0) {
      console.log(`Generated ${ticks.length} ticks for interval: ${interval}, width: ${width}px`);
    }
    
    function getTicks(scale, interval) {      
      const domain = scale.domain();
      const range = scale.range();
      const rangeWidth = range[1] - range[0];
      
      // Calculate the ideal number of ticks based on available width
      const idealTickCount = Math.max(2, Math.floor(rangeWidth / IDEAL_TICK_SPACING));
      
      // Calculate the domain time span in days
      const domainSpanMs = domain[1] - domain[0];
      const domainSpanDays = domainSpanMs / (1000 * 60 * 60 * 24);
      
      // Determine the appropriate time interval based on both the interval parameter and the domain span
      if (interval === 'hourly') {
        if (domainSpanDays <= 2) {
          // For 1-2 days, show hours more frequently
          return timeHour.every(Math.max(1, Math.floor(12 / idealTickCount))).range(domain[0], domain[1]);
        } else if (domainSpanDays <= 7) {
          // For 2-7 days, mix of hours and days
          return timeDay.every(1).range(domain[0], domain[1]);
        } else {
          // For longer periods, switch to daily ticks
          return timeDay.every(Math.max(1, Math.floor(domainSpanDays / idealTickCount))).range(domain[0], domain[1]);
        }
      } else if (interval === 'daily') {
        if (domainSpanDays <= 30) {
          // For shorter periods, use more daily ticks
          const dayInterval = Math.max(1, Math.floor(domainSpanDays / idealTickCount));
          const ticks = timeDay.every(dayInterval).range(domain[0], domain[1]);

          return ticks;
        } else if (domainSpanDays <= 90) {
          // For medium periods, use weekly ticks but more frequently
          return timeWeek.every(Math.max(1, Math.floor((domainSpanDays / 7) / idealTickCount))).range(domain[0], domain[1]);
        } else {
          // For longer periods, use monthly ticks but more frequently
          return timeMonth.every(Math.max(1, Math.floor((domainSpanDays / 30) / idealTickCount))).range(domain[0], domain[1]);
        }
      } else if (interval === 'weekly') {
        // Calculate weeks between start and end dates
        const weeksSpan = Math.ceil(domainSpanDays / 7);
        
        if (domainSpanDays <= 120) {
          // For shorter periods, use more weekly ticks
          const weekInterval = Math.max(1, Math.floor(weeksSpan / idealTickCount));
          const ticks = timeWeek.every(weekInterval).range(domain[0], domain[1]);

          return ticks;
        } else {
          // For longer periods, use more monthly ticks
          return timeMonth.every(Math.max(1, Math.floor((domainSpanDays / 30) / idealTickCount))).range(domain[0], domain[1]);
        }
      } else if (interval === 'monthly') {
        // Calculate months between start and end dates
        const monthsSpan = 
          (domain[1].getFullYear() - domain[0].getFullYear()) * 12 + 
          (domain[1].getMonth() - domain[0].getMonth());
        
        const monthInterval = Math.max(1, Math.floor(monthsSpan / (idealTickCount/2)));
        const ticks = timeMonth.every(monthInterval).range(domain[0], domain[1]);
        
        return ticks;
      }
      
      // Default fallback - let d3 decide
      return scale.ticks(idealTickCount);
    }
    
    function formatDate(dateString, format) {
      const date = new Date(dateString);
      
      if (format === 'day') {
        // Format as "7 Apr"
        const day = date.getDate();
        const month = date.toLocaleDateString('en-US', { month: 'short' });
        return `${day} ${month}`;
      } else if (format === 'month') {
        // Format as "Apr 24" (month and year)
        const month = date.toLocaleDateString('en-US', { month: 'short' });
        const year = date.getFullYear().toString().substr(-2);
        return `${month} ${year}`;
      }
      
      return dateString; // Default fallback
    }
  </script>
  
  {#each ticks as tick, i}
    {#if tick}
      <line
        x1={xScale(new Date(tick))}
        x2={xScale(new Date(tick))}
        y1={height}
        y2={height + TICK_LENGTH}
        stroke="#808080"
      />
      {#if interval === 'hourly' || interval === 'daily' || interval === 'weekly'}
        <text
          x={xScale(new Date(tick))}
          y={height + TICK_LENGTH}
          dy="6"
          dominant-baseline="hanging"
          text-anchor="middle"
        >
          {formatDate(tick, 'day')}
        </text>
      {:else if interval === 'monthly'}
        <text
          x={xScale(new Date(tick))}
          y={height + TICK_LENGTH}
          dy="6"
          dominant-baseline="hanging"
          text-anchor="middle"
        >
          {formatDate(tick, 'month')}
        </text>
      {/if}
    {/if}
  {/each}
  
  <style>
    text {
      font-size: 0.75rem;
      fill: black;
    }
  </style>