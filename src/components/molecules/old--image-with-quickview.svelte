<script>
  import QuickviewSimple from "../quickview-simple.svelte";

  export let src = "some url"; 
  export let alt = "alt text";
  export let caption = "caption hur";

  function testFunction(event) {
    // const parent_container = event.target.parentElement;
    const parent_container = document.body;
    const quickview_component = new QuickviewSimple({
      target: parent_container,
      props: { 
        image_url : src, 
        alt_text : alt,
        caption : caption,
      }
    })
  }
</script>

<section class="image-with-quickview" on:click={testFunction}>
  <img {src} {alt} />
</section>

<style scoped lang="scss">
  .image_with_quickview {
    position: fixed;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    z-index: 64; /* Is there a better way to do this? ie. attach to top of document */
    visibility: hidden;
    box-sizing: border-box;

    &:hover {
      cursor: pointer;
    }
  }
</style>
