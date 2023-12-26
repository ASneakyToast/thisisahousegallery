<script>
  import QuickviewSimple from "../../quickview-simple.svelte";

  export let images = [];

  function zoomOnThis(event) {
    const parent_container = document.body;
    const quickview_component = new QuickviewSimple({
      target: parent_container,
      props: { 
        image_url : event.target.srcset, 
        alt_text : event.target.alt,
        caption : "caption",
      }
    })
  }
</script> 

<section id="memories" class="memories">
  <hr>
  <section class="memories__images">
    {#each images as photo, index}
      <img
        class="memories__image memories__image--{ photo.size } memories__image--{ photo.side }"
        srcset={ photo.src }
        alt={ photo.alt }
        on:click={ zoomOnThis }
      />
    {/each}
  </section>
</section>

<style lang="scss">
  .memories {
    padding: 80px 0 40px;
    overflow-x: scroll;

    & h2 {
      margin: 0 140px 40px;
      padding: 10px 30px;
      width: fit-content;
    }

    &__images {
      position: relative;
      padding: 20px 40px;
      width: max-content;
      height: 77vh;
    }

    &__image {
      display: inline-block;
      padding: 10px;
      max-height: 100%;
      cursor: pointer;
    }

    @media screen and (min-width: 768px) {
      &__images {
        width: auto;
      }
      &__image {
        max-height: 250px;
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
  }
</style>
