<script>
  export let legendData;
  export let title;
  export let clicked;
</script>

<style>
  .legend-container {
    display: flex;
    width: 100%;
    flex-wrap: wrap;
  }

  .legend-item {
    display: flex;
    align-items: center;
    margin-bottom: 6px;
    margin-left: 20px;
    font-size: 0.85em;
    min-width: 130px;
    cursor: pointer;
  }

  /* Base styles for color indicators */
  .color-indicator {
    width: 14px;
    height: 14px;
    margin-right: 8px;
  }

  /* Circle shape */
  .shape-circle {
    border-radius: 50%;
  }

  /* Rectangle shape */
  .shape-rect {
    border-radius: 0;
    height: 7px;
  }
  
  /* Special style for when an item is clicked/selected */
  .selected {
    font-weight: bold;
  }
</style>

{#if title}
  <h3 style="margin: 5px 20px;">{title}</h3>
{/if}
<div class='legend-container'>
  {#each legendData as { color, key, text, shape = 'circle' }}
    <div 
      class="legend-item {clicked === key ? 'selected' : ''}"
      on:click={(event) => {
        event.stopImmediatePropagation();
        clicked = key;
      }}
      on:dblclick={(event) => {
        event.stopImmediatePropagation();
        clicked = null;
      }}
    >
      <div 
        class="color-indicator {shape === 'circle' ? 'shape-circle' : 'shape-rect'}" 
        style="background-color: {color}"
      ></div>
      <span>{text}</span>
    </div>
  {/each}
</div>