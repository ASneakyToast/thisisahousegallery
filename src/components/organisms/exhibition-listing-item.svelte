<script>
  import QuickviewThumbnails from "../../components/quickview-thumbnails.astro";

  export let title = "Exhibition title";
  export let title_slug = "exhibition_title";
  export let date = "06.23 - 07-07";
  export let gallery_images = "";
  export let card_images = {
    front_src: "/exhibitions/thisisalivingroom/Showcard001.jpg",
    back_src: "/exhibitions/thisisalivingroom/showcard-back.jpg",
  }
</script>

<div id={ title_slug }>
  <section class="exhibition-header">
    <h2>{ title }</h2>
    <h3>{ date }</h3>
  </section>
  <section class="exhibition-media">
    <section class="exhibition-card">
      <img 
        src={ card_images.front_src }
        alt="The promotional showcard for the exhibition '{ title }' by This is a House Gallery."
      />
      <img 
        src="{ card_images.back_src }"
        alt="The back side of the promotional showcard for the exhibition '{ title }' by This is a House Gallery."
      />
    </section>
    <section class="exhibition-images">
      {#each gallery_images as photo, index}
        <img 
          class="quickview-item" 
          src={ "/exhibitions/" + title_slug + "/images/" + gallery_images[ index ].photo[0].filename }
          alt="An exhibition photo of the show 'This is a living room' by Joel Lithgow and Joseph Blake with This is a House Gallery." 
        />
      {/each}
    </section>
  </section>
</div>

<style>
  .exhibition-header {
    display: flex;
    flex-direction: row;
    justify-content: space-between;
    align-items: center;
    margin-bottom: var(--space-base-medium);
    border-bottom: 1px solid var(--color-base-black);

    & h2, h3 {
      font-weight: var(--font_weight-small);
    }
    & h2 {
      font-size: var(--font_size-large);
    }
    & h3 {
      font-size: var(--font_size-small); 
    }
  }

  .exhibition-media {
    display: flex;
    gap: var(--space-base-large);

    @media (max-width: 675px) {
      display: block;
    }
  }


  .exhibition-card {
    flex: 1;
    display: flex;
    flex-direction: column;
    gap: var(--space-base-small);
    position: sticky;
    top: 60px;
    height: fit-content;

    @media (max-width: 675px) {
      display: grid;
      grid-template-columns: 1fr 1fr;
      margin-bottom: var(--space-base-medium);
      position: relative;
      top: 0;
    }

    & img {
      max-height: 40vh;
      margin: auto;
    }
  }

  .exhibition-images {
    flex: 5;
    display: flex;
    gap: var(--space-base-tiny);
    flex-wrap: wrap;

    & img {
      max-height: 35vh;

      @media (max-width: 675px) {
        max-height: 25vh;
      }
    }
  }

  .quickview-item {
    &:hover {
      cursor: pointer;
    }
  }
</style>
