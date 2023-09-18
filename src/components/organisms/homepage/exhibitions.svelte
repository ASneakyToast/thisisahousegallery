<script>
  export let previous_show = "The Previous Show";
  export let upcoming_show = "The Next Show";

  function previewSelectedCard(e) {
    e.target.classList.add("exhibitions__card--active");
  }
  function previewNoCard(e) {
    e.target.classList.remove("exhibitions__card--active");
  }
</script>

<section class="exhibitions">
  <section class="exhibitions__interface">
    <!--
      <h2>Our exhibitions center around making art as a living or whatever</h2>
    -->

    <section class="exhibitions__critical-pathways">
      <a href="/schedule/{upcoming_show}">
        <p class="exhibitions__pathway pathway-option__next">> Upcoming</p>
      </a>
      <a href="/exhibitions/#{previous_show}">
        <p class="exhibitions__pathway pathway-option__last">> Previous</p>
      </a>
      <a href="/exhibitions/thisisalivingroom">
        <p class="exhibitions__pathway pathway-option__your">> First Show</p>
      </a>
    </section>
  </section>

  <section class="exhibitions__cards">
    <article class="exhibitions__card pathway-card__last" >
      <a href="/exhibitions#yourleastfavwork">
        <img src="exhibitions/yourleastfavwork/showcards/showcard-main--front.jpg" />
      </a>
    </article>
    <article class="exhibitions__card pathway-card__next">
      <a href="/exhibitions#thisisalivingroom">
        <img src="exhibitions/thisisalivingroom/Showcard001.jpg" />
      </a>
    </article>
  </section>
</section>

<style lang="scss">
  @keyframes spin {
    from {
      transform: rotate3d(1, 20, 0, 360deg);
    }
    to {
      transform: rotate3d(0, 0, 0, 0deg);
    }
  }
  @keyframes spinreallyfast {
    from {
      transform: rotate3d(1, 20, 0, 960deg);
    }
    to {
      transform: rotate3d(0, 0, 0, 0deg);
    }
  }
  @keyframes spincrazy {
    from {
      transform: rotate3d(19, -3, 5, 720deg);
    }
    to {
      transform: rotate3d(19, -3, 5, 0deg);
    }
  }

  .exhibitions {
    padding: var(--space-section-gap) var(--space-page-gutter);
    display: flex;
    flex-direction: column;
    gap: var(--space-section-gap);

    @media screen and (min-width: 768px) {
      flex-direction: row;
      min-height: 50vh;
    }

    &__interface {
      flex: 1;

      & h2 {
        margin: 0 0 40px;
      }
    }

    &__critical-pathways {
      flex: 1;
      display: flex;
      flex-direction: column;
      font-size: 24px;

      & a {
        width: fit-content;
      }
    }

    &__pathway {
      display: inline-block;
    }
    &__pathway:hover {
      text-decoration: underline;
    }

    &__cards {
      flex: 3;
      position: relative;

      min-height: 500px;
      margin-top: -50vh;

      @media screen and (max-width: 768px) {
        display: none;
      }
    }

    &__card {
      width: fit-content;
      display: inline-block;
      position: absolute;
      /*
      &:hover {
        transition: all 1s;
        transition-timing-function: linear;
        animation-name: spin;
        animation-duration: .50s;
        animation-iteration-count: infinite;
        animation-iteration-count: 1;
      }
      */

      & img {
        max-width: 300px;
        max-height: 300px;
      }
    }

    &__card--active {
      transform: none !important;
      bottom: 200px !important;
      left: 200px !important;
    }

    /* Previous */
    &__card:nth-child(1) {
      padding: 283px 74px;
    }
    /* Next */
    &__card:nth-child(2) {
      padding: 59px 74px;
      right: 0;
      & img {
        max-height: 600px;
      }
    }
    /* Open Call */
    &__card:nth-child(3) {
      width: 40%;
      margin-top: -54px;
      float: right;
    }
  }
</style>
