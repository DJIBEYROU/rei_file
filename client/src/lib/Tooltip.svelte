<script>
  export let width;
  export let data;
  export let colorScale;
  export let x;
  export let showDemand = false;
  export let showSpotPrice = false;
  export let aggregationLevel = 'hourly';
  export let currentLang = 'en';
  import { translations } from './consts.js'
  import { fly, fade } from "svelte/transition";

  let tooltipWidth, rows;

  const xNudge = 5;
  const yNudge = 5;

  // If the x position + the tooltip width exceeds the chart width, offset backward to prevent overflow
  $: xPosition =
    x + tooltipWidth + xNudge > width
      ? x - tooltipWidth - xNudge
      : x + xNudge;
  
  let yPosition = yNudge;

  // Format the date based on aggregation level
  $: formattedDate = formatDate(data.date, aggregationLevel);

  function formatDate(dateStr, level) {
    const date = new Date(dateStr);
    
    // Function to get ordinal suffix (1st, 2nd, 3rd, etc.)
    const getOrdinalSuffix = (day) => {
      if (day > 3 && day < 21) return 'th';
      switch (day % 10) {
        case 1: return 'st';
        case 2: return 'nd';
        case 3: return 'rd';
        default: return 'th';
      }
    };
    
    const day = date.getDate();
    const ordinalDay = day + getOrdinalSuffix(day);
    
    // Array of month names
    const months = [
      'Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
      'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'
    ];
    const month = months[date.getMonth()];
    const year = date.getFullYear();
    
    // Base date format without time
    let formattedStr = (level === 'monthly')  ? `${month} ${year}` : `${ordinalDay} ${month} ${year}`;
    
    // Add time for hourly aggregation
    if (level === 'hourly') {
      let hours = date.getHours();
      const minutes = date.getMinutes();
      const ampm = hours >= 12 ? 'pm' : 'am';
      
      // Convert to 12-hour format
      hours = hours % 12;
      hours = hours ? hours : 12; // the hour '0' should be '12'
      
      // Format minutes with leading zero if needed
      const minutesStr = minutes < 10 ? '0' + minutes : minutes;
      
      formattedStr += `, ${hours}.${minutesStr}${ampm}`;
    }
    
    return formattedStr;
  }

  $: if(data){
    let objEntries = Object.entries(data);
    objEntries.sort((a, b) => b[1] - a[1]);
    let sortedObj = Object.fromEntries(objEntries);
    rows = Object.keys(sortedObj).filter(
      d => d !== 'date' && d !== 'region' && 
      (!showDemand || d !== 'demand') && 
      (!showSpotPrice || d !== 'spot_price')
    );
  }

  // Helper function to get translation
  function getTranslation(key, lang) {
    return translations[lang][key] || key;
  }
</script>

<div
  class="tooltip"
  in:fly={{ y: 10, duration: 200, delay: 200 }}
  out:fade
  style="left:{xPosition}px; top:{yPosition}px;"
  bind:clientWidth={tooltipWidth}
>
  <h1>
    {formattedDate}
  </h1>
  
  <!-- Energy types data -->
  {#each rows as row}
  <div class='info'>
    <span class="key" style="background: {colorScale(row)}">
      {getTranslation(row, currentLang)}
    </span> 
    <span>
      {typeof data[row] === 'number' ? data[row].toFixed(2) : data[row]}
    </span>
  </div>
  {/each}
  
  <!-- Demand data -->
  {#if showDemand && data.demand !== undefined}
  <div class="separator"></div>
  <div class='info special-row'>
    <span class="key demand-key">
      {getTranslation('demand', currentLang)}
    </span> 
    <span>
      {typeof data.demand === 'number' ? data.demand.toFixed(2) : data.demand}
    </span>
  </div>
  {/if}
  
  <!-- Spot Price data -->
  {#if showSpotPrice && data['spot_price'] !== undefined}
  <div class="separator"></div>
  <div class='info special-row'>
    <span class="key spot_price-key">
      {getTranslation('systemPrice', currentLang)}
    </span> 
    <span>
      {typeof data['spot_price'] === 'number' ? data['spot_price'].toFixed(2) : data['spot_price']} ¥/kWh
    </span>
  </div>
  {/if}
</div>

<style>
  .tooltip {
    position: absolute;
    padding: 8px 6px;
    background: white;
    box-shadow: rgba(0, 0, 0, 0.15) 2px 3px 8px;
    border-radius: 3px;
    pointer-events: none;
    min-width: 130px;
    transition: top 300ms ease, left 300ms ease;
    font-size: 0.8rem;
  }

  h1 {
    margin: 0;
    font-size: 1rem;
    font-weight: 500;
    margin-bottom: 3px;
  }

  .info {
    display: flex;
    justify-content: space-between;
    column-gap: 8px;
  }

  .key {
    font-size: 0.65rem;
    font-weight: bold;
    padding: 3px 4px 2px 4px;
    border-radius: 3px;
    text-transform: uppercase;
    white-space: nowrap;
  }

  .special-row {
    margin-top: 2px;
  }

  .separator {
    height: 1px;
    background-color: #eee;
    margin: 4px 0;
  }

  .demand-key {
    background-color: black;
    color: white;
  }

  .spot-price-key {
    background-color: purple;
    color: white;
  }
</style>