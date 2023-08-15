<section class="image_with_quickview">
  <img src={ image_url } alt={ alt_text } />
</section>

<script>
  import { onMount } from 'svelte';
  import QuickviewSimple from "./quickview-simple.svelte";

  export let image_url = "some url"; 
  export let alt_text = "alt text";
  export let caption = "caption hur";

  onMount(() => {
    const image_with_quickview_items = document.querySelectorAll( ".image_with_quickview" );
    console.log( image_with_quickview_items );

    image_with_quickview_items.forEach(( image ) => {
      image.addEventListener( "click", () => {
        console.log( "alert" );

        const parent_container = image.parentElement;
        const quickview_component = new QuickviewSimple({
          target: parent_container,
          props: { 
            image_url : image_url, 
            alt_text : alt_text,
            caption : caption,
          }
        })

        /* other method
        // Send Data
        const quickviewEvent = new CustomEvent( "quickview-simple--open", {
          // bubbles: true,
          detail: {
            image_url: image_url,
            alt_text: alt_text,
            caption: caption,
          }
        });
        console.log( quickviewEvent );
        image.dispatchEvent( quickviewEvent );
        */

      });
    });
  });
</script>

<style scoped lang="scss">
  .image_with_quickview {

    &:hover {
      cursor: pointer;
    }
  }
</style>
