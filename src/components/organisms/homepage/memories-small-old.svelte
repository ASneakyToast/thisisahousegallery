<script>
  export let images = [];
</script> 

<section class="memories">
  <h2>Memories</h2>
  <section class="memories__images">
    {#each images as photo, index}
      <img
        class="memories__image"
        src={ photo.src }
        alt={ photo.alt }
      />
    {/each}
  </section>
</section>

<style lang="scss">
  .memories {
    padding: 80px 0;
    margin: 0 140px;

    &__images {
      position: relative;

      display: flex;
      flex-direction: row;
      flex-wrap: wrap;
      gap: 10px;

      padding: 20px;
      box-sizing: border-box;
      max-width: 300px;
      border: 1px solid black;
    }

    &__image {
      max-height: 50px;
    }
  }
</style>
