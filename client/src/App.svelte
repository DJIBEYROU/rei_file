<script>
  import { onMount } from 'svelte';
  import StackedAreaChart from './lib/StackedAreaChart.svelte';
  import LineChart from './lib/LineChart.svelte';
  import TimeSlider from './lib/TimeSlider.svelte';
  import Legend from "./lib/Legend.svelte";
  import { renewables, non_renewables, colors, misc, translations, regions } from './lib/consts.js'
  import { writable } from 'svelte/store';

  // Create a store for the current language
  export const currentLanguage = writable('jp'); // Default to English

  let dailyData = []
  let monthlyData = []
  let selectedRegion = 'japan';
  let startDate = '2024-04-01';
  let endDate = '2024-04-15';
  let aggregationLevel = 'hourly'; // Default aggregation for full date range
  let allDates = []; // Store all dates for reuse
  let clickedItem; // Clicked item on legend

  // Add these variables to your existing variables
  let currentLang;
  currentLanguage.subscribe(value => {
    currentLang = value;
  });

  // Add this to your existing legendData transform to make it reactive to language changes
  $: legendData = Object.entries(colors).map(([key, value]) => {
    return {
      color: value,
      shape: (key === 'demand' || key === 'spot_price') ? 'rect' : 'circle',
      text: translations[currentLang][key] || key,
      key: key // Keep original key for filtering
    };
  });

  $: legendData_renewable = legendData.filter(d => renewables.indexOf(d.key) !== -1);
  $: legendData_nonrenewable = legendData.filter(d => non_renewables.indexOf(d.key) !== -1);
  $: legendData_misc = legendData.filter(d => misc.indexOf(d.key) !== -1);

  async function fetchData() {
    try {
      const params = new URLSearchParams({
        start_date: startDate,
        end_date: endDate,
        region: selectedRegion,
        aggregation: aggregationLevel,
      });

      //const base = import.meta.env.VITE_API_BASE_URL;
      //const response = await fetch(`${base}/api/data?${params}`);
      // old: fetch(`http://localhost:3000/api/data?${params}`)

      //const response = await fetch(`${base}/api/data?${params}`);
      const response = await fetch(`/api/data?${params.toString()}`);
      const result = await response.json();
      dailyData = JSON.parse(result.type.daily)
      monthlyData = JSON.parse(result.categorized.monthly)
      //console.log(dailyData, monthlyData)

      if (regions.length > 0 && !selectedRegion) {
        selectedRegion = regions[0];
      }
      
      // Still store actual data dates separately if needed
      if (dailyData.length > 0) {
        allDates = dailyData.map(d => new Date(d.date));
        allDates.sort((a, b) => a - b);
      }
    } catch (error) {
      console.error('Error fetching data:', error);
    } finally {
    }
  }

  onMount(fetchData);

  $: {
    // Refetch when these values change
    if (selectedRegion || startDate || endDate) {
      fetchData();
    }
  }

  function handleOptionChange(event) {
    selectedRegion = event.target.value;
  }
  
  function handleDateRangeChange(event) {
    const { startDate: newStartDate, endDate: newEndDate, aggregationLevel: newAggregationLevel } = event.detail;
    startDate = newStartDate;
    endDate = newEndDate;
    aggregationLevel = newAggregationLevel;
    console.log(`Date range changed: ${startDate} to ${endDate} with aggregation: ${aggregationLevel}`);
    // The reactive statement above will trigger a data fetch
  }

  function downloadCSV(data, filename) {
    const csvContent = convertToCSV(data);
    
    // Create a blob and a download link
    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    
    // Create a temporary link element
    const link = document.createElement('a');
    link.setAttribute('href', url);
    link.setAttribute('download', filename);
    link.style.visibility = 'hidden';
    
    // Append to the document, click it, and remove it
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  }

  function convertToCSV(data) {
    if (!data || data.length === 0) return '';
    
    // Get headers from the first object
    const headers = Object.keys(data[0]);
    
    // Add the header row
    let csvContent = headers.join(',') + '\n';
    
    // Add the data rows
    data.forEach(item => {
      const row = headers.map(header => {
        // Handle values that might contain commas
        let value = item[header];
        
        // Convert objects/arrays to JSON strings
        if (typeof value === 'object' && value !== null) {
          value = JSON.stringify(value);
        }
        
        // Escape quotes and wrap in quotes if needed
        if (typeof value === 'string') {
          value = value.replace(/"/g, '""');
          if (value.includes(',') || value.includes('"') || value.includes('\n')) {
            value = `"${value}"`;
          }
        }
        
        return value;
      }).join(',');
      
      csvContent += row + '\n';
    });
    
    return csvContent;
  }

  function handleDownload(type) {
    if (dailyData.length > 0) {
      downloadCSV(dailyData, `${selectedRegion}_daily_${startDate}_to_${endDate}.csv`);
    }
    if (monthlyData.length > 0) {
      downloadCSV(monthlyData, `${selectedRegion}_monthly_data.csv`);
    }
  }
</script>

<main>
  {#if monthlyData.length > 0}
  <div class='header'>
    <div class='dropdown'>
      <select value={selectedRegion} on:change={handleOptionChange}>
        {#each regions as option}
        <option value={option}>{translations[currentLang][option] || option}</option>
        {/each}
      </select>
      <span class="caret"></span>
    </div>
    <div class='panel'>
      <div class="language-toggle">
        <button 
          class="lang-btn {currentLang === 'jp' ? 'active' : ''}" 
          on:click={() => currentLanguage.set('jp')}>
          JP
        </button>
        <span class="divider">|</span>
        <button 
          class="lang-btn {currentLang === 'en' ? 'active' : ''}" 
          on:click={() => currentLanguage.set('en')}>
          English
        </button>
      </div>      
      <div class="download-buttons">
        <button on:click={() => handleDownload()} class="download-btn">
          Download CSV
        </button>
      </div>

    </div>
  </div>

  <div class="wrapper">
    <div class='left'>
      {#if dailyData.length > 0}
        <StackedAreaChart 
          data={dailyData} 
          aggregationLevel={aggregationLevel} 
          clickedItem={clickedItem}
          currentLang={currentLang}
          />
        {:else}
          <div>Loading...</div>
        {/if}
    </div>
    <div class='right'>
      {#if monthlyData.length > 0}
        <LineChart 
          data={monthlyData} 
          currentLang={currentLang}
        />
      {:else}
        <div>Loading...</div>
      {/if}
    </div>
  </div>
  
  <!-- Time Slider Component -->
  <div class="timeslider-wrapper">
    <TimeSlider 
      {startDate}
      {endDate}
      on:dateRangeChange={handleDateRangeChange}
    />
  </div>
  
  <div style="width: 90%;">
    <div><span style='font-size: 0.7em; margin-left: 20px;'>Click on a legend item to highlight the fuel source. Double-click on any item to un-highlight.</span></div>
    <Legend 
      legendData={legendData_renewable} 
      title="Renewables" 
      bind:clicked={clickedItem}
    />
    <Legend 
      legendData={legendData_nonrenewable} 
      title="Non-renewables" 
      bind:clicked={clickedItem}
    />
    <Legend 
      legendData={legendData_misc} 
      title="" 
      bind:clicked={clickedItem}
    />
  </div>
  
  {:else}
  <div class="wrapper">Loading...</div>
  {/if}
</main>

<style>
  main {
    display: flex;
    flex-direction: column;
    align-items: center;
    width: 100vw;
    height: 100vh;
  }

  .download-buttons {
    display: flex;
    gap: 5px;
  }

  .download-btn {
    padding: 8px 12px;
    margin: 8px;
    cursor: pointer;
    background-color: #fff;
    color: black;
    border: 2px solid black;
    border-radius: 10px;
    font-family: Avenir;
    font-size: 0.85em;
    height: 25px;
    display: flex;
    align-items: center;
    transition: background-color 0.3s ease, color 0.3s ease;
  }

  .download-btn:hover {
    background-color: #000;
    color: #fff;
  }

  .wrapper {
    display: flex;
    width: 90%;
    min-height: 70vh;
    max-height: 70vh; /* Reduced to make room for slider and legend */
  }
  
  .timeslider-wrapper {
    width: 90%;
    margin-top: 0px;
    height: 75px;
  }

  .left {
    width: 75%;
    height: 100%;
  }

  .right {
    width: 25%;
    height: 100%;
  }

  .buttons {
    display: flex;
    margin: 0 20px;
    width: auto;
  }

  .buttons div {
    padding: 8px 12px;
    cursor: pointer;
    border-bottom: none;
    background-color: #d3d3d3;
    color: #696969;
    transition: background-color 0.3s ease;
    border-radius: 10px;
    margin: 8px;
    display: flex;
    align-items: center;
    justify-content: center;
    width: 120px;
    height: 48px;
  }
  
  .buttons div:hover {
    background-color: #C0C0C0;
  }
  
  .buttons div.active {
    background-color: #000;
    color: #fff;
  }

  .buttons h3 {
    text-align: center;
    font-size: 1em;
  }
  
  .dropdown {
    position: relative;
    display: inline-block;
    display: flex;
    padding: 6px 10px;
    cursor: pointer;
    background-color: #fff;
    color: black;
    border: 2px solid black;
    border-radius: 10px;
    height: 25px;
  } 
  
  .dropdown select {
    height: 100%;
    font-family: Avenir;
    appearance: none;
    -webkit-appearance: none;
    -moz-appearance: none;
    background-color: transparent;
    border: none;
    outline: none;
    text-align: center;
    font-size: 1.2em;
    margin: 0px 16px;
  }

  .caret {
    position: absolute;
    top: 50%;
    right: 8px;
    transform: translateY(-50%);
    width: 0;
    height: 0;
    border-style: solid;
    border-width: 5px 5px 0 5px;
    border-color: black transparent transparent transparent;
    pointer-events: none;
    margin-left: 8px
  }

  /* Add these styles to your <style> section */
  .language-toggle {
    display: flex;
    align-items: center;
    margin-right: 15px;
  }

  .lang-btn {
    background: none;
    border: none;
    cursor: pointer;
    padding: 5px 8px;
    font-family: Avenir;
    font-size: 0.9em;
    color: #696969;
    transition: color 0.3s ease;
  }

  .lang-btn.active {
    color: #000;
    font-weight: bold;
  }

  .lang-btn:hover {
    color: #000;
  }

  .divider {
    color: #696969;
    margin: 0 2px;
  }

  .header {
    display: flex;
    justify-content: space-between;
    width: 90%;
    margin: 3px 0px;
    align-items: center; /* Ensure vertical alignment */
  }

  /* Update existing panel style */
  .panel { 
    display: flex;
    align-items: center;
    gap: 10px;
  }
</style>