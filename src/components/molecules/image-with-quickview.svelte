<script>
  export let src = "some url"; 
  export let alt = "alt text";
  export let caption = "caption hur";

  let className; 
  export { className as class };

  function toggleZoom( event ) {
    event.target.classList.toggle( "zoomed_in" );
  }
</script>

<section class={`image-with-quickview ${$$props.class}`} on:click={toggleZoom}>
  <img {src} {alt} />
</section>

<style scoped lang="scss">
  .image_with_quickview {
    position: relative;
    width: auto;
    height: auto;

    &:hover {
      cursor: pointer;
    }
  }

  :global(.zoomed_in) {
    background-color: white;
    object-fit: contain;
    position: fixed;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    z-index: 64; /* Is there a better way to do this? ie. attach to top of document */
    box-sizing: border-box;
    padding: var(--space-section-gap);
  }
</style>
