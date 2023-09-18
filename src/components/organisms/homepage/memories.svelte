<script>
  import QuickviewSimple from "../../quickview-simple.svelte";

  export let images = [];

  function testing() {
    console.log("What what");
    alert("TEST");
  }

  function zoomOnThis(event) {
    const parent_container = document.body;
    const quickview_component = new QuickviewSimple({
      target: parent_container,
      props: { 
        image_url : event.target.src, 
        alt_text : event.target.alt,
        caption : "caption",
      }
    })
  }
</script> 

<section id="memories" class="memories">
  <hr>
  <!-- <h2>Memories</h2> -->
  <section class="memories__images">
    {#each images as photo, index}
      <img
        class="memories__image memories__image--{ photo.size } memories__image--{ photo.side }"
        src={ photo.src }
        alt={ photo.alt }
        on:click={ zoomOnThis }
      />
    {/each}

    <!-- NOTE -->
    <!-- Image with quickview doesnt work because the grid relies on dyanmic image sizing -->
    <!--
    {#each images as photo, index}
      <ImageWithQuickview
        class="memories__image memories__image--{ photo.size } memories__image--{ photo.side }"
        src={ photo.src }
        alt={ photo.alt }
      />
    {/each}
    -->
  </section>
</section>

<style lang="scss">
  .memories :global(.memories__image) {
      max-height: 250px;
      display: inline-block;
      /* padding: 0 25px 25px 0; */
      padding: 10px;
  }
  .memories :global(.memories__image--1) {
    /* Really gotta fix this up for diff breakpoints */
    max-height: 100px;
    max-height: 12vh;
    max-height: none;
    max-width: 6vw;
  }
   .memories :global(.memories__image--2) {
    max-height: 150px;
    max-height: 18vh;
    max-height: none;
    max-width: 8vw;
  }
  .memories :global(.memories__image--3) {
    max-height: 250px;
    max-height: 29vh;
    max-height: none;
    max-width: 23vw;
  }
  .memories :global(.memories__image--right) {
    float: right;
  }
  .memories :global(.memories__image--left) {
    float: left;
  }

  .memories {
    padding: 80px 0;
    overflow-x: scroll;

    & h2 {
      margin: 0 140px 40px;
      padding: 10px 30px;
      width: fit-content;
    }

    &__images {
      position: relative;
      padding: 20px 40px;

      height: 77vh;
    }

    &__image {
      max-height: 250px;
      display: inline-block;
      /* padding: 0 25px 25px 0; */
      padding: 10px;

      /* Really gotta fix this up for diff breakpoints */
      &--1 {
        max-height: 100px;
        max-height: 12vh;
        max-height: none;
        max-width: 6vw;
      }
      &--2 {
        max-height: 150px;
        max-height: 18vh;
        max-height: none;
        max-width: 8vw;
      }
      &--3 {
        max-height: 250px;
        max-height: 29vh;
        max-height: none;
        max-width: 23vw;
      }
      &--right {
        float: right;
      }
      &--left {
        float: left;
      }
    }
  }
</style>
